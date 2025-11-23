"""
Request ID Middleware
请求追踪中间件 - 为每个请求生成唯一 ID
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from contextvars import ContextVar

# 使用 ContextVar 储存请求 ID（线程安全）
request_id_var: ContextVar[str] = ContextVar('request_id', default='')


def get_request_id() -> str:
    """获取当前请求的 ID"""
    return request_id_var.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    请求 ID 中间件
    为每个请求生成唯一的追踪 ID，方便日志追踪和调试
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        为每个请求生成唯一 ID
        
        优先使用客户端提供的 X-Request-ID
        否则自动生成新的 UUID
        """
        # 尝试从请求头获取 Request ID
        request_id = request.headers.get("X-Request-ID")
        
        # 如果没有，生成新的 UUID
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # 储存到 ContextVar（方便在任何地方获取）
        request_id_var.set(request_id)
        
        # 处理请求
        response = await call_next(request)
        
        # 在回应头中返回 Request ID
        response.headers["X-Request-ID"] = request_id
        
        return response

