"""
User Repository (Async)
用戶資料存取層 (異步版本)
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
from core.exceptions import NotFoundException


class UserRepository:
    """用戶資料存取層 (異步)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """根據 ID 獲取用戶 (異步)"""
        result = await self.db.execute(
            select(User).filter(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """根據 email 獲取用戶 (異步)"""
        result = await self.db.execute(
            select(User).filter(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """根據 username 獲取用戶 (異步)"""
        result = await self.db.execute(
            select(User).filter(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def create(self, username: str, email: str, password_hash: str) -> User:
        """創建新用戶 (異步)"""
        user = User(
            username=username,
            email=email,
            password_hash=password_hash
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def exists_by_email(self, email: str) -> bool:
        """檢查 email 是否已存在 (異步)"""
        result = await self.db.execute(
            select(User).filter(User.email == email)
        )
        return result.scalar_one_or_none() is not None
    
    async def exists_by_username(self, username: str) -> bool:
        """檢查 username 是否已存在 (異步)"""
        result = await self.db.execute(
            select(User).filter(User.username == username)
        )
        return result.scalar_one_or_none() is not None

