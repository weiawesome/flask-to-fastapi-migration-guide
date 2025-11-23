"""
User Repository - 用戶資料存取層
使用 Memory 存儲，用於演示測試框架
"""
from typing import Optional


class User:
    """用戶資料模型"""
    
    def __init__(self, id: int, username: str, email: str):
        self.id = id
        self.username = username
        self.email = email
    
    def to_dict(self):
        """轉換為字典"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email
        }


class UserRepository:
    """用戶資料存取層（Memory 存儲）"""
    
    def __init__(self):
        # 初始化一些測試數據
        self._users: dict[int, User] = {
            1: User(id=1, username="alice", email="alice@example.com"),
            2: User(id=2, username="bob", email="bob@example.com"),
            3: User(id=3, username="charlie", email="charlie@example.com"),
        }
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """根據 ID 獲取用戶"""
        return self._users.get(user_id)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """根據用戶名獲取用戶"""
        for user in self._users.values():
            if user.username == username:
                return user
        return None
    
    def create(self, username: str, email: str) -> User:
        """創建新用戶"""
        user_id = max(self._users.keys(), default=0) + 1
        user = User(id=user_id, username=username, email=email)
        self._users[user_id] = user
        return user


# 依賴注入
_user_repository = UserRepository()


def get_user_repository() -> UserRepository:
    """獲取 UserRepository 實例（依賴注入）"""
    return _user_repository
