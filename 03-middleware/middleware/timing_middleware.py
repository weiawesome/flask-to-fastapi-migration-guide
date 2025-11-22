"""
Timing Middleware
计时中间件 - 监控端点效能
"""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from utils.metrics import metrics_collector


class TimingMiddleware(BaseHTTPMiddleware):
    """
    计时中间件
    记录每个端点的执行时间，用于效能监控
    """
    
    async def dispatch(self, request: Request, call_next):
        """拦截请求并记录执行时间"""
        start_time = time.time()
        
        # 处理请求
        response = await call_next(request)
        
        # 计算执行时间
        process_time = time.time() - start_time
        
        # 记录指标
        metrics_collector.record_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=process_time
        )
        
        # 添加自定义回应头
        response.headers["X-Response-Time"] = f"{process_time:.3f}s"
        
        return response

