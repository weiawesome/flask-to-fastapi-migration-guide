"""
Todos Router
待辦事項相關路由 (異步版本)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from database import get_db
from repositories.todo_repository import TodoRepository
from services.todo_service import TodoService
from schemas.todo import TodoCreate, TodoUpdate, TodoResponse
from utils.cache import CacheManager
from core.dependencies import get_current_user_id
from core.exceptions import NotFoundException, BadRequestException

router = APIRouter(prefix="/api/v2/todos", tags=["todos"])
cache_manager = CacheManager()


def get_todo_repository(db: AsyncSession = Depends(get_db)) -> TodoRepository:
    """獲取 TodoRepository 實例"""
    return TodoRepository(db)


def get_todo_service(
    todo_repo: TodoRepository = Depends(get_todo_repository),
    cache: CacheManager = Depends(lambda: cache_manager)
) -> TodoService:
    """獲取 TodoService 實例"""
    return TodoService(todo_repo, cache)


@router.get("", response_model=List[TodoResponse])
async def get_all_todos(
    user_id: int = Depends(get_current_user_id),
    todo_service: TodoService = Depends(get_todo_service)
):
    """獲取用戶的所有 TODO"""
    todos = await todo_service.get_all_todos(user_id)
    return todos


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: int,
    user_id: int = Depends(get_current_user_id),
    todo_service: TodoService = Depends(get_todo_service)
):
    """獲取單個 TODO"""
    try:
        todo = await todo_service.get_todo(todo_id, user_id)
        return todo
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(
    todo_data: TodoCreate,
    user_id: int = Depends(get_current_user_id),
    todo_service: TodoService = Depends(get_todo_service)
):
    """創建新 TODO"""
    todo = await todo_service.create_todo(
        user_id=user_id,
        title=todo_data.title,
        description=todo_data.description
    )
    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: int,
    todo_data: TodoUpdate,
    user_id: int = Depends(get_current_user_id),
    todo_service: TodoService = Depends(get_todo_service)
):
    """更新 TODO"""
    try:
        todo = await todo_service.update_todo(
            todo_id=todo_id,
            user_id=user_id,
            title=todo_data.title,
            description=todo_data.description,
            completed=todo_data.completed
        )
        return todo
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )


@router.delete("/{todo_id}")
async def delete_todo(
    todo_id: int,
    user_id: int = Depends(get_current_user_id),
    todo_service: TodoService = Depends(get_todo_service)
):
    """刪除 TODO"""
    try:
        await todo_service.delete_todo(todo_id, user_id)
        return {"message": "Todo deleted successfully"}
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

