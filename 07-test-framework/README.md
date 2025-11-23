# 07 - 測試框架

## 本章學習重點

本章重點學習 **測試框架與實戰**，從 Flask 的測試方式遷移到 FastAPI，掌握異步測試、依賴覆寫、Mock Service 依賴等測試技巧。

✅ **已包含的內容：**
- ✅ Flask test_client → FastAPI TestClient 對比
- ✅ 異步測試設定（pytest-asyncio）
- ✅ 依賴覆寫在測試中的應用（Repository、Service）
- ✅ Mock Service 依賴（Service 層相互依賴）
- ✅ 測試覆蓋率自動計算（100% 覆蓋率）⭐
- ✅ 完整架構示例：Router → Service → Repository → Memory

## 專案結構

```
07-test-framework/
├── main.py                    # 應用程式入口
├── pyproject.toml             # 專案配置
├── pytest.ini                 # Pytest 配置（自動計算覆蓋率）⭐
├── .coveragerc                # 測試覆蓋率配置
├── .gitignore                 # Git 忽略文件
├── core/                      # 核心模組
│   ├── __init__.py
│   └── dependencies.py        # 依賴注入（認證等）
├── routers/                   # 路由層
│   ├── __init__.py
│   └── users.py               # 用戶路由（只有一個端點）⭐
├── services/                  # 服務層（可相互依賴）⭐
│   ├── __init__.py
│   └── user_service.py        # 用戶服務（依賴 NotificationService）
├── repositories/              # 資料存取層 ⭐
│   ├── __init__.py
│   └── user_repository.py     # Memory 存儲
├── schemas/                   # Pydantic 模型
│   ├── __init__.py
│   └── user.py                # UserResponse
└── tests/                     # 測試文件（獨立目錄）⭐
    ├── __init__.py
    ├── conftest.py            # Pytest 配置和 Fixtures
    ├── test_users.py          # 用戶端點和 Repository 測試
    ├── test_main.py           # 主模組測試
    └── test_core.py           # 核心依賴測試
```

## 架構設計

### 完整架構層級

```
HTTP Request
    ↓
Router (routers/users.py)
    ↓
Service (services/user_service.py) ← 可依賴其他 Service ⭐
    ↓
Repository (repositories/user_repository.py)
    ↓
Memory Storage (dict)
```

### 關鍵設計特點

1. **簡化示例**：只有一個 API 端點 `GET /users/{user_id}`
2. **完整層級**：Router → Service → Repository → Memory
3. **Service 相互依賴**：UserService 可以依賴 NotificationService，便於在測試中 Mock
4. **依賴注入**：所有層級都使用 FastAPI 的依賴注入系統
5. **測試友好**：每個依賴都可以在測試中被覆寫或 Mock

## 目錄

