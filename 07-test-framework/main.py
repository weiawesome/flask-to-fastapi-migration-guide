"""
FastAPI 應用程式入口 - 測試框架示範
"""
import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from routers import users

# 建立 FastAPI 應用
app = FastAPI(
    title="Flask to FastAPI - 測試框架",
    description="""
## 本章學習重點

### ⭐ 測試框架與實戰
- ✅ **Flask test_client → FastAPI TestClient**：從 Flask 測試遷移到 FastAPI
- ✅ **異步測試設定**：使用 pytest-asyncio 測試異步端點
- ✅ **依賴覆寫**：在測試中覆寫依賴注入
- ✅ **Mock Service 依賴**：在測試中 Mock Service 層依賴
- ✅ **測試覆蓋率**：使用 coverage 工具自動計算
- ✅ **完整架構**：Router → Service → Repository → Memory

### 架構示例
- **Router**: `GET /users/{user_id}` - 只有一個端點
- **Service**: `UserService` - 可依賴其他 Service（便於 Mock）
- **Repository**: `UserRepository` - Memory 存儲
    """,
    version="1.0.0"
)

# CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(users.router)


@app.get("/", tags=["root"])
def read_root():
    """根路徑 - API 資訊"""
    return {
        "message": "Flask to FastAPI - Testing Framework",
        "docs": "/docs",
        "endpoint": {
            "get_user": "GET /users/{user_id}"
        }
    }


@app.get("/health", tags=["monitoring"])
def health_check():
    """健康檢查端點"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
