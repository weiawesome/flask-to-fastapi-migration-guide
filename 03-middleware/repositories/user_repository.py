"""
User Repository
使用者資料存取層 - 目前使用記憶體儲存
下一步會改用 SQLAlchemy
"""
from typing import Optional, List
from datetime import datetime


class User:
    """使用者資料模型（簡單版本，下一步會用 SQLAlchemy ORM）"""
    def __init__(
        self,
        id: int,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.username = username
        self.email = email
        self.password = password  # 實際應用中應該加密
        self.full_name = full_name
        self.created_at = created_at or datetime.now()
    
    def to_dict(self):
        """轉換為字典（不包含密碼）"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "created_at": self.created_at
        }


class UserRepository:
    """
    使用者資料存取層
    目前使用記憶體儲存，下一步會改用 SQLAlchemy
    """
    
    def __init__(self):
        self._users: dict[int, User] = {}
        self._next_id = 1
    
    def create(self, username: str, email: str, password: str, full_name: Optional[str] = None) -> User:
        """建立新使用者"""
        user = User(
            id=self._next_id,
            username=username,
            email=email,
            password=password,
            full_name=full_name
        )
        self._users[self._next_id] = user
        self._next_id += 1
        return user
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """根據 ID 獲取使用者"""
        return self._users.get(user_id)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """根據使用者名稱獲取使用者"""
        for user in self._users.values():
            if user.username == username:
                return user
        return None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """根據 email 獲取使用者"""
        for user in self._users.values():
            if user.email == email:
                return user
        return None
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """獲取所有使用者（支援分頁）"""
        users = list(self._users.values())
        return users[skip:skip + limit]
    
    def count(self) -> int:
        """獲取使用者總數"""
        return len(self._users)
    
    def update(self, user_id: int, **kwargs) -> Optional[User]:
        """更新使用者資料"""
        user = self._users.get(user_id)
        if not user:
            return None
        
        # 更新允許的欄位
        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        
        return user
    
    def delete(self, user_id: int) -> bool:
        """刪除使用者"""
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False


# 全域 repository 實例（單例模式）
# 下一步會改用依賴注入 + SQLAlchemy Session
user_repository = UserRepository()


def get_user_repository() -> UserRepository:
    """
    獲取 UserRepository 實例
    這是一個依賴注入函數，FastAPI 會自動調用
    """
    return user_repository

