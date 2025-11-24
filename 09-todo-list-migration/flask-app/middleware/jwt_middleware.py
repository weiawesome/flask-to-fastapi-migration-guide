"""
JWT Middleware
JWT 認證中間件
"""
from functools import wraps
from flask import request, g
from core.exceptions import UnauthorizedException
from utils.jwt_utils import verify_token
from utils.cache import CacheManager


cache_manager = CacheManager()


def jwt_middleware(app):
    """
    註冊 JWT 認證中間件
    
    Args:
        app: Flask 應用實例
    """
    @app.before_request
    def verify_jwt_token():
        # 排除認證相關的路由
        if request.path.startswith('/api/v1/auth/'):
            return None
        
        # 獲取 Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            raise UnauthorizedException("Missing authorization header")
        
        # 檢查 Bearer token 格式
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != 'bearer':
                raise UnauthorizedException("Invalid authorization scheme")
        except ValueError:
            raise UnauthorizedException("Invalid authorization header format")
        
        # 檢查 token 是否在黑名單中（登出）
        if cache_manager.get(f"jwt:blacklist:{token}"):
            raise UnauthorizedException("Token has been revoked")
        
        # 驗證 token
        try:
            payload = verify_token(token)
            g.current_user_id = int(payload.get("sub"))
            g.current_user_email = payload.get("email")
        except ValueError as e:
            raise UnauthorizedException(str(e))


def get_current_user_id() -> int:
    """
    獲取當前用戶 ID（從 Flask g 對象）
    
    Returns:
        int: 當前用戶 ID
    
    Raises:
        UnauthorizedException: 如果用戶未認證
    """
    user_id = getattr(g, 'current_user_id', None)
    if user_id is None:
        raise UnauthorizedException("User not authenticated")
    return user_id


def require_auth(f):
    """
    裝飾器：要求認證
    
    Usage:
        @blueprint.route('/todos')
        @require_auth
        def get_todos():
            user_id = get_current_user_id()
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # jwt_middleware 已經處理了認證
        # 這裡只是確保裝飾器存在
        return f(*args, **kwargs)
    return decorated_function

