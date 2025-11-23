"""
User Repository
使用者資料存取層 - 使用 SQLAlchemy
"""
from typing import Optional, List
from fastapi import Depends
from sqlalchemy.orm import Session

from models import User
from database import get_db


class UserRepository:
    """
    使用者資料存取層
    使用 SQLAlchemy ORM 與資料庫互動
    """
    
    def __init__(self, db: Session):
        """
        初始化 Repository
        
        Args:
            db: SQLAlchemy Session 實例
        """
        self.db = db
    
    def create(self, username: str, email: str, password: str, full_name: Optional[str] = None) -> User:
        """
        建立新使用者
        
        Args:
            username: 使用者名稱
            email: 電子郵件
            password: 密碼（未加密）
            full_name: 全名（可選）
        
        Returns:
            User: 新建立的使用者
        """
        user = User(
            username=username,
            email=email,
            password=password,  # 實際應用中應該加密
            full_name=full_name
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        根據 ID 獲取使用者
        
        Args:
            user_id: 使用者 ID
        
        Returns:
            User 或 None
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """
        根據使用者名稱獲取使用者
        
        Args:
            username: 使用者名稱
        
        Returns:
            User 或 None
        """
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        根據 email 獲取使用者
        
        Args:
            email: 電子郵件
        
        Returns:
            User 或 None
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        獲取所有使用者（支援分頁）
        
        Args:
            skip: 跳過筆數
            limit: 限制筆數
        
        Returns:
            List[User]: 使用者列表
        """
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def count(self) -> int:
        """
        獲取使用者總數
        
        Returns:
            int: 使用者總數
        """
        return self.db.query(User).count()
    
    def update(self, user_id: int, **kwargs) -> Optional[User]:
        """
        更新使用者資料
        
        Args:
            user_id: 使用者 ID
            **kwargs: 要更新的欄位
        
        Returns:
            User 或 None（如果使用者不存在）
        """
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        # 更新允許的欄位
        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete(self, user_id: int) -> bool:
        """
        刪除使用者
        
        Args:
            user_id: 使用者 ID
        
        Returns:
            bool: 是否成功刪除
        """
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        return True


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """
    獲取 UserRepository 實例
    這是一個依賴注入函數，FastAPI 會自動調用
    
    Args:
        db: SQLAlchemy Session（透過依賴注入自動提供）
    
    Returns:
        UserRepository: Repository 實例
    """
    return UserRepository(db)
