"""
Todo Service (Async)
待辦事項服務層 (異步版本)
"""
from typing import List, Optional
from repositories.todo_repository import TodoRepository
from utils.cache import CacheManager
from core.exceptions import NotFoundException
from models.todo import Todo


class TodoService:
    """待辦事項服務層 (異步)"""
    
    def __init__(self, todo_repo: TodoRepository, cache_manager: CacheManager):
        self.todo_repo = todo_repo
        self.cache = cache_manager
    
    async def get_all_todos(self, user_id: int) -> List[dict]:
        """
        獲取用戶的所有 TODO（帶快取）(異步)
        
        Args:
            user_id: 用戶 ID
            
        Returns:
            List[dict]: TODO 列表
        """
        cache_key = f"todos:user:{user_id}"
        
        async def fetch_todos():
            todos = await self.todo_repo.get_all_by_user(user_id)
            # 返回列表，即使是空列表也要返回（不要返回 None）
            return [todo.to_dict() for todo in todos]
        
        # 使用快取（自動處理雪崩、穿透、擊穿）
        # 注意：對於列表查詢，不使用布隆過濾器，因為空列表是有效結果
        todos = await self.cache.get_or_set(
            key=cache_key,
            fetch_func=fetch_todos,
            ttl=3600,  # 1 小時
            check_bloom=False  # 列表查詢不使用布隆過濾器（空列表是有效結果）
        )
        
        # 優化：移除額外的檢查，get_or_set 已經處理了所有情況
        return todos if todos is not None else []
    
    async def get_todo(self, todo_id: int, user_id: int) -> dict:
        """
        獲取單個 TODO（帶快取）(異步)
        
        Args:
            todo_id: TODO ID
            user_id: 用戶 ID
            
        Returns:
            dict: TODO 資料
            
        Raises:
            NotFoundException: 如果 TODO 不存在
        """
        cache_key = f"todo:{todo_id}"
        
        async def fetch_todo():
            todo = await self.todo_repo.get_by_id(todo_id, user_id)
            if not todo:
                return None
            return todo.to_dict()
        
        # 使用快取（自動處理雪崩、穿透、擊穿）
        todo = await self.cache.get_or_set(
            key=cache_key,
            fetch_func=fetch_todo,
            ttl=3600  # 1 小時
        )
        
        if todo is None:
            raise NotFoundException(f"Todo {todo_id} not found")
        
        return todo
    
    async def create_todo(self, user_id: int, title: str, description: Optional[str] = None) -> dict:
        """
        創建新 TODO (異步)
        
        Args:
            user_id: 用戶 ID
            title: 標題
            description: 描述
            
        Returns:
            dict: 創建的 TODO 資料
        """
        todo = await self.todo_repo.create(user_id, title, description)
        
        # 使相關快取失效（創建後需要清除列表快取）
        await self.cache.invalidate_user_todos(user_id)
        # 雖然是新創建的，但為了保險起見也清除單個 todo 快取
        await self.cache.invalidate_todo(todo.id)
        
        return todo.to_dict()
    
    async def update_todo(
        self,
        todo_id: int,
        user_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        completed: Optional[bool] = None
    ) -> dict:
        """
        更新 TODO (異步)
        
        Args:
            todo_id: TODO ID
            user_id: 用戶 ID
            title: 標題（可選）
            description: 描述（可選）
            completed: 完成狀態（可選）
            
        Returns:
            dict: 更新後的 TODO 資料
            
        Raises:
            NotFoundException: 如果 TODO 不存在
        """
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if description is not None:
            update_data["description"] = description
        if completed is not None:
            update_data["completed"] = completed
        
        todo = await self.todo_repo.update(todo_id, user_id, **update_data)
        
        # 使相關快取失效（更新後需要清除單個 todo 和列表快取）
        await self.cache.invalidate_todo(todo_id)
        await self.cache.invalidate_user_todos(user_id)
        
        return todo.to_dict()
    
    async def delete_todo(self, todo_id: int, user_id: int) -> bool:
        """
        刪除 TODO (異步)
        
        Args:
            todo_id: TODO ID
            user_id: 用戶 ID
            
        Returns:
            bool: 是否刪除成功
            
        Raises:
            NotFoundException: 如果 TODO 不存在
        """
        result = await self.todo_repo.delete(todo_id, user_id)
        
        # 使相關快取失效（刪除後需要清除單個 todo 和列表快取）
        await self.cache.invalidate_todo(todo_id)
        await self.cache.invalidate_user_todos(user_id)
        
        return result

