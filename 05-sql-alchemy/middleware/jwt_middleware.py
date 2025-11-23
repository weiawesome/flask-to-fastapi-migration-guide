"""
JWT Middleware
JWT 中間件 - 負責驗證 JWT token 並提供 user_id
類似 RequestIDMiddleware，將驗證後的 user_id 存儲到 ContextVar 中
"""
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from contextvars import ContextVar
from utils.jwt import verify_token
from core.exceptions import InvalidTokenException

# 使用 ContextVar 儲存當前使用者 ID（線程安全）
current_user_id_var: ContextVar[Optional[int]] = ContextVar('current_user_id', default=None)


def get_current_user_id() -> Optional[int]:
    """
    獲取當前請求的使用者 ID
    
    Returns:
        Optional[int]: 使用者 ID，如果未認證則返回 None
    """
    return current_user_id_var.get()


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    JWT 認證中間件
    驗證請求中的 JWT token，並將 user_id 存儲到 ContextVar 中
    
    這個中間件是可選的，不會強制要求所有請求都必須有 token
    如果沒有 token 或 token 無效，user_id 會是 None
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        驗證 JWT token 並提取 user_id
        
        優先從 Authorization header 中獲取 Bearer token
        如果 token 有效，將 user_id 存儲到 ContextVar
        """
        user_id = None
        
        # 嘗試從 Authorization header 獲取 token
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            
            try:
                # 驗證 token
                payload = verify_token(token)
                
                # 從 token 中提取 user_id
                user_id_str = payload.get("sub")
                if user_id_str:
                    user_id = int(user_id_str)
            except (InvalidTokenException, ValueError, TypeError):
                # Token 無效或格式錯誤，但不阻止請求繼續
                # 讓路由層決定是否需要認證
                pass
        
        # 將 user_id 存儲到 ContextVar
        current_user_id_var.set(user_id)
        
        # 處理請求
        response = await call_next(request)
        
        return response
