"""
依賴注入模組
用於演示如何在測試中覆寫依賴
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    獲取當前用戶（從 JWT token 中解析）
    
    在測試中，這個依賴可以被覆寫，無需真正的 JWT token
    """
    token = credentials.credentials
    
    # 簡化的驗證邏輯（實際應用中應該解析 JWT）
    if token == "valid-token":
        return {"user_id": 1, "username": "test_user"}
    elif token == "admin-token":
        return {"user_id": 2, "username": "admin", "role": "admin"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials"
    )


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional)
) -> Optional[dict]:
    """
    可選的用戶驗證（用於公開端點或可選認證）
    """
    if not credentials:
        return None
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None
