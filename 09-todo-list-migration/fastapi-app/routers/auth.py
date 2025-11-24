"""
Auth Router
認證相關路由 (異步版本)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from repositories.user_repository import UserRepository
from services.auth_service import AuthService
from schemas.auth import RegisterRequest, LoginRequest, AuthResponse
from utils.cache import CacheManager
from core.exceptions import BadRequestException, UnauthorizedException

router = APIRouter(prefix="/api/v2/auth", tags=["auth"])
cache_manager = CacheManager()
security = HTTPBearer()


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """獲取 UserRepository 實例"""
    return UserRepository(db)


def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    """獲取 AuthService 實例"""
    return AuthService(user_repo)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    register_data: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """用戶註冊"""
    try:
        result = await auth_service.register(
            username=register_data.username,
            email=register_data.email,
            password=register_data.password
        )
        return result
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """用戶登入"""
    try:
        result = await auth_service.login(
            email=login_data.email,
            password=login_data.password
        )
        return result
    except UnauthorizedException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    用戶登出（將 token 加入黑名單）
    """
    token = credentials.credentials
    
    # 將 token 加入黑名單（設置 30 分鐘過期，與 JWT token 過期時間一致）
    await cache_manager.set(f"jwt:blacklist:{token}", True, ttl=1800)
    
    return {"message": "Logged out successfully"}

