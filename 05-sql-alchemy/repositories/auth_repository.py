"""
Auth Repository
認證資料存取層 - 使用 SQLAlchemy
"""
from typing import Optional
from datetime import datetime
import bcrypt
from fastapi import Depends
from sqlalchemy.orm import Session

from models import AuthUser
from database import get_db


class AuthRepository:
    """
    認證資料存取層
    使用 SQLAlchemy ORM 與資料庫互動
    """
    
    def __init__(self, db: Session):
        """
        初始化 Repository
        
        Args:
            db: SQLAlchemy Session 實例
        """
        self.db = db
    
    def create(self, email: str, password: str) -> AuthUser:
        """
        建立新認證使用者（密碼會自動加密）
        
        Args:
            email: 電子郵件
            password: 原始密碼（會自動使用 bcrypt 加密）
        
        Returns:
            AuthUser: 新建立的認證使用者
        """
        # 加密密碼
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        
        auth_user = AuthUser(
            email=email,
            password=hashed_password
        )
        self.db.add(auth_user)
        self.db.commit()
        self.db.refresh(auth_user)
        return auth_user
    
    def get_by_id(self, id: int) -> Optional[AuthUser]:
        """
        根據 ID 獲取認證使用者
        
        Args:
            id: 使用者 ID
        
        Returns:
            AuthUser 或 None
        """
        return self.db.query(AuthUser).filter(AuthUser.id == id).first()
    
    def get_by_email(self, email: str) -> Optional[AuthUser]:
        """
        根據 email 獲取認證使用者
        
        Args:
            email: 電子郵件
        
        Returns:
            AuthUser 或 None
        """
        return self.db.query(AuthUser).filter(AuthUser.email == email).first()
    
    def verify_password(self, email: str, password: str) -> bool:
        """
        驗證密碼
        
        Args:
            email: 電子郵件
            password: 原始密碼
        
        Returns:
            bool: 密碼是否正確
        """
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


def get_auth_repository(db: Session = Depends(get_db)) -> AuthRepository:
    """
    獲取 AuthRepository 實例
    這是一個依賴注入函數，FastAPI 會自動調用
    
    Args:
        db: SQLAlchemy Session（透過依賴注入自動提供）
    
    Returns:
        AuthRepository: Repository 實例
    """
    return AuthRepository(db)
