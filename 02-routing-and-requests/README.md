# 02 - 路由與請求處理轉換

## 本章學習重點

本章專注於 FastAPI 的**核心功能**，採用簡潔的分層架構：

✅ **已包含的內容：**
- Flask 與 FastAPI 路由系統的完整對比
- 路徑參數、查詢參數、請求體的處理
- Pydantic 自動驗證的強大功能
- Repository 模式（使用記憶體儲存）
- 完整的使用者 CRUD 範例
- 簡單的依賴注入（Repository 注入）

## 目錄
- [專案結構](#專案結構)
- [Layered Architecture 架構說明](#layered-architecture-架構說明)
- [Flask vs FastAPI 路由對比](#flask-vs-fastapi-路由對比)
- [Flask Blueprint vs FastAPI APIRouter](#flask-blueprint-vs-fastapi-apirouter)
- [路徑參數處理](#路徑參數處理)
- [查詢參數處理](#查詢參數處理)
- [請求體處理與 Pydantic](#請求體處理與-pydantic)
- [回應模型與狀態碼](#回應模型與狀態碼)
- [Repository 模式](#repository-模式)
- [完整 CRUD 範例](#完整-crud-範例)
- [啟動與測試](#啟動與測試)

## 專案結構

本章節採用 **Layered Architecture（分層架構）** 設計：

```
02-routing-and-requests/
├── main.py                 # 應用程式入口
├── routers/               # 路由層（處理 HTTP 請求）
│   ├── __init__.py
│   └── users.py           # 使用者路由
├── schemas/               # Pydantic 模型（資料驗證）
│   ├── __init__.py
│   └── user.py            # 使用者資料模型
├── repositories/          # 資料存取層
│   ├── __init__.py
│   └── user_repository.py # 使用者資料存取（目前用記憶體）
├── pyproject.toml         # 專案配置
└── README.md
```

### 為什麼採用分層架構？

| 優勢 | 說明 | 範例 |
|------|------|------|
| **關注點分離** | 路由、驗證、資料存取各司其職 | Router 只負責 HTTP，不管資料如何儲存 |
| **易於測試** | 每層可獨立測試 | 可以單獨測試 Repository 的 CRUD 操作 |
| **易於遷移** | 輕鬆替換底層實作 | 從記憶體改成 SQLAlchemy 只需修改 Repository |
| **符合最佳實踐** | 業界標準的架構模式 | 類似 MVC、Clean Architecture 的概念 |

> 🎯 本章的分層架構非常簡單，只有三層，易於理解和學習。

## Layered Architecture 架構說明

### 架構圖

```
┌─────────────────────────────────────────┐
│       Client (HTTP Request)             │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  Layer 1: Routers (routers/)           │
│  - 定義 API 端點                        │
│  - 處理 HTTP 請求/回應                  │
│  - 呼叫 Repository                      │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  Layer 2: Schemas (schemas/)           │
│  - Pydantic 模型                        │
│  - 自動資料驗證                         │
│  - 定義請求/回應格式                    │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  Layer 3: Repositories (repositories/) │
│  - 資料存取邏輯                         │
│  - 目前：記憶體儲存                     │
│  - 下一步：SQLAlchemy                   │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  Data Storage (Memory / Database)      │
└─────────────────────────────────────────┘
```

### 各層職責

| 層級 | 檔案位置 | 職責 | 範例 |
|------|---------|------|------|
| **Router** | `routers/users.py` | 定義端點、呼叫 Repository | `@router.get("/users")` |
| **Schema** | `schemas/user.py` | 資料驗證、型別定義 | `UserCreate(BaseModel)` |
| **Repository** | `repositories/user_repository.py` | CRUD 操作、資料存取 | `repo.create()` |

## Flask vs FastAPI 路由對比

### 基本路由

#### Flask
```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/users', methods=['GET'])
def get_users():
    return {'users': []}

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    # 手動驗證
    if not isinstance(user_id, int):
        return {'error': 'Invalid ID'}, 400
    return {'user_id': user_id}
```

#### FastAPI
```python
from fastapi import FastAPI

app = FastAPI()

@app.get('/users')
def get_users():
    return {'users': []}

@app.get('/users/{user_id}')
def get_user(user_id: int):
    # 自動驗證！
    return {'user_id': user_id}
```

### 關鍵差異

| 特性 | Flask | FastAPI |
|------|-------|---------|
| **路由裝飾器** | `@app.route()` | `@app.get()`, `@app.post()` 等 |
| **HTTP 方法** | `methods=['GET', 'POST']` | 獨立裝飾器 |
| **參數驗證** | 手動驗證 | 自動驗證（型別提示） |
| **文檔生成** | 需第三方套件 | 自動生成 |

## Flask Blueprint vs FastAPI APIRouter

當專案規模變大時，需要將路由分散到多個檔案中。Flask 使用 **Blueprint**，FastAPI 使用 **APIRouter**。

### Flask Blueprint

```python
# users_bp.py (Flask)
from flask import Blueprint, request

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/', methods=['GET'])
def get_users():
    return {'users': []}

@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    return {'user_id': user_id}

# app.py (Flask)
from flask import Flask
from users_bp import users_bp

app = Flask(__name__)
app.register_blueprint(users_bp)
# 路徑會是：/users/ 和 /users/<user_id>
```

### FastAPI APIRouter

```python
# routers/users.py (FastAPI)
from fastapi import APIRouter

router = APIRouter(
    prefix="/users",
    tags=["users"],  # 👈 自動在文檔中分組
    responses={404: {"description": "Not found"}}
)

@router.get('/')
def get_users():
    return {'users': []}

@router.get('/{user_id}')
def get_user(user_id: int):
    return {'user_id': user_id}

# main.py (FastAPI)
from fastapi import FastAPI
from routers import users

app = FastAPI()
app.include_router(users.router)
# 路徑會是：/users/ 和 /users/{user_id}
```

### 詳細對比

| 特性 | Flask Blueprint | FastAPI APIRouter | 說明 |
|------|----------------|-------------------|------|
| **建立** | `Blueprint('name', __name__)` | `APIRouter()` | FastAPI 不需要 `__name__` |
| **前綴** | `url_prefix='/users'` | `prefix='/users'` | 參數名稱不同 |
| **註冊** | `app.register_blueprint(bp)` | `app.include_router(router)` | 方法名稱不同 |
| **標籤** | ❌ 無 | ✅ `tags=['users']` | FastAPI 自動在文檔中分組 |
| **預設回應** | ❌ 無 | ✅ `responses={...}` | 可統一定義錯誤回應 |
| **依賴注入** | ❌ 無 | ✅ `dependencies=[...]` | 可在 Router 層級共用依賴 |
| **回呼函數** | ✅ `before_request`, `after_request` | ⚠️ 用中間件或依賴注入替代 | FastAPI 更靈活 |

### 多個 Router 範例

```python
# main.py (FastAPI)
from fastapi import FastAPI
from routers import users, items, auth

app = FastAPI()

# 可以為每個 Router 設定不同的前綴
app.include_router(users.router)
app.include_router(items.router)
app.include_router(auth.router, prefix="/api")  # /api/...

# 甚至可以包含多次（不同前綴）
app.include_router(users.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v2")
```

### 巢狀 Router（進階）

```python
# FastAPI 支援巢狀 Router
api_router = APIRouter(prefix="/api")

# 子 Router
api_router.include_router(users.router, prefix="/v1")
api_router.include_router(items.router, prefix="/v1")

# 主應用
app = FastAPI()
app.include_router(api_router)
# 最終路徑：/api/v1/users/, /api/v1/items/
```

### 為什麼 APIRouter 更強大？

| 優勢 | 說明 |
|------|------|
| **自動文檔分組** | `tags` 參數讓 Swagger UI 自動分組 |
| **統一錯誤處理** | `responses` 參數統一定義可能的錯誤 |
| **依賴注入** | Router 層級的 `dependencies` 可套用到所有端點 |
| **更靈活的組織** | 可以巢狀、重用、動態組合 Router |
| **型別安全** | 完整的型別提示支援 |

## 路徑參數處理

### Flask 方式

```python
@app.route('/users/<int:user_id>')
def get_user(user_id):
    # 手動驗證
    if user_id < 1:
        return {'error': 'Invalid user_id'}, 400
    return {'user_id': user_id}
```

### FastAPI 方式

```python
from fastapi import Path

@app.get('/users/{user_id}')
def get_user(user_id: int = Path(..., gt=0, description="使用者 ID")):
    # 自動驗證！user_id 保證是 > 0 的整數
    return {'user_id': user_id}
```

### 對比

| 功能 | Flask | FastAPI |
|------|-------|---------|
| **基本用法** | `<user_id>` | `{user_id}` |
| **型別** | `<int:user_id>` | `user_id: int` |
| **驗證** | 手動 if 檢查 | `Path(gt=0)` 自動驗證 |
| **錯誤訊息** | 自己寫 | 自動生成 |
| **文檔** | 無 | 自動生成 |

## 查詢參數處理

### Flask 方式

```python
from flask import request

@app.route('/users')
def get_users():
    # 手動解析
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    # 手動驗證
    if skip < 0:
        return {'error': 'skip must be >= 0'}, 400
    if limit < 1 or limit > 100:
        return {'error': 'limit must be 1-100'}, 400
    
    return {'skip': skip, 'limit': limit}
```

### FastAPI 方式

```python
from fastapi import Query

@app.get('/users')
def get_users(
    skip: int = Query(0, ge=0, description="跳過筆數"),
    limit: int = Query(10, ge=1, le=100, description="限制筆數")
):
    # 參數自動驗證！
    return {'skip': skip, 'limit': limit}
```

### 對比

| 功能 | Flask | FastAPI |
|------|-------|---------|
| **取值** | `request.args.get()` | 函數參數 |
| **預設值** | 第二個參數 | `= 預設值` |
| **型別轉換** | `type=int` | `: int` |
| **驗證** | 手動 if 檢查 | `Query()` 自動驗證 |
| **程式碼行數** | ~10 行 | ~3 行 |

## 請求體處理與 Pydantic

### Flask 方式

```python
from flask import request

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    # 手動驗證（至少 15 行）
    if not data:
        return {'error': 'No data'}, 400
    if 'username' not in data:
        return {'error': 'username required'}, 400
    if 'email' not in data:
        return {'error': 'email required'}, 400
    if len(data['username']) < 3:
        return {'error': 'username too short'}, 400
    # ... 更多驗證
    
    return {'id': 1, 'username': data['username']}, 201
```

### FastAPI 方式

```python
from fastapi import FastAPI
from pydantic import BaseModel, EmailStr, Field

# 1. 定義 Pydantic 模型
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str | None = None

# 2. 使用模型（所有驗證自動完成）
@app.post('/users', status_code=201)
def create_user(user: UserCreate):
    # user 已經是驗證過的物件！
    return {'id': 1, 'username': user.username}
```

### Pydantic 自動驗證

```python
# schemas/user.py
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr  # 自動驗證 email 格式
    password: str = Field(..., min_length=6)
    full_name: str | None = None
```

**Pydantic 會自動：**
- ✅ 檢查必填欄位
- ✅ 驗證型別
- ✅ 驗證長度 / 範圍
- ✅ 驗證 email 格式
- ✅ 生成錯誤訊息
- ✅ 轉換型別
- ✅ 生成 JSON Schema

### 對比

| 功能 | Flask | FastAPI |
|------|-------|---------|
| **解析 JSON** | `request.get_json()` | `user: UserCreate` |
| **驗證** | 手動（~20 行） | Pydantic（0 行） |
| **錯誤訊息** | 自己定義 | 自動詳細錯誤 |
| **程式碼量** | ~30 行 | ~10 行 |

## 回應模型與狀態碼

### Flask 方式

```python
@app.route('/users/<int:user_id>')
def get_user(user_id):
    if user_id not in users_db:
        return {'error': 'User not found'}, 404
    return users_db[user_id], 200

@app.route('/users', methods=['POST'])
def create_user():
    # ...
    return {'id': 1, 'username': 'john'}, 201
```

### FastAPI 方式

```python
from fastapi import HTTPException, status

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

@app.get('/users/{user_id}', response_model=UserResponse)
def get_user(user_id: int):
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@app.post('/users', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate):
    return repo.create(...)
```

### 對比

| 功能 | Flask | FastAPI |
|------|-------|---------|
| **狀態碼** | 第二個返回值 | `status_code=201` |
| **錯誤處理** | `return ..., 404` | `raise HTTPException` |
| **回應模型** | 無型別保證 | `response_model=UserResponse` |
| **文檔** | 無 | 自動顯示所有可能的回應 |

## Repository 模式

### 為什麼使用 Repository？

| 優勢 | 說明 |
|------|------|
| **關注點分離** | Router 不需要知道資料如何儲存 |
| **易於測試** | 可以輕鬆 mock Repository |
| **易於替換** | 從記憶體改成 SQLAlchemy 只需修改 Repository |
| **重用性** | 多個 Router 可共用同一個 Repository |

### 架構圖

```
Router (users.py)
    ↓ 依賴注入
UserRepository (user_repository.py)
    ↓
Data Storage (Memory / Database)
```

### 目前實作（記憶體）

```python
# repositories/user_repository.py
class UserRepository:
    def __init__(self):
        self._users: dict[int, User] = {}
    
    def create(self, username: str, email: str, password: str, full_name: str | None = None) -> User:
        """建立使用者"""
        user = User(id=self._next_id, username=username, ...)
        self._users[self._next_id] = user
        return user
    
    def get_by_id(self, user_id: int) -> User | None:
        """根據 ID 獲取使用者"""
        return self._users.get(user_id)
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """獲取所有使用者"""
        users = list(self._users.values())
        return users[skip:skip + limit]
    
    def update(self, user_id: int, **kwargs) -> User | None:
        """更新使用者"""
        # ...
    
    def delete(self, user_id: int) -> bool:
        """刪除使用者"""
        # ...
```

### 下一步（SQLAlchemy）

```python
# 下一章會改成這樣：
class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, username: str, ...) -> User:
        user = User(username=username, ...)
        self.db.add(user)
        self.db.commit()
        return user
    
    def get_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()
```

### 依賴注入（簡單版）

FastAPI 使用依賴注入來提供 Repository 實例：

```python
# repositories/user_repository.py
def get_user_repository() -> UserRepository:
    """
    依賴注入函數
    FastAPI 會自動調用此函數並將結果注入到路由函數中
    """
    return user_repository

# routers/users.py
@router.get("/users")
def get_users(
    skip: int = 0,
    limit: int = 10,
    repo: UserRepository = Depends(get_user_repository)  # 👈 依賴注入
):
    # repo 已經是 UserRepository 的實例
    users = repo.get_all(skip=skip, limit=limit)
    return [user.to_dict() for user in users]
```

**為什麼使用依賴注入？**

| 優勢 | 說明 |
|------|------|
| **易於測試** | 測試時可以輕鬆替換為 mock Repository |
| **解耦合** | Router 不需要知道如何建立 Repository |
| **易於替換** | 下一步改用資料庫時，只需修改 `get_user_repository()` |

> 💡 **進階依賴注入**（認證、權限、分頁等）會在後續章節介紹。本章只示範最基本的 Repository 注入。

## 完整 CRUD 範例

### 1. 定義 Schema

```python
# schemas/user.py
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str | None = None

class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    full_name: str | None = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str | None
    created_at: datetime
```

### 2. 定義 Repository

```python
# repositories/user_repository.py
class UserRepository:
    def create(self, ...) -> User: ...
    def get_by_id(self, user_id: int) -> User | None: ...
    def get_all(self, skip: int, limit: int) -> List[User]: ...
    def update(self, user_id: int, **kwargs) -> User | None: ...
    def delete(self, user_id: int) -> bool: ...
```

### 3. 定義 Router

```python
# routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/users", tags=["users"])

# CREATE
@router.post("/", response_model=UserResponse, status_code=201)
def create_user(
    user_data: UserCreate,
    repo: UserRepository = Depends(get_user_repository)
):
    # 檢查使用者名稱是否存在
    if repo.get_by_username(user_data.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user = repo.create(...)
    return user.to_dict()

# READ (List)
@router.get("/", response_model=List[UserResponse])
def get_users(
    skip: int = 0,
    limit: int = 10,
    repo: UserRepository = Depends(get_user_repository)
):
    users = repo.get_all(skip=skip, limit=limit)
    return [user.to_dict() for user in users]

# READ (Single)
@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    repo: UserRepository = Depends(get_user_repository)
):
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.to_dict()

# UPDATE
@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    repo: UserRepository = Depends(get_user_repository)
):
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    updated_user = repo.update(user_id, ...)
    return updated_user.to_dict()

# DELETE
@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    repo: UserRepository = Depends(get_user_repository)
):
    success = repo.delete(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
```

### 4. 註冊 Router

```python
# main.py
from fastapi import FastAPI
from routers import users

app = FastAPI()
app.include_router(users.router)
```

## 啟動與測試

### 1. 安裝依賴

```bash
# 進入專案目錄
cd 02-routing-and-requests

# 安裝依賴（使用 uv）
uv sync

# 或使用 pip
pip install fastapi uvicorn[standard] pydantic[email]
```

### 2. 啟動應用

```bash
# 使用 uv（推薦）
uv run uvicorn main:app --reload

# 或直接使用 uvicorn
uvicorn main:app --reload
```

啟動成功後，你會看到：
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 3. 訪問 API 文檔

FastAPI 會自動生成兩種互動式文檔：

| 文檔類型 | URL | 特色 |
|---------|-----|------|
| **Swagger UI** | http://localhost:8000/docs | 可直接測試 API |
| **ReDoc** | http://localhost:8000/redoc | 更美觀的閱讀介面 |
| **根路徑** | http://localhost:8000/ | 查看 API 資訊 |

### 4. 測試 API

#### 方式 1：使用 Swagger UI（最簡單）

1. 開啟 http://localhost:8000/docs
2. 點擊任一端點（如 `POST /users`）
3. 點擊「Try it out」
4. 填寫請求資料
5. 點擊「Execute」
6. 查看回應結果

#### 方式 2：使用 curl

**建立使用者 (CREATE)**
```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "secret123",
    "full_name": "John Doe"
  }'
```

**回應範例：**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "created_at": "2024-01-01T00:00:00"
}
```

**獲取所有使用者 (READ List)**
```bash
curl http://localhost:8000/users
```

**獲取單一使用者 (READ Single)**
```bash
curl http://localhost:8000/users/1
```

**更新使用者 (UPDATE)**
```bash
curl -X PUT http://localhost:8000/users/1 \
  -H "Content-Type: application/json" \
  -d '{"full_name": "John Updated"}'
```

**刪除使用者 (DELETE)**
```bash
curl -X DELETE http://localhost:8000/users/1
```

#### 方式 3：使用 HTTPie（更友善的工具）

```bash
# 安裝 httpie
pip install httpie

# 建立使用者
http POST localhost:8000/users username=johndoe email=john@example.com password=secret123

# 獲取使用者列表
http GET localhost:8000/users

# 更新使用者
http PUT localhost:8000/users/1 full_name="John Updated"

# 刪除使用者
http DELETE localhost:8000/users/1
```

## 總結

### 本章學到了什麼？

#### ✅ 核心概念

| 概念 | Flask 做法 | FastAPI 做法 | 優勢 |
|------|-----------|-------------|------|
| **路由定義** | `@app.route('/', methods=['GET'])` | `@app.get('/')` | 更清晰、更語意化 |
| **路徑參數** | `<int:id>` + 手動驗證 | `{id}: int` | 自動驗證、型別安全 |
| **查詢參數** | `request.args.get()` + 驗證 | 函數參數 + `Query()` | 自動驗證、自動文檔 |
| **請求體** | `request.get_json()` + 驗證 | Pydantic 模型 | 零驗證程式碼 |
| **回應** | 手動 return | `response_model` | 型別安全、自動文檔 |
| **路由組織** | `Blueprint` | `APIRouter` | 更靈活、自動分組 |
| **資料存取** | 直接操作 | Repository 模式 | 易於測試、易於替換 |

#### 🎯 關鍵優勢

**相比 Flask，FastAPI 讓你：**

- ⚡ **快 4-10 倍**（異步 + 更高效的處理）
- 📝 **少寫 60% 的驗證程式碼**（Pydantic 自動驗證）
- 📚 **零成本的 API 文檔**（Swagger UI + ReDoc）
- 🛡️ **型別安全**（編譯期就能發現錯誤）
- 🏗️ **更好的架構**（分層設計、依賴注入）

#### 📊 程式碼量對比

以建立使用者 API 為例：

| 功能 | Flask | FastAPI | 節省 |
|------|-------|---------|------|
| 路由定義 | 2 行 | 2 行 | - |
| 參數驗證 | 15-20 行 | 0 行 | ✅ 節省 100% |
| 錯誤處理 | 5-10 行 | 0 行 | ✅ 節省 100% |
| API 文檔 | 需安裝額外套件 + 配置 | 自動生成 | ✅ 節省 100% |
| **總計** | ~30 行 | ~10 行 | ✅ **節省 66%** |



## 參考資源

- [FastAPI - Path Parameters](https://fastapi.tiangolo.com/tutorial/path-params/)
- [FastAPI - Query Parameters](https://fastapi.tiangolo.com/tutorial/query-params/)
- [FastAPI - Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
