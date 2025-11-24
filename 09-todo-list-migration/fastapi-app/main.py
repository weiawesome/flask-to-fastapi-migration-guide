"""
FastAPI Application
FastAPI 應用程式入口 (異步版本)
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 導入模組
from database import init_db
from routers import auth_router, todos_router
from core.error_handlers import (
    not_found_exception_handler,
    unauthorized_exception_handler,
    bad_request_exception_handler,
    validation_exception_handler
)
from core.exceptions import (
    NotFoundException,
    UnauthorizedException,
    BadRequestException,
    ValidationException
)


# Lifespan 事件處理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用生命週期事件處理器
    - 啟動時：初始化資料庫、預先建立 Redis 連接
    - 關閉時：可在此處添加清理邏輯
    """
    # Startup: 在應用啟動時執行
    await init_db()
    
    # 預先建立 Redis 連接（優化性能，避免第一次請求時的延遲）
    try:
        from routers.todos import cache_manager as todos_cache_manager
        from routers.auth import cache_manager as auth_cache_manager
        
        # 預先建立連接
        await todos_cache_manager._get_redis()
        await auth_cache_manager._get_redis()
        print("✅ Redis connections pre-initialized")
    except Exception as e:
        print(f"⚠️  Warning: Could not pre-initialize Redis connections: {e}")
    
    yield
    # Shutdown: 在應用關閉時執行（如果需要清理資源）
    # 關閉 Redis 連接
    try:
        from routers.todos import cache_manager as todos_cache_manager
        from routers.auth import cache_manager as auth_cache_manager
        
        if todos_cache_manager.redis_client:
            await todos_cache_manager.redis_client.close()
        if auth_cache_manager.redis_client:
            await auth_cache_manager.redis_client.close()
        print("✅ Redis connections closed")
    except Exception as e:
        print(f"⚠️  Warning: Error closing Redis connections: {e}")


# 創建 FastAPI 應用
app = FastAPI(
    title="FastAPI TO-DO List API",
    description="""
    ## FastAPI TO-DO List API (異步版本)
    
    ### 核心特性
    - ✅ 完全異步架構 (async/await)
    - ✅ PostgreSQL + asyncpg (異步資料庫)
    - ✅ Redis + aioredis (異步快取)
    - ✅ 快取雪崩/穿透/擊穿解決方案
    - ✅ JWT 認證系統
    - ✅ 分層架構 (Router → Service → Repository)
    
    ### API 端點
    - `/api/v2/auth/*` - 認證相關
    - `/api/v2/todos/*` - 待辦事項 CRUD
    """,
    version="2.0.0",
    lifespan=lifespan
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊錯誤處理器
app.add_exception_handler(NotFoundException, not_found_exception_handler)
app.add_exception_handler(UnauthorizedException, unauthorized_exception_handler)
app.add_exception_handler(BadRequestException, bad_request_exception_handler)
app.add_exception_handler(ValidationException, validation_exception_handler)

# 註冊路由
app.include_router(auth_router)
app.include_router(todos_router)


@app.get("/")
async def index():
    """根路徑"""
    return {
        "message": "FastAPI TO-DO List API",
        "version": "v2",
        "docs": "/docs",
        "endpoints": {
            "auth": "/api/v2/auth/*",
            "todos": "/api/v2/todos/*"
        }
    }


@app.get("/health")
async def health():
    """健康檢查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

