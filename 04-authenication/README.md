# 04 - 認證系統 (Authentication)

## 本章學習重點

本章重點學習 FastAPI 的**JWT 認證系統**，展示如何實現完整的用戶註冊、登入和認證流程，並展示良好的架構設計原則。

✅ **已包含的內容：**
- JWT Token 創建與驗證
- 密碼加密（bcrypt）
- 認證中間件設計
- 依賴注入模式
- Swagger 文檔整合
- 職責分離架構（Utils → Middleware → Router）

## 目錄

- [專案結構](#專案結構)
- [認證系統架構](#認證系統架構)
- [JWT 工具層 (Utils)](#jwt-工具層-utils)
- [JWT 中間件層 (Middleware)](#jwt-中間件層-middleware)
- [認證路由層 (Router)](#認證路由層-router)
- [認證流程](#認證流程)
- [使用方式](#使用方式)
- [測試認證系統](#測試認證系統)
- [架構設計原則](#架構設計原則)

## 專案結構

```
04-authentication/
├── main.py                    # 應用程式入口
├── core/                     # 核心模組
│   ├── __init__.py
│   ├── exceptions.py            # 自訂例外（包含認證相關例外）
│   └── error_handlers.py        # 錯誤處理器
├── middleware/               # 中間件層
│   ├── __init__.py
│   ├── logging_middleware.py    # 日誌中間件
│   ├── timing_middleware.py     # 計時中間件
│   ├── request_id_middleware.py # 請求追蹤
│   └── jwt_middleware.py        # JWT 認證中間件 ⭐
├── utils/                    # 共用工具
│   ├── __init__.py
│   ├── logger.py                # 日誌配置
│   ├── metrics.py               # 效能指標收集
│   └── jwt.py                   # JWT 工具函數 ⭐
├── routers/                  # 路由層
│   ├── __init__.py
│   ├── users.py                 # 使用者路由
│   └── auth.py                  # 認證路由 ⭐
├── schemas/                  # Pydantic 模型
│   ├── __init__.py
│   ├── user.py                  # 使用者模型
│   └── auth.py                  # 認證模型 ⭐
├── repositories/             # 資料存取層
│   ├── __init__.py
│   ├── user_repository.py       # 使用者資料存取
│   └── auth_repository.py       # 認證資料存取 ⭐
└── README.md
```

## 認證系統架構

本專案採用**三層架構設計**，實現職責分離：

```
┌─────────────────────────────────────────┐
│         Router 層 (routers/auth.py)      │
│  - 處理 HTTP 請求/回應                   │
│  - 業務邏輯（註冊、登入、獲取當前用戶）   │
│  - 依賴注入（get_current_user）         │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│    Middleware 層 (middleware/jwt_*)     │
│  - 驗證 JWT token                       │
│  - 提取 user_id                        │
│  - 存儲到 ContextVar（線程安全）        │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│      Utils 層 (utils/jwt.py)            │
│  - 創建 JWT token（純函數）             │
│  - 驗證 JWT token（純函數）             │
│  - 無副作用，可重用                     │
└─────────────────────────────────────────┘
```

### 為什麼這樣設計？

| 層級 | 職責 | 理由 |
|------|------|------|
| **Utils** | 純函數，無副作用 | 可重用、易測試、不依賴外部狀態 |
| **Middleware** | 驗證和提供 user_id | 可重用、不強制認證、讓路由層決定 |
| **Router** | 業務邏輯和依賴注入 | 處理業務需求、獲取完整用戶物件 |

## JWT 工具層 (Utils)

**檔案：`utils/jwt.py`**

這層負責 JWT token 的創建和驗證，是純函數，無副作用。

### 核心函數

```python
# utils/jwt.py
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from core.exceptions import InvalidTokenException, TokenExpiredException

# JWT 設定
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(
    data: Dict,
    expires_delta: Optional[timedelta] = None,
    secret_key: Optional[str] = None
) -> str:
    """創建 JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    key = secret_key or SECRET_KEY
    encoded_jwt = jwt.encode(to_encode, key, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(
    token: str,
    secret_key: Optional[str] = None
) -> Dict:
    """驗證 JWT token"""
    try:
        key = secret_key or SECRET_KEY
        payload = jwt.decode(token, key, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        if "expired" in str(e).lower() or "exp" in str(e).lower():
            raise TokenExpiredException()
        raise InvalidTokenException(f"Could not validate credentials: {str(e)}")

def create_token_for_user(user_id: int, email: str) -> str:
    """為使用者創建 JWT token（便捷函數）"""
    token_data = {"sub": str(user_id), "email": email}
    return create_access_token(data=token_data)
```

### 特點

- ✅ **純函數**：無副作用，不依賴外部狀態
- ✅ **可重用**：可在任何地方使用
- ✅ **易測試**：輸入輸出明確
- ✅ **可配置**：支援自訂過期時間和密鑰

## JWT 中間件層 (Middleware)

**檔案：`middleware/jwt_middleware.py`**

這層負責驗證 JWT token 並提供 `user_id`，使用 `ContextVar` 存儲（線程安全）。

### 核心實現

```python
# middleware/jwt_middleware.py
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from contextvars import ContextVar
from utils.jwt import verify_token
from core.exceptions import InvalidTokenException

# 使用 ContextVar 儲存當前使用者 ID（線程安全）
current_user_id_var: ContextVar[Optional[int]] = ContextVar('current_user_id', default=None)

def get_current_user_id() -> Optional[int]:
    """獲取當前請求的使用者 ID"""
    return current_user_id_var.get()

class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    JWT 認證中間件
    驗證請求中的 JWT token，並將 user_id 存儲到 ContextVar 中
    
    這個中間件是可選的，不會強制要求所有請求都必須有 token
    如果沒有 token 或 token 無效，user_id 會是 None
    """
    
    async def dispatch(self, request: Request, call_next):
        user_id = None
        
        # 嘗試從 Authorization header 獲取 token
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            
            try:
                # 驗證 token（使用 utils 層的函數）
                payload = verify_token(token)
                
                # 從 token 中提取 user_id
                user_id_str = payload.get("sub")
                if user_id_str:
                    user_id = int(user_id_str)
            except (InvalidTokenException, ValueError, TypeError):
                # Token 無效或格式錯誤，但不阻止請求繼續
                # 讓路由層決定是否需要認證
                pass
        
        # 將 user_id 存儲到 ContextVar
        current_user_id_var.set(user_id)
        
        # 處理請求
        response = await call_next(request)
        
        return response
```

### 特點

- ✅ **可選認證**：不強制要求所有請求都有 token
- ✅ **線程安全**：使用 `ContextVar` 存儲 `user_id`
- ✅ **可重用**：所有請求都會經過這個中間件
- ✅ **職責單一**：只負責驗證和提供 `user_id`，不處理業務邏輯

### 註冊中間件

```python
# main.py
from middleware import JWTAuthMiddleware

app.add_middleware(JWTAuthMiddleware)  # JWT 認證（驗證 token 並提供 user_id）
```

## 認證路由層 (Router)

**檔案：`routers/auth.py`**

這層負責處理認證相關的 HTTP 請求，包含註冊、登入和獲取當前用戶。

### 核心實現

```python
# routers/auth.py
from fastapi import APIRouter, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from repositories.auth_repository import AuthRepository, AuthUser, get_auth_repository
from middleware.jwt_middleware import get_current_user_id
from utils.jwt import create_token_for_user

# HTTP Bearer Token 安全方案（用於 Swagger 文檔顯示）
security = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    repo: AuthRepository = Depends(get_auth_repository)
) -> AuthUser:
    """
    從 middleware 提供的 user_id 獲取當前使用者
    
    這個函數作為 FastAPI 的依賴注入使用
    """
    # 從 middleware 獲取 user_id（實際驗證在 middleware 中完成）
    user_id = get_current_user_id()
    
    if user_id is None:
        raise InvalidTokenException("Authentication required")
    
    # 從資料庫獲取使用者
    user = repo.get_by_id(user_id)
    if user is None:
        raise UserNotFoundException(user_id)
    
    return user

@router.post("/register", response_model=AuthResponse)
def register(
    auth_data: AuthCreate,
    repo: AuthRepository = Depends(get_auth_repository)
):
    """註冊新使用者"""
    # 檢查 email 是否已存在
    if repo.get_by_email(auth_data.email):
        raise UserAlreadyExistsException(auth_data.email)
    
    # 建立新使用者（密碼會自動加密）
    user = repo.create(auth_data.email, auth_data.password)
    
    # 創建 JWT token（使用 utils 層的函數）
    access_token = create_token_for_user(user.id, user.email)
    
    return AuthResponse(
        access_token=access_token,
        token_type="Bearer"
    )

@router.post("/login", response_model=AuthResponse)
def login(
    auth_data: AuthLogin,
    repo: AuthRepository = Depends(get_auth_repository)
):
    """使用者登入"""
    # 驗證密碼
    if not repo.verify_password(auth_data.email, auth_data.password):
        raise InvalidCredentialsException(auth_data.email)
    
    # 獲取使用者
    user = repo.get_by_email(auth_data.email)
    
    # 創建 JWT token
    access_token = create_token_for_user(user.id, user.email)
    
    return AuthResponse(
        access_token=access_token,
        token_type="Bearer"
    )

@router.get("/me", response_model=AuthMe)
def me(user: AuthUser = Depends(get_current_user)):
    """
    獲取當前使用者資訊
    
    需要 Bearer token 認證
    """
    return AuthMe(
        id=user.id,
        email=user.email,
        created_at=user.created_at
    )
```

### 特點

- ✅ **業務邏輯**：處理註冊、登入等業務需求
- ✅ **依賴注入**：使用 `Depends(get_current_user)` 保護需要認證的路由
- ✅ **Swagger 整合**：使用 `HTTPBearer` 讓 Swagger 顯示認證選項
- ✅ **錯誤處理**：統一的錯誤回應格式

## 認證流程

### 1. 註冊流程

```
用戶註冊
  ↓
POST /auth/register
  ↓
驗證 email 是否已存在
  ↓
使用 bcrypt 加密密碼
  ↓
創建用戶（AuthRepository）
  ↓
創建 JWT token（utils/jwt.py）
  ↓
返回 token
```

### 2. 登入流程

```
用戶登入
  ↓
POST /auth/login
  ↓
驗證 email 和密碼（bcrypt）
  ↓
獲取用戶資訊
  ↓
創建 JWT token（utils/jwt.py）
  ↓
返回 token
```

### 3. 認證流程（保護的路由）

```
請求保護的路由
  ↓
JWTAuthMiddleware 驗證 token
  ↓
提取 user_id 存儲到 ContextVar
  ↓
路由處理器調用 get_current_user
  ↓
從 ContextVar 獲取 user_id
  ↓
從資料庫獲取完整用戶物件
  ↓
返回用戶資訊
```

## 使用方式

### 1. 註冊新用戶

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "secret123"
  }'
```

**回應：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer"
}
```

### 2. 登入

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "secret123"
  }'
```

**回應：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer"
}
```

### 3. 獲取當前用戶（需要認證）

```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**回應：**
```json
{
  "id": 1,
  "email": "john@example.com",
  "created_at": "2024-01-01T00:00:00"
}
```

### 4. 在其他路由中使用認證

```python
# routers/users.py
from routers.auth import get_current_user
from repositories.auth_repository import AuthUser

@router.get("/profile")
def get_profile(user: AuthUser = Depends(get_current_user)):
    """獲取用戶個人資料（需要認證）"""
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at
    }
```

## 測試認證系統

### 1. 使用 Swagger UI 測試

1. 啟動應用：`uv run uvicorn main:app --reload`
2. 打開瀏覽器：`http://localhost:8000/docs`
3. 註冊用戶：
   - 點擊 `POST /auth/register`
   - 點擊 "Try it out"
   - 輸入 email 和 password
   - 點擊 "Execute"
   - 複製返回的 `access_token`
4. 認證：
   - 點擊右上角的 "Authorize" 按鈕
   - 在 "Value" 欄位輸入：`Bearer <你的token>`
   - 點擊 "Authorize"
5. 測試保護的路由：
   - 點擊 `GET /auth/me`
   - 點擊 "Try it out"
   - 點擊 "Execute"
   - 應該能成功獲取用戶資訊

### 2. 使用 curl 測試

```bash
# 1. 註冊
TOKEN=$(curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"secret123"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"

# 2. 獲取當前用戶
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### 3. 測試錯誤情況

```bash
# 未提供 token
curl -X GET http://localhost:8000/auth/me
# 回應：{"error": {"status_code": 401, "message": "Authentication required"}}

# 無效的 token
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer invalid_token"
# 回應：{"error": {"status_code": 401, "message": "Invalid token"}}

# 錯誤的密碼
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"wrong"}'
# 回應：{"error": {"status_code": 401, "message": "Invalid credentials"}}
```

## 架構設計原則

### 1. 職責分離 (Separation of Concerns)

- **Utils 層**：純函數，無副作用
- **Middleware 層**：驗證和提供 `user_id`
- **Router 層**：業務邏輯和依賴注入

### 2. 可重用性 (Reusability)

- JWT 工具函數可在任何地方使用
- Middleware 可應用於所有請求
- `get_current_user` 可在任何路由中使用

### 3. 靈活性 (Flexibility)

- Middleware 不強制要求認證，讓路由層決定
- 可以輕鬆擴展（例如添加角色檢查）
- 支援自訂過期時間和密鑰

### 4. 可測試性 (Testability)

- Utils 層的純函數易於測試
- Middleware 可以獨立測試
- Router 層可以使用 mock 依賴

## 資料模型

### AuthUser

```python
class AuthUser:
    id: int
    email: str
    password: str  # 已加密（bcrypt）
    created_at: datetime
```

### Auth Schemas

```python
# 註冊請求
class AuthCreate(BaseModel):
    email: EmailStr
    password: str  # min_length=6

# 登入請求
class AuthLogin(BaseModel):
    email: EmailStr
    password: str

# 認證回應
class AuthResponse(BaseModel):
    access_token: str
    token_type: str  # 預設 "Bearer"

# 當前用戶資訊
class AuthMe(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
```

## 安全考量

### 1. 密碼加密

使用 `bcrypt` 加密密碼，確保即使資料庫洩漏，密碼也無法被還原。

```python
# 加密
hashed_password = bcrypt.hashpw(
    password.encode('utf-8'),
    bcrypt.gensalt()
).decode('utf-8')

# 驗證
bcrypt.checkpw(
    password.encode('utf-8'),
    hashed_password.encode('utf-8')
)
```

### 2. JWT Token 安全

- ✅ 使用環境變數設定 `JWT_SECRET_KEY`（生產環境必須）
- ✅ Token 預設 30 分鐘過期
- ✅ 使用 HS256 演算法
- ✅ Token 中包含 `exp` 過期時間

### 3. 錯誤處理

- ✅ 不洩漏敏感資訊（例如：不告訴用戶 email 是否存在）
- ✅ 統一的錯誤格式
- ✅ 適當的 HTTP 狀態碼

## 生產環境建議

### 1. 環境變數

```bash
# .env
JWT_SECRET_KEY=your-very-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 2. 密碼強度

在 `AuthCreate` schema 中添加更嚴格的驗證：

```python
from pydantic import validator

class AuthCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
```

### 3. Refresh Token

考慮實現 refresh token 機制，讓用戶無需頻繁登入。

### 4. Rate Limiting

添加速率限制，防止暴力破解攻擊。

### 5. 日誌記錄

記錄所有認證相關的操作（登入成功/失敗、token 驗證失敗等）。

## 總結

### 架構優勢

✅ **職責分離**：每層都有明確的職責  
✅ **可重用性**：工具函數和中間件可在多處使用  
✅ **可測試性**：純函數和依賴注入易於測試  
✅ **靈活性**：可以輕鬆擴展和修改  
✅ **安全性**：密碼加密、JWT token、錯誤處理  

### 關鍵學習點

1. **三層架構**：Utils → Middleware → Router
2. **依賴注入**：使用 FastAPI 的 `Depends` 實現
3. **ContextVar**：線程安全的上下文變數
4. **Swagger 整合**：使用 `HTTPBearer` 顯示認證選項
5. **錯誤處理**：統一的錯誤格式和適當的狀態碼

## 參考資源

- [FastAPI - Security](https://fastapi.tiangolo.com/tutorial/security/)
- [FastAPI - Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [JWT.io](https://jwt.io/) - JWT 介紹和工具
- [bcrypt](https://github.com/pyca/bcrypt/) - 密碼加密庫
- [python-jose](https://python-jose.readthedocs.io/) - JWT 處理庫
