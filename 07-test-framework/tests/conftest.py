"""
Pytest 配置和共享 Fixtures
"""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import Mock, AsyncMock

from main import app
from repositories.user_repository import UserRepository, User
from services.user_service import UserService, NotificationService


# ========== 同步 TestClient ==========
@pytest.fixture
def client():
    """
    FastAPI TestClient Fixture
    
    對比 Flask:
    - Flask: client = app.test_client()
    - FastAPI: client = TestClient(app)
    """
    return TestClient(app)


# ========== 異步 AsyncClient ==========
@pytest.fixture
async def async_client():
    """
    異步測試客戶端
    
    用於測試異步端點
    """
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ========== Repository Fixtures ==========
@pytest.fixture
def mock_user_repository():
    """模擬用戶 Repository"""
    repo = Mock(spec=UserRepository)
    return repo


@pytest.fixture
def override_user_repository(mock_user_repository):
    """覆寫 UserRepository 依賴"""
    from repositories.user_repository import get_user_repository
    
    app.dependency_overrides[get_user_repository] = lambda: mock_user_repository
    yield
    app.dependency_overrides.clear()


# ========== Service Fixtures ==========
@pytest.fixture
def mock_notification_service():
    """模擬通知服務"""
    mock_service = Mock(spec=NotificationService)
    mock_service.send_notification = AsyncMock(return_value=None)
    return mock_service


@pytest.fixture
def override_notification_service(mock_notification_service):
    """覆寫 NotificationService 依賴"""
    from services.user_service import get_notification_service
    
    app.dependency_overrides[get_notification_service] = lambda: mock_notification_service
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user_service():
    """模擬用戶服務"""
    mock_service = Mock(spec=UserService)
    mock_service.get_user = AsyncMock()
    return mock_service


@pytest.fixture
def override_user_service(mock_user_service):
    """覆寫 UserService 依賴"""
    from services.user_service import get_user_service
    
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    yield
    app.dependency_overrides.clear()


# ========== 組合 Fixtures ==========
@pytest.fixture
def user_repository_with_data():
    """帶有測試數據的 UserRepository"""
    repo = UserRepository()
    # Repository 已經有初始數據了
    return repo


@pytest.fixture
def user_service_with_repo(user_repository_with_data):
    """帶有真實 Repository 的 UserService（用於集成測試）"""
    return UserService(user_repo=user_repository_with_data)


@pytest.fixture
def user_service_with_mock_notification(user_repository_with_data, mock_notification_service):
    """帶有 Mock NotificationService 的 UserService"""
    return UserService(
        user_repo=user_repository_with_data,
        notification_service=mock_notification_service
    )