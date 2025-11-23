"""
Users Router
使用者相關的路由處理
展示：路徑參數、查詢參數、請求體、回應模型、Repository 模式、自訂例外
"""
from fastapi import APIRouter, status, Depends, Query
from typing import List

from schemas.user import UserCreate, UserUpdate, UserResponse
from repositories.user_repository import UserRepository, get_user_repository
from core import UserNotFoundException, UserAlreadyExistsException

# 創建路由器
router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "User not found"}}
)


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="獲取使用者列表"
)
def get_users(
    skip: int = Query(0, ge=0, description="跳過筆數"),
    limit: int = Query(10, ge=1, le=100, description="限制筆數"),
    repo: UserRepository = Depends(get_user_repository)
):
    """
    獲取使用者列表
    
    - **skip**: 跳過筆數（預設: 0）
    - **limit**: 限制筆數（預設: 10，最大: 100）
    """
    users = repo.get_all(skip=skip, limit=limit)
    return [user.to_dict() for user in users]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="獲取單一使用者"
)
def get_user(
    user_id: int,
    repo: UserRepository = Depends(get_user_repository)
):
    """
    根據 ID 獲取使用者資料
    
    - **user_id**: 使用者 ID
    """
    user = repo.get_by_id(user_id)
    if not user:
        raise UserNotFoundException(user_id)
    return user.to_dict()


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="建立新使用者"
)
def create_user(
    user_data: UserCreate,
    repo: UserRepository = Depends(get_user_repository)
):
    """
    建立新使用者
    
    請求體需要包含：
    - **username**: 使用者名稱（3-50 字元）
    - **email**: 電子郵件（需符合格式）
    - **password**: 密碼（至少 6 字元）
    - **full_name**: 全名（可選）
    """
    # 檢查使用者名稱是否已存在
    if repo.get_by_username(user_data.username):
        raise UserAlreadyExistsException(user_data.username)
    
    # 檢查 email 是否已存在
    if repo.get_by_email(user_data.email):
        raise UserAlreadyExistsException(user_data.email)
    
    # 建立新使用者
    user = repo.create(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,  # 實際應用中應該加密
        full_name=user_data.full_name
    )
    
    return user.to_dict()


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="更新使用者"
)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    repo: UserRepository = Depends(get_user_repository)
):
    """
    更新使用者資訊
    
    - **user_id**: 使用者 ID
    - 只需提供要更新的欄位
    """
    # 檢查使用者是否存在
    user = repo.get_by_id(user_id)
    if not user:
        raise UserNotFoundException(user_id)
    
    # 如果要更新 username，檢查是否已被使用
    if user_data.username and user_data.username != user.username:
        existing = repo.get_by_username(user_data.username)
        if existing:
            raise UserAlreadyExistsException(user_data.username)
    
    # 如果要更新 email，檢查是否已被使用
    if user_data.email and user_data.email != user.email:
        existing = repo.get_by_email(user_data.email)
        if existing:
            raise UserAlreadyExistsException(user_data.email)
    
    # 更新使用者
    updated_user = repo.update(
        user_id,
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name
    )
    
    return updated_user.to_dict()


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="刪除使用者"
)
def delete_user(
    user_id: int,
    repo: UserRepository = Depends(get_user_repository)
):
    """
    刪除使用者
    
    - **user_id**: 使用者 ID
    """
    success = repo.delete(user_id)
    if not success:
        raise UserNotFoundException(user_id)
    return None
