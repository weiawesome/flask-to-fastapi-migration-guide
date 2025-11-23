"""
FastAPI 應用程式入口 - 異步編程實戰示範
"""
import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# 導入自訂模組
from routers import async_demo, background_tasks
from core import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from utils import setup_logger

# 設定日誌
setup_logger("fastapi_app", level=logging.INFO, log_file="logs/app.log")


# ========== 0. Lifespan 事件處理器 ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用生命週期事件處理器
    - 啟動時：初始化異步資源（資料庫連接池、Redis 連接等）
    - 關閉時：清理異步資源
    """
    # Startup: 在應用啟動時執行
    logging.info("Initializing async resources...")
    # 這裡可以初始化異步資料庫連接池、Redis 連接等
    yield
    # Shutdown: 在應用關閉時執行
    logging.info("Cleaning up async resources...")


# 建立 FastAPI 應用
app = FastAPI(
    title="Flask to FastAPI - 異步編程實戰",
    description="""
## 本章學習重點

### ⭐ 異步編程 (Async/Await)
- ✅ **await 順序執行**：等待後執行，適合有依賴關係的操作
- ✅ **asyncio.gather 並發執行**：同時啟動多個協程，適合獨立操作
- ✅ **背景任務**：FastAPI BackgroundTasks 與 Celery 整合

### 核心概念
- 異步函數定義：`async def`
- 等待異步操作：`await` - 順序執行
- 並發執行：`asyncio.gather()` - 同時執行多個協程
- 背景任務：Celery - 立即返回，任務在背景執行
    """,
    version="1.0.0",
    lifespan=lifespan
)

# ========== 1. 註冊錯誤處理器 ==========
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# ========== 2. 加入中間件 ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== 3. 註冊路由 ==========
app.include_router(async_demo.router, prefix="/async", tags=["異步編程"])
app.include_router(background_tasks.router, prefix="/tasks", tags=["背景任務"])


# ========== 4. 根路徑 ==========
@app.get("/", tags=["root"])
async def read_root():
    """根路徑 - API 資訊"""
    return {
        "message": "Flask to FastAPI - Async Programming",
        "docs": "/docs",
        "endpoints": {
            "async_demo": "/async",
            "background_tasks": "/tasks",
        },
        "topics": [
            "Sequential await execution",
            "Concurrent execution with asyncio.gather",
            "Background tasks and Celery integration"
        ]
    }


# ========== 5. 健康檢查端點 ==========
@app.get("/health", tags=["monitoring"])
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "async_support": True,
        "features": {
            "await_sequential": "enabled",
            "gather_concurrent": "enabled",
            "background_tasks": "enabled"
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

