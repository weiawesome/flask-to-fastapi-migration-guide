"""
Users Router - 簡化版本
只有一個端點：GET /users/{user_id}
"""
from fastapi import APIRouter, Depends, HTTPException, status

from services.user_service import UserService, get_user_service
from schemas.user import UserResponse

router = APIRouter(
    prefix="/users",
    tags=["users"]
)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="根據 ID 獲取用戶"
)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """
    根據 ID 獲取用戶
    
    - **user_id**: 用戶 ID
    """
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    return user.to_dict()