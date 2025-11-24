"""
FastAPI 應用程式入口 - WebSocket 實時通訊範例
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 導入 WebSocket 路由
from routers import websocket

# 建立 FastAPI 應用
app = FastAPI(
    title="Flask to FastAPI - WebSocket 實時通訊",
    description="""
## 本章學習重點

### ⭐ WebSocket 實時通訊
- ✅ **WebSocket 基礎**：從 Flask-SocketIO 遷移到 FastAPI WebSocket
- ✅ **連接管理**：ConnectionManager 管理多個連接
- ✅ **訊息廣播**：一對多訊息廣播功能
- ✅ **點對點通訊**：用戶名識別與私訊功能
- ✅ **前端整合**：簡單的 HTML 聊天室界面

### 核心概念
- WebSocket 端點定義：`@router.websocket("/ws")`
- 連接管理：使用 Set 儲存活躍連接
- 訊息格式：JSON 格式的結構化訊息
- 錯誤處理：WebSocketDisconnect 異常處理
    """,
    version="1.0.0"
)

# ========== 1. 加入中間件 ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== 2. 靜態文件服務 ==========
# 提供 HTML 文件訪問
app.mount("/static", StaticFiles(directory="static"), name="static")

# ========== 3. 註冊路由 ==========
app.include_router(websocket.router, tags=["WebSocket"])


# ========== 4. 根路徑 ==========
@app.get("/", tags=["root"])
async def read_root():
    """根路徑 - API 資訊"""
    return {
        "message": "Flask to FastAPI - WebSocket Real-time Communication",
        "docs": "/docs",
        "endpoints": {
            "websocket_basic": "ws://localhost:8000/ws",
            "websocket_chat": "ws://localhost:8000/ws/chat",
            "websocket_chat_with_username": "ws://localhost:8000/ws/chat/{username}",
            "status": "/ws/status"
        },
        "frontend": {
            "chat_page": "/static/chat.html"
        },
        "topics": [
            "WebSocket connection management",
            "Real-time message broadcasting",
            "One-to-one private messaging",
            "Frontend integration"
        ]
    }


# ========== 5. 提供 HTML 頁面 ==========
@app.get("/chat", tags=["frontend"])
async def chat_page():
    """聊天室頁面"""
    return FileResponse("static/chat.html")


# ========== 6. 健康檢查端點 ==========
@app.get("/health", tags=["monitoring"])
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "websocket_support": True,
        "features": {
            "basic_websocket": "enabled",
            "chat_room": "enabled",
            "private_messaging": "enabled",
            "connection_management": "enabled"
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

