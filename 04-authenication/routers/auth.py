"""
Auth Router
認證相關的路由處理
"""
from fastapi import APIRouter, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from schemas.auth import AuthCreate, AuthLogin, AuthResponse, AuthMe
from repositories.auth_repository import AuthRepository, AuthUser, get_auth_repository
from core import (
    UserNotFoundException,
    UserAlreadyExistsException,
    InvalidCredentialsException,
    InvalidTokenException
)
from middleware.jwt_middleware import get_current_user_id
from utils.jwt import create_token_for_user

# HTTP Bearer Token 安全方案（用於 Swagger 文檔顯示）
# auto_error=False 表示不會自動拋錯，由我們的邏輯來處理
security = HTTPBearer(auto_error=False)

# 創建路由器
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Auth not found"}}
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    repo: AuthRepository = Depends(get_auth_repository)
) -> AuthUser:
    """
    從 middleware 提供的 user_id 獲取當前使用者
    
    這個函數作為 FastAPI 的依賴注入使用，例如：
    @router.get("/me")
    def me(user: AuthUser = Depends(get_current_user)):
        return user
    
    Args:
        credentials: HTTP Bearer token 憑證（用於 Swagger 文檔顯示認證選項）
        repo: AuthRepository 實例（透過依賴注入）
    
    Returns:
        AuthUser: 當前認證的使用者
    
    Raises:
        InvalidTokenException: 未提供 token 或 token 無效
        UserNotFoundException: 使用者不存在
    
    Note:
        credentials 參數主要是為了讓 Swagger 文檔顯示認證選項
        實際的 token 驗證由 JWTAuthMiddleware 完成
    """
    # 從 middleware 獲取 user_id（實際驗證在 middleware 中完成）
    user_id = get_current_user_id()
    
    if user_id is None:
        raise InvalidTokenException("Authentication required")
    
    # 從資料庫獲取使用者
    user = repo.get_by_id(user_id)
    if user is None:
        raise UserNotFoundException(user_id)
    
    return user


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    auth_data: AuthCreate,
    repo: AuthRepository = Depends(get_auth_repository)
):
    """
    註冊新使用者
    
    請求體需要包含：
    - **email**: 電子郵件（需符合格式）
    - **password**: 密碼（至少 6 字元）
    """
    # 檢查 email 是否已存在
    if repo.get_by_email(auth_data.email):
        raise UserAlreadyExistsException(auth_data.email)
    
    # 建立新使用者
    user = repo.create(auth_data.email, auth_data.password)
    
    # 創建 JWT token
    access_token = create_token_for_user(user.id, user.email)
    
    return AuthResponse(
        access_token=access_token,
        token_type="Bearer"
    )


@router.post("/login", response_model=AuthResponse)
def login(
    auth_data: AuthLogin,
    repo: AuthRepository = Depends(get_auth_repository)
):
    """
    使用者登入
    
    請求體需要包含：
    - **email**: 電子郵件
    - **password**: 密碼
    """
    # 驗證密碼
    if not repo.verify_password(auth_data.email, auth_data.password):
        raise InvalidCredentialsException(auth_data.email)
    
    # 獲取使用者
    user = repo.get_by_email(auth_data.email)
    if not user:
        raise UserNotFoundException(0)  # 理論上不會到這裡
    
    # 創建 JWT token
    access_token = create_token_for_user(user.id, user.email)
    
    return AuthResponse(
        access_token=access_token,
        token_type="Bearer"
    )


@router.get("/me", response_model=AuthMe)
def me(user = Depends(get_current_user)):
    """
    獲取當前使用者資訊
    
    需要 Bearer token 認證
    """
    return AuthMe(
        id=user.id,
        email=user.email,
        created_at=user.created_at
    )