"""
Users 端點測試

展示：
- Flask test_client → FastAPI TestClient
- 依賴覆寫（Repository、Service）
- Mock Service 依賴（NotificationService）
- 異步測試
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock

from repositories.user_repository import UserRepository, User
from services.user_service import UserService, NotificationService


class TestGetUserEndpoint:
    """測試 GET /users/{user_id} 端點"""
    
    def test_get_user_success(self, client, override_user_repository, mock_user_repository):
        """測試成功獲取用戶"""
        # 設置 Mock Repository 返回用戶
        mock_user = User(id=1, username="alice", email="alice@example.com")
        mock_user_repository.get_by_id.return_value = mock_user
        
        response = client.get("/users/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["username"] == "alice"
        assert data["email"] == "alice@example.com"
        
        # 驗證 Repository 被調用
        mock_user_repository.get_by_id.assert_called_once_with(1)
    
    def test_get_user_not_found(self, client, override_user_repository, mock_user_repository):
        """測試用戶不存在"""
        # 設置 Mock Repository 返回 None
        mock_user_repository.get_by_id.return_value = None
        
        response = client.get("/users/999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
        # 驗證 Repository 被調用
        mock_user_repository.get_by_id.assert_called_once_with(999)
    
    def test_get_user_invalid_id(self, client):
        """測試無效的用戶 ID"""
        # 負數 ID 會被 FastAPI 驗證拒絕（如果配置了驗證）
        response = client.get("/users/-1")
        # 根據配置，可能會返回 422 或正常處理
        assert response.status_code in [404, 422]


@pytest.mark.asyncio
class TestGetUserAsync:
    """異步測試 GET /users/{user_id} 端點"""
    
    async def test_get_user_async(self, async_client, override_user_repository, mock_user_repository):
        """異步測試獲取用戶"""
        mock_user = User(id=2, username="bob", email="bob@example.com")
        mock_user_repository.get_by_id.return_value = mock_user
        
        response = await async_client.get("/users/2")
        
        assert response.status_code == 200
        assert response.json()["username"] == "bob"


class TestUserServiceDependencies:
    """測試 UserService 的依賴（演示 Mock Service 依賴）"""
    
    @pytest.mark.asyncio
    async def test_user_service_without_notification(self, user_repository_with_data):
        """測試 UserService 沒有 NotificationService 的情況"""
        service = UserService(user_repo=user_repository_with_data)
        
        user = await service.get_user(1)
        
        assert user is not None
        assert user.id == 1
    
    @pytest.mark.asyncio
    async def test_user_service_with_notification(
        self,
        user_repository_with_data,
        mock_notification_service
    ):
        """測試 UserService 調用 NotificationService"""
        service = UserService(
            user_repo=user_repository_with_data,
            notification_service=mock_notification_service
        )
        
        user = await service.get_user(1)
        
        assert user is not None
        assert user.id == 1
        
        # 驗證 NotificationService 被調用
        mock_notification_service.send_notification.assert_called_once()
        call_args = mock_notification_service.send_notification.call_args[0][0]
        assert "User 1" in call_args
        assert "alice" in call_args
    
    @pytest.mark.asyncio
    async def test_user_service_with_notification_user_not_found(
        self,
        user_repository_with_data,
        mock_notification_service
    ):
        """測試用戶不存在時，NotificationService 不會被調用"""
        service = UserService(
            user_repo=user_repository_with_data,
            notification_service=mock_notification_service
        )
        
        user = await service.get_user(999)  # 不存在的用戶
        
        assert user is None
        
        # 驗證 NotificationService 沒有被調用
        mock_notification_service.send_notification.assert_not_called()


class TestDependencyOverride:
    """測試依賴覆寫"""
    
    def test_override_repository(self, client, override_user_repository, mock_user_repository):
        """測試覆寫 Repository 依賴"""
        mock_user = User(id=100, username="test_user", email="test@example.com")
        mock_user_repository.get_by_id.return_value = mock_user
        
        response = client.get("/users/100")
        
        assert response.status_code == 200
        assert response.json()["username"] == "test_user"
    
    def test_override_service(self, client, override_user_service, mock_user_service):
        """測試覆寫 Service 依賴"""
        from repositories.user_repository import User as RepoUser
        
        mock_user = RepoUser(id=200, username="service_user", email="service@example.com")
        mock_user_service.get_user = AsyncMock(return_value=mock_user)
        
        response = client.get("/users/200")
        
        assert response.status_code == 200
        assert response.json()["username"] == "service_user"
        
        # 驗證 Service 被調用
        mock_user_service.get_user.assert_called_once_with(200)


class TestUserRepository:
    """測試 UserRepository 方法（提高覆蓋率）"""
    
    def test_get_by_username_found(self, user_repository_with_data):
        """測試根據用戶名獲取用戶（找到）"""
        user = user_repository_with_data.get_by_username("alice")
        
        assert user is not None
        assert user.id == 1
        assert user.username == "alice"
        assert user.email == "alice@example.com"
    
    def test_get_by_username_not_found(self, user_repository_with_data):
        """測試根據用戶名獲取用戶（未找到）"""
        user = user_repository_with_data.get_by_username("nonexistent")
        
        assert user is None
    
    def test_get_by_username_multiple_users(self, user_repository_with_data):
        """測試在多個用戶中查找"""
        user = user_repository_with_data.get_by_username("bob")
        
        assert user is not None
        assert user.username == "bob"
        assert user.id == 2
    
    def test_create_user(self):
        """測試創建新用戶"""
        repo = UserRepository()
        initial_count = len(repo._users)
        
        new_user = repo.create(username="new_user", email="new@example.com")
        
        assert new_user is not None
        assert new_user.username == "new_user"
        assert new_user.email == "new@example.com"
        # 驗證用戶已添加到存儲中
        assert len(repo._users) == initial_count + 1
        assert new_user.id in repo._users
        assert repo._users[new_user.id] == new_user
    
    def test_create_user_auto_increment_id(self):
        """測試創建用戶時自動遞增 ID"""
        repo = UserRepository()
        max_id = max(repo._users.keys()) if repo._users else 0
        
        new_user = repo.create(username="auto_user", email="auto@example.com")
        
        assert new_user.id == max_id + 1
    
    def test_create_user_empty_repository(self):
        """測試在空 Repository 中創建用戶"""
        repo = UserRepository()
        repo._users = {}  # 清空用戶列表
        
        new_user = repo.create(username="first_user", email="first@example.com")
        
        assert new_user.id == 1
        assert len(repo._users) == 1
    
    def test_user_to_dict(self):
        """測試 User.to_dict() 方法"""
        user = User(id=1, username="test", email="test@example.com")
        
        result = user.to_dict()
        
        assert result == {
            "id": 1,
            "username": "test",
            "email": "test@example.com"
        }
        assert isinstance(result, dict)


class TestIntegration:
    """集成測試（使用真實的 Repository 和 Service）"""
    
    @pytest.mark.asyncio
    async def test_integration_get_user(self, async_client):
        """集成測試：使用真實的 Repository 和 Service"""
        response = await async_client.get("/users/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["username"] == "alice"
    
    @pytest.mark.asyncio
    async def test_integration_user_not_found(self, async_client):
        """集成測試：用戶不存在"""
        response = await async_client.get("/users/9999")
        
        assert response.status_code == 404