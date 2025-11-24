"""
Todo Repository (Async)
待辦事項資料存取層 (異步版本)
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.todo import Todo
from core.exceptions import NotFoundException


class TodoRepository:
    """待辦事項資料存取層 (異步)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, todo_id: int, user_id: int) -> Optional[Todo]:
        """根據 ID 獲取 TODO（必須屬於指定用戶）(異步)"""
        result = await self.db.execute(
            select(Todo).filter(
                Todo.id == todo_id,
                Todo.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_all_by_user(self, user_id: int) -> List[Todo]:
        """獲取用戶的所有 TODO (異步)"""
        result = await self.db.execute(
            select(Todo)
            .filter(Todo.user_id == user_id)
            .order_by(Todo.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def create(self, user_id: int, title: str, description: Optional[str] = None) -> Todo:
        """創建新 TODO (異步)"""
        todo = Todo(
            user_id=user_id,
            title=title,
            description=description
        )
        self.db.add(todo)
        await self.db.commit()
        await self.db.refresh(todo)
        return todo
    
    async def update(self, todo_id: int, user_id: int, **kwargs) -> Todo:
        """更新 TODO (異步)"""
        todo = await self.get_by_id(todo_id, user_id)
        if not todo:
            raise NotFoundException(f"Todo {todo_id} not found")
        
        for key, value in kwargs.items():
            if value is not None and hasattr(todo, key):
                setattr(todo, key, value)
        
        await self.db.commit()
        await self.db.refresh(todo)
        return todo
    
    async def delete(self, todo_id: int, user_id: int) -> bool:
        """刪除 TODO (異步)"""
        todo = await self.get_by_id(todo_id, user_id)
        if not todo:
            raise NotFoundException(f"Todo {todo_id} not found")
        
        await self.db.delete(todo)
        await self.db.commit()
        return True

