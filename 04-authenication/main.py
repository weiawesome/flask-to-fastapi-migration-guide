"""
FastAPI 應用程式入口 - 中間件與錯誤處理示範
"""
import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# 導入自訂模組
from routers import users
from middleware import LoggingMiddleware, TimingMiddleware, RequestIDMiddleware
from core import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from utils import setup_logger, metrics_collector

# 設定日誌
setup_logger("fastapi_app", level=logging.INFO, log_file="logs/app.log")

# 建立 FastAPI 應用
app = FastAPI(
    title="Flask to FastAPI - 中間件與錯誤處理",
    description="""
## 本章學習重點

### 中間件 (Middleware)
- ✅ 請求日誌中間件（類似 Flask before_request/after_request）
- ✅ 請求計時中間件（效能監控）
- ✅ 請求 ID 追蹤（分散式系統必備）
- ✅ CORS 中間件（跨域設定）

### 錯誤處理 (Error Handling)
- ✅ HTTP 例外處理器
- ✅ 驗證錯誤處理器
- ✅ 全域例外處理器
- ✅ 自訂例外類別

### 共用工具 (Utils)
- ✅ 統一日誌配置
- ✅ 效能指標收集器
    """,
    version="1.0.0"
)

# ========== 1. 註冊錯誤處理器 ==========
# 類似 Flask 的 @app.errorhandler()
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# ========== 2. 加入中間件（注意順序！）==========
# 中間件的執行順序：後加入的先執行
# 所以這裡的順序是：CORS -> RequestID -> Timing -> Logging

# CORS 中間件（跨域設定）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境應該設定具體的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 自訂中間件
app.add_middleware(LoggingMiddleware)  # 日誌記錄
app.add_middleware(TimingMiddleware)   # 效能監控
app.add_middleware(RequestIDMiddleware)  # 請求追蹤

# ========== 3. 註冊路由 ==========
app.include_router(users.router)


# ========== 4. 根路徑 ==========
@app.get("/", tags=["root"])
def read_root():
    """根路徑 - API 資訊"""
    return {
        "message": "Flask to FastAPI - Middleware and Error Handling",
        "docs": "/docs",
        "endpoints": {
            "users": "/users",
            "metrics": "/metrics"
        }
    }


# ========== 5. 效能指標端點 ==========
@app.get("/metrics", tags=["monitoring"])
def get_metrics():
    """
    獲取 API 效能指標
    展示所有端點的請求次數和回應時間
    """
    return metrics_collector.get_stats()


# ========== 6. 健康檢查端點 ==========
@app.get("/health", tags=["monitoring"])
def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "middleware": {
            "logging": "enabled",
            "timing": "enabled",
            "request_id": "enabled",
            "cors": "enabled"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
