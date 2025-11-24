"""
Dependencies
依賴注入 - 認證相關
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.jwt_utils import verify_token
from utils.cache import CacheManager

security = HTTPBearer()
cache_manager = CacheManager()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """
    獲取當前用戶 ID（從 JWT token）
    
    Args:
        credentials: HTTP Bearer token 憑證
    
    Returns:
        int: 當前用戶 ID
    
    Raises:
        HTTPException: 如果 token 無效或已登出
    """
    token = credentials.credentials
    
    # 檢查 token 是否在黑名單中（登出）
    blacklisted = await cache_manager.get(f"jwt:blacklist:{token}")
    if blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )
    
    # 驗證 token
    try:
        payload = verify_token(token)
        user_id = int(payload.get("sub"))
        return user_id
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

