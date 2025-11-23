"""
Auth Repository
登入資料存取層 - 目前使用記憶體儲存
下一步會改用 SQLAlchemy
"""
from typing import Optional, List
from datetime import datetime
import bcrypt

class AuthUser:
    """登入使用者模型"""
    def __init__(self, id: int, email: str, password: str, created_at: datetime):
        self.id = id
        self.email = email
        self.password = password
        self.created_at = created_at
    
    def to_dict(self):
        """轉換為字典"""
        return {
            "id": self.id,
            "email": self.email,
            "created_at": self.created_at
        }

class AuthRepository:
    """登入資料存取層"""
    def __init__(self):
        self._auth_users: dict[int, AuthUser] = {}
        self._next_id = 1
    
    def create(self, email: str, password: str) -> AuthUser:
        """建立新登入使用者"""
        # 加密密碼
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        
        auth_user = AuthUser(
            id=self._next_id,
            email=email,
            password=hashed_password,
            created_at=datetime.now()
        )
        self._auth_users[self._next_id] = auth_user
        self._next_id += 1
        return auth_user
    
    def get_by_id(self, id: int) -> Optional[AuthUser]:
        """根據 ID 獲取登入使用者"""
        return self._auth_users.get(id)
    
    def get_by_email(self, email: str) -> Optional[AuthUser]:
        """根據 email 獲取登入使用者"""
        for auth_user in self._auth_users.values():
            if auth_user.email == email:
                return auth_user
        return None

    def verify_password(self, email: str, password: str) -> bool:
        """驗證密碼"""
        auth_user = self.get_by_email(email)
        if not auth_user:
            return False
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                auth_user.password.encode('utf-8')
            )
        except Exception:
            return False


# 全域 repository 實例（單例模式）
# 下一步會改用依賴注入 + SQLAlchemy Session
auth_repository = AuthRepository()


def get_auth_repository() -> AuthRepository:
    """
    獲取 AuthRepository 實例
    這是一個依賴注入函數，FastAPI 會自動調用
    """
    return auth_repository