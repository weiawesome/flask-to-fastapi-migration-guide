"""
Todo Repository
待辦事項資料存取層
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from models.todo import Todo
from core.exceptions import NotFoundException


class TodoRepository:
    """待辦事項資料存取層"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, todo_id: int, user_id: int) -> Optional[Todo]:
        """根據 ID 獲取 TODO（必須屬於指定用戶）"""
        return self.db.query(Todo).filter(
            Todo.id == todo_id,
            Todo.user_id == user_id
        ).first()
    
    def get_all_by_user(self, user_id: int) -> List[Todo]:
        """獲取用戶的所有 TODO"""
        return self.db.query(Todo).filter(
            Todo.user_id == user_id
        ).order_by(Todo.created_at.desc()).all()
    
    def create(self, user_id: int, title: str, description: Optional[str] = None) -> Todo:
        """創建新 TODO"""
        todo = Todo(
            user_id=user_id,
            title=title,
            description=description
        )
        self.db.add(todo)
        self.db.commit()
        self.db.refresh(todo)
        return todo
    
    def update(self, todo_id: int, user_id: int, **kwargs) -> Todo:
        """更新 TODO"""
        todo = self.get_by_id(todo_id, user_id)
        if not todo:
            raise NotFoundException(f"Todo {todo_id} not found")
        
        for key, value in kwargs.items():
            if value is not None and hasattr(todo, key):
                setattr(todo, key, value)
        
        self.db.commit()
        self.db.refresh(todo)
        return todo
    
    def delete(self, todo_id: int, user_id: int) -> bool:
        """刪除 TODO"""
        todo = self.get_by_id(todo_id, user_id)
        if not todo:
            raise NotFoundException(f"Todo {todo_id} not found")
        
        self.db.delete(todo)
        self.db.commit()
        return True

