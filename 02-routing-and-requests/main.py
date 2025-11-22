"""
FastAPI 應用程式入口
展示 Layered Architecture 和 APIRouter 的使用
"""
import uvicorn
from fastapi import FastAPI

# 導入 routers
from routers import users

# 創建 FastAPI 應用
app = FastAPI(
    title="Flask to FastAPI - 路由與請求處理",
    description="""
## Layered Architecture 範例

展示分層架構設計：
- **Router Layer**: 處理 HTTP 請求和路由
- **Schema Layer**: Pydantic 模型驗證
- **Repository Layer**: 資料存取層（目前使用記憶體，下一步改用 SQLAlchemy）

### 學習重點
- ✅ 路徑參數、查詢參數、請求體處理
- ✅ Pydantic 自動驗證
- ✅ APIRouter 組織路由
- ✅ Repository 模式
- ✅ 簡單的依賴注入（Repository）
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 註冊路由器
app.include_router(users.router)


# 根路徑
@app.get("/", tags=["root"])
def read_root():
    """
    根路徑 - API 資訊
    """
    return {
        "message": "Flask to FastAPI - Routing and Requests Example",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "users": "/users"
        },
        "architecture": {
            "layer_1": "Routers - Handle HTTP requests",
            "layer_2": "Schemas - Pydantic validation",
            "layer_3": "Repositories - Data access (currently in-memory)",
            "note": "Next: integrate a real database with SQLAlchemy"
        }
    }


# 健康檢查端點
@app.get("/health", tags=["health"])
def health_check():
    """健康檢查端點"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
