"""
FastAPI 應用程式入口 - SQLAlchemy 資料庫整合示範
"""
import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# 導入自訂模組
from routers import users, auth
from middleware import (
    LoggingMiddleware,
    TimingMiddleware,
    RequestIDMiddleware,
    JWTAuthMiddleware
)
from core import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from utils import setup_logger, metrics_collector
from database import init_db
# 設定日誌
setup_logger("fastapi_app", level=logging.INFO, log_file="logs/app.log")


# ========== 0. Lifespan 事件處理器 ==========
# 使用新的 lifespan 事件處理器（替代已棄用的 @app.on_event）
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用生命週期事件處理器
    - 啟動時：初始化資料庫
    - 關閉時：可在此處添加清理邏輯
    """
    # Startup: 在應用啟動時執行
    init_db()
    logging.info("Database initialized")
    yield
    # Shutdown: 在應用關閉時執行（如果需要清理資源）
    # 例如：關閉資料庫連接池等


# 建立 FastAPI 應用
app = FastAPI(
    title="Flask to FastAPI - SQLAlchemy 資料庫整合",
    description="""
## 本章學習重點

### ⭐ SQLAlchemy ORM 框架導入與使用
- ✅ **SQLAlchemy 核心導入**：`create_engine`, `declarative_base`, `sessionmaker`
- ✅ **資料庫配置**：Engine、Session、Base 的設定與管理
- ✅ **ORM 模型定義**：使用 `Column` 定義資料表結構
- ✅ **Repository 模式**：封裝 SQLAlchemy 查詢邏輯
- ✅ **依賴注入 Session**：使用 FastAPI `Depends` 管理資料庫連接
- ✅ **SQLite 資料庫初始化**：自動創建資料表和連接管理
- ✅ **Flask-SQLAlchemy → FastAPI + SQLAlchemy** 轉換對比

### 中間件 (Middleware)
- ✅ 請求日誌中間件
- ✅ 請求計時中間件
- ✅ 請求 ID 追蹤
- ✅ CORS 中間件
- ✅ JWT 認證中間件

### 錯誤處理 (Error Handling)
- ✅ HTTP 例外處理器
- ✅ 驗證錯誤處理器
- ✅ 全域例外處理器
- ✅ 自訂例外類別

### 共用工具 (Utils)
- ✅ 統一日誌配置
- ✅ 效能指標收集器
    """,
    version="1.0.0",
    lifespan=lifespan
)

# ========== 1. 註冊錯誤處理器 ==========
# 類似 Flask 的 @app.errorhandler()
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# ========== 2. 加入中間件（注意順序！）==========
# 中間件的執行順序：後加入的先執行
# 所以這裡的順序是：CORS -> JWT -> RequestID -> Timing -> Logging

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
app.add_middleware(JWTAuthMiddleware)  # JWT 認證（驗證 token 並提供 user_id）

# ========== 3. 註冊路由 ==========
app.include_router(users.router)
app.include_router(auth.router)


# ========== 4. 根路徑 ==========
@app.get("/", tags=["root"])
def read_root():
    """根路徑 - API 資訊"""
    return {
        "message": "Flask to FastAPI - SQLAlchemy Database Integration",
        "docs": "/docs",
        "database": "SQLite (app.db)",
        "endpoints": {
            "users": "/users",
            "auth": "/auth",
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
        "database": "SQLite (initialized)",
        "middleware": {
            "logging": "enabled",
            "timing": "enabled",
            "request_id": "enabled",
            "cors": "enabled",
            "jwt_auth": "enabled"
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
