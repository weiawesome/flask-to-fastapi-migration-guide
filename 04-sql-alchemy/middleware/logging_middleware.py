"""
Logging Middleware
日志中间件 - 记录所有请求和回应
类似 Flask 的 @app.before_request 和 @app.after_request
"""
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# 设定日志 - 使用統一的 logger 名稱
logger = logging.getLogger("fastapi_app")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    日志中间件
    记录每个请求的详细信息
    
    相当于 Flask 的：
    @app.before_request
    def log_request():
        ...
    
    @app.after_request
    def log_response(response):
        ...
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        拦截所有请求和回应
        
        Args:
            request: 传入的请求
            call_next: 调用下一个中间件或路由处理器
        
        Returns:
            Response: 回应对象
        """
        # ========== Before Request（请求前）==========
        start_time = time.time()
        
        # 获取请求信息
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"
        
        logger.info(
            f"📨 Incoming request: {method} {url} from {client_host}"
        )
        
        # ========== Process Request（处理请求）==========
        # call_next 会执行路由处理器并返回回应
        response = await call_next(request)
        
        # ========== After Request（请求后）==========
        process_time = time.time() - start_time
        
        # 记录回应信息
        logger.info(
            f"📤 Response: {method} {url} "
            f"Status: {response.status_code} "
            f"Duration: {process_time:.3f}s"
        )
        
        # 在回应头中添加处理时间
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

