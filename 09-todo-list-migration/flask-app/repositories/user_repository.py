"""
User Repository
用戶資料存取層
"""
from typing import Optional
from sqlalchemy.orm import Session
from models.user import User
from core.exceptions import NotFoundException


class UserRepository:
    """用戶資料存取層"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """根據 ID 獲取用戶"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """根據 email 獲取用戶"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """根據 username 獲取用戶"""
        return self.db.query(User).filter(User.username == username).first()
    
    def create(self, username: str, email: str, password_hash: str) -> User:
        """創建新用戶"""
        user = User(
            username=username,
            email=email,
            password_hash=password_hash
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def exists_by_email(self, email: str) -> bool:
        """檢查 email 是否已存在"""
        return self.db.query(User).filter(User.email == email).first() is not None
    
    def exists_by_username(self, username: str) -> bool:
        """檢查 username 是否已存在"""
        return self.db.query(User).filter(User.username == username).first() is not None