- [快速開始](#快速開始)
- [專案結構詳解](#專案結構詳解)
- [Flask test_client → FastAPI TestClient](#flask-test_client--fastapi-testclient)
- [異步測試設定](#異步測試設定)
- [依賴覆寫在測試中的應用](#依賴覆寫在測試中的應用)
- [Mock Service 依賴](#mock-service-依賴) ⭐
- [測試覆蓋率](#測試覆蓋率) ⭐
- [使用方式](#使用方式)
- [常見問題](#常見問題)

## 快速開始

### 1. 安裝依賴

```bash
cd 07-test-framework
uv sync --dev
```

### 2. 運行測試（自動計算覆蓋率）

```bash
# 運行所有測試（自動顯示覆蓋率）
uv run pytest

# 輸出示例：
# ==================== 36 passed in 0.10s ====================
# 
# ---------- coverage: platform darwin, python 3.11.13-final-0 -----------
# Name                              Stmts   Miss    Cover   Missing
# ------------------------------------------------------------------
# repositories/user_repository.py      26      0  100.00%
# routers/users.py                     10      0  100.00%
# services/user_service.py             19      0  100.00%
# ... (所有文件 100% 覆蓋率) ⭐
# ------------------------------------------------------------------
# TOTAL                               101      0  100.00%
```

### 3. 啟動應用

```bash
uv run uvicorn main:app --reload

# 訪問 API 文檔
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

## 專案結構詳解

### API 端點

**只有一個端點**：`GET /users/{user_id}`

```python
# routers/users.py
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """根據 ID 獲取用戶"""
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return user.to_dict()
```

### 完整架構示例

#### 1. Router 層

```python
# routers/users.py
from services.user_service import UserService, get_user_service

@router.get("/{user_id}")
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)  # 依賴注入
):
    user = await service.get_user(user_id)
    # ...
```

#### 2. Service 層（可相互依賴）⭐

```python
# services/user_service.py
class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        notification_service: Optional[NotificationService] = None  # 可選依賴
    ):
        self.user_repo = user_repo
        self.notification_service = notification_service
    
    async def get_user(self, user_id: int):
        user = self.user_repo.get_by_id(user_id)
        
        # 如果配置了通知服務，發送通知
        if user and self.notification_service:
            await self.notification_service.send_notification(...)
        
        return user
```

#### 3. Repository 層（Memory 存儲）

```python
# repositories/user_repository.py
class UserRepository:
    def __init__(self):
        self._users: dict[int, User] = {
            1: User(id=1, username="alice", email="alice@example.com"),
            # ...
        }
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        return self._users.get(user_id)
```

## Flask test_client → FastAPI TestClient

### 基本對比

#### Flask 測試方式

```python
# Flask
from flask import Flask
app = Flask(__name__)

def test_root():
    client = app.test_client()
    response = client.get('/users/1')
    assert response.status_code == 200
    assert response.json == {"id": 1, "username": "alice"}  # json 是屬性
```

#### FastAPI 測試方式

```python
# FastAPI
from fastapi.testclient import TestClient
from main import app

def test_get_user():
    client = TestClient(app)
    response = client.get('/users/1')
    assert response.status_code == 200
    assert response.json() == {"id": 1, "username": "alice"}  # json() 是方法
```

### 主要差異對照表

| 特性 | Flask | FastAPI |
|------|-------|---------|
| **客戶端創建** | `app.test_client()` | `TestClient(app)` |
| **JSON 回應** | `response.json` (屬性) | `response.json()` (方法) |
| **狀態碼** | `response.status_code` | `response.status_code` (相同) |
| **錯誤訊息** | `response.json['error']` | `response.json()['detail']` |

### 實際範例

```python
# tests/test_users.py
def test_get_user_success(client, override_user_repository, mock_user_repository):
    """測試成功獲取用戶"""
    mock_user = User(id=1, username="alice", email="alice@example.com")
    mock_user_repository.get_by_id.return_value = mock_user
    
    response = client.get("/users/1")
    
    assert response.status_code == 200
    assert response.json()["username"] == "alice"
```

## 異步測試設定

### 為什麼需要異步測試？

FastAPI 支援異步端點（`async def`），這些端點需要使用異步測試客戶端。

### 配置

```ini
# pytest.ini
[pytest]
asyncio_mode = auto  # 自動檢測異步測試
```

### 使用 AsyncClient

```python
# tests/test_users.py
@pytest.mark.asyncio
async def test_get_user_async(async_client, override_user_repository, mock_user_repository):
    """異步測試獲取用戶"""
    mock_user = User(id=2, username="bob", email="bob@example.com")
    mock_user_repository.get_by_id.return_value = mock_user
    
    response = await async_client.get("/users/2")
    
    assert response.status_code == 200
    assert response.json()["username"] == "bob"
```

### conftest.py 配置

```python
# tests/conftest.py
from httpx import AsyncClient, ASGITransport

@pytest.fixture
async def async_client():
    """異步測試客戶端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

## 依賴覆寫在測試中的應用

### 為什麼需要依賴覆寫？

在測試中，我們不希望：
- 真正執行認證邏輯（無需 JWT token）
- 連接真實的資料庫
- 調用外部服務

FastAPI 的依賴注入系統允許我們在測試中覆寫這些依賴。

### 覆寫 Repository 依賴

```python
# tests/test_users.py
def test_get_user_success(client, override_user_repository, mock_user_repository):
    """測試覆寫 Repository 依賴"""
    # Mock Repository 返回值
    mock_user = User(id=1, username="alice", email="alice@example.com")
    mock_user_repository.get_by_id.return_value = mock_user
    
    response = client.get("/users/1")
    
    assert response.status_code == 200
    # 驗證 Mock 被調用
    mock_user_repository.get_by_id.assert_called_once_with(1)
```

### 覆寫 Service 依賴

```python
def test_override_service(client, override_user_service, mock_user_service):
    """測試覆寫 Service 依賴"""
    from repositories.user_repository import User as RepoUser
    
    mock_user = RepoUser(id=200, username="service_user", email="service@example.com")
    mock_user_service.get_user = AsyncMock(return_value=mock_user)
    
    response = client.get("/users/200")
    
    assert response.status_code == 200
    mock_user_service.get_user.assert_called_once_with(200)
```

### conftest.py 中的 Fixtures

```python
# tests/conftest.py

@pytest.fixture
def override_user_repository(mock_user_repository):
    """覆寫 UserRepository 依賴"""
    from repositories.user_repository import get_user_repository
    
    app.dependency_overrides[get_user_repository] = lambda: mock_user_repository
    yield
    app.dependency_overrides.clear()  # 測試後自動清除
```

## Mock Service 依賴 ⭐

### Service 相互依賴設計

UserService 可以依賴其他 Service（如 NotificationService），這樣可以在測試中獨立 Mock 每個依賴：

```python
# services/user_service.py
class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        notification_service: Optional[NotificationService] = None  # 可選依賴
    ):
        self.user_repo = user_repo
        self.notification_service = notification_service
```

### 測試中 Mock Service 依賴

```python
# tests/test_users.py
@pytest.mark.asyncio
async def test_user_service_with_notification(
    user_repository_with_data,
    mock_notification_service
):
    """測試 UserService 調用 NotificationService"""
    service = UserService(
        user_repo=user_repository_with_data,
        notification_service=mock_notification_service  # Mock 依賴
    )
    
    user = await service.get_user(1)
    
    assert user is not None
    
    # 驗證 NotificationService 被調用
    mock_notification_service.send_notification.assert_called_once()
    call_args = mock_notification_service.send_notification.call_args[0][0]
    assert "User 1" in call_args
    assert "alice" in call_args
```

### 測試沒有依賴的情況

```python
@pytest.mark.asyncio
async def test_user_service_without_notification(user_repository_with_data):
    """測試 UserService 沒有 NotificationService 的情況"""
    service = UserService(user_repo=user_repository_with_data)  # 不注入通知服務
    
    user = await service.get_user(1)
    
    assert user is not None
    # 沒有通知服務時，不會調用通知
```

## 測試覆蓋率 ⭐

### 自動計算覆蓋率

項目已配置**自動計算覆蓋率**，運行 `pytest` 時會自動顯示覆蓋率報告。

### 配置

```ini
# pytest.ini
[pytest]
addopts = 
    --cov=.                    # 自動計算覆蓋率
    --cov-report=term-missing  # 終端顯示未覆蓋的行
    --cov-report=html          # 生成 HTML 報告
    --cov-report=xml           # 生成 XML 報告（CI/CD 用）
```

### 運行測試查看覆蓋率

```bash
# 運行所有測試（自動顯示覆蓋率）
uv run pytest

# 輸出示例：
# ---------- coverage: platform darwin, python 3.11.13-final-0 -----------
# Name                              Stmts   Miss    Cover   Missing
# ------------------------------------------------------------------
# repositories/user_repository.py      26      0  100.00%
# routers/users.py                     10      0  100.00%
# services/user_service.py             19      0  100.00%
# core/dependencies.py                 19      0  100.00%
# main.py                              13      0  100.00%
# ------------------------------------------------------------------
# TOTAL                               101      0  100.00% ⭐
```

### 查看 HTML 報告

```bash
# 生成 HTML 報告後
open htmlcov/index.html

# 可以視覺化查看：
# - 🟢 綠色行 = 被測試覆蓋
# - 🔴 紅色行 = 未被測試覆蓋
```

### 當前覆蓋率狀態

✅ **所有文件 100% 覆蓋率**：
- `repositories/user_repository.py`: 100%
- `routers/users.py`: 100%
- `services/user_service.py`: 100%
- `core/dependencies.py`: 100%
- `main.py`: 100%
- `schemas/user.py`: 100%

## 使用方式

### 1. 安裝依賴

```bash
# 使用 uv（推薦）
cd 07-test-framework
uv sync --dev

# 或使用 pip
pip install -e ".[dev]"
```

### 2. 運行測試

```bash
# 運行所有測試（自動計算覆蓋率）
uv run pytest

# 運行特定測試文件
uv run pytest tests/test_users.py

# 運行特定測試類
uv run pytest tests/test_users.py::TestGetUserEndpoint

# 運行特定測試函數
uv run pytest tests/test_users.py::TestGetUserEndpoint::test_get_user_success

# 顯示詳細輸出
uv run pytest -v

# 顯示 print 輸出
uv run pytest -s
```

### 3. 查看測試覆蓋率

```bash
# 運行測試（自動生成覆蓋率報告）
uv run pytest

# 查看 HTML 報告
open htmlcov/index.html

# 生成 XML 報告（用於 CI/CD）
uv run pytest --cov-report=xml
```

### 4. 啟動應用

```bash
# 啟動 FastAPI 應用
uv run uvicorn main:app --reload

# 訪問 API 文檔
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc

# 測試 API 端點
curl http://localhost:8000/users/1
```

## 測試文件說明

### tests/test_users.py

測試用戶端點和 Repository：

- ✅ 端點測試：成功、失敗、無效 ID
- ✅ Repository 測試：`get_by_id`、`get_by_username`、`create`
- ✅ Service 依賴測試：Mock NotificationService
- ✅ 依賴覆寫測試：Mock Repository 和 Service
- ✅ 集成測試：使用真實依賴

### tests/test_main.py

測試主模組：

- ✅ 根路徑端點測試
- ✅ 健康檢查端點測試
- ✅ FastAPI 應用配置測試

### tests/test_core.py

測試核心依賴：

- ✅ `get_current_user` 函數測試（各種 token 情況）
- ✅ `get_current_user_optional` 函數測試
- ✅ 模組導入測試

### tests/conftest.py

共享的測試 Fixtures：

- ✅ `client`: TestClient Fixture
- ✅ `async_client`: AsyncClient Fixture
- ✅ Repository Fixtures: `mock_user_repository`、`override_user_repository`
- ✅ Service Fixtures: `mock_notification_service`、`override_user_service`
- ✅ 組合 Fixtures: `user_service_with_repo`、`user_service_with_mock_notification`

## 常見問題

### Q1: Flask 和 FastAPI 測試的主要區別是什麼？

**A:** 主要區別：

1. **客戶端創建**：
   - Flask: `app.test_client()`
   - FastAPI: `TestClient(app)`

2. **JSON 回應**：
   - Flask: `response.json` (屬性)
   - FastAPI: `response.json()` (方法)

3. **錯誤訊息字段**：
   - Flask: `response.json['error']`
   - FastAPI: `response.json()['detail']`

4. **異步測試**：
   - Flask: 不支援原生異步測試
   - FastAPI: 使用 `AsyncClient` 和 `pytest-asyncio`

### Q2: 如何測試需要認證的端點？

**A:** 使用依賴覆寫：

```python
def test_authenticated_endpoint(client, override_user_repository, mock_user_repository):
    # Mock Repository 返回值
    mock_user = User(id=1, username="test_user", email="test@example.com")
    mock_user_repository.get_by_id.return_value = mock_user
    
    response = client.get("/users/1")
    assert response.status_code == 200
```

### Q3: 如何 Mock Service 依賴？

**A:** 使用 Fixture：

```python
@pytest.mark.asyncio
async def test_with_mock_service(
    user_repository_with_data,
    mock_notification_service
):
    service = UserService(
        user_repo=user_repository_with_data,
        notification_service=mock_notification_service  # Mock 依賴
    )
    
    await service.get_user(1)
    
    # 驗證 Mock 被調用
    mock_notification_service.send_notification.assert_called_once()
```

### Q4: 如何提高測試覆蓋率？

**A:** 

1. **運行覆蓋率報告**：`uv run pytest`
2. **查看未覆蓋的行**：終端會顯示 `Missing` 欄位
3. **查看 HTML 報告**：`open htmlcov/index.html` 視覺化查看
4. **為未覆蓋的代碼添加測試**

### Q5: 測試後如何清理依賴覆寫？

**A:** 使用 Fixture（推薦）：

```python
# conftest.py 中的 Fixture 會自動清理
@pytest.fixture
def override_user_repository(mock_user_repository):
    app.dependency_overrides[get_user_repository] = lambda: mock_user_repository
    yield
    app.dependency_overrides.clear()  # 自動清理
```

### Q6: 異步測試中如何使用 Mock？

**A:** 使用 `AsyncMock`：

```python
from unittest.mock import AsyncMock

mock_notification_service.send_notification = AsyncMock(return_value=None)
```

## 總結

### 關鍵要點

1. **Flask → FastAPI 遷移**：
   - `TestClient` 替代 `test_client()`
   - `json()` 方法替代 `json` 屬性
   - `detail` 字段替代 `error` 字段

2. **異步測試**：
   - 使用 `AsyncClient` 和 `@pytest.mark.asyncio`
   - 配置 `asyncio_mode = auto`

3. **依賴覆寫**：
   - 使用 `app.dependency_overrides`
   - 使用 Fixture 自動管理清理

4. **Mock Service 依賴**：
   - Service 層可以相互依賴
   - 在測試中可以獨立 Mock 每個依賴
   - 使用 `AsyncMock` 處理異步方法

5. **測試覆蓋率**：
   - 項目已配置自動計算覆蓋率
   - 當前達到 **100% 覆蓋率** ⭐
   - 使用 HTML 報告視覺化查看

### 測試統計

- ✅ **36 個測試全部通過**
- ✅ **100% 代碼覆蓋率**
- ✅ **執行時間**: ~0.10 秒
- ✅ **所有層級都有完整測試**

