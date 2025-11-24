"""
WebSocket 路由處理器 - 實時聊天室範例
"""
import json
import asyncio
import time
from typing import Set, Dict
from datetime import datetime, timedelta
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter

router = APIRouter()

# ========== 連接管理 ==========
class ConnectionManager:
    """
    WebSocket 連接管理器
    負責管理所有活躍的 WebSocket 連接，並提供廣播功能
    """
    
    def __init__(self, heartbeat_timeout: int = 30):
        # 使用 Set 儲存所有活躍的連接
        # 每個連接都有一個唯一的 WebSocket 物件
        self.active_connections: Set[WebSocket] = set()
        # 儲存用戶名與連接的對應關係
        self.user_connections: Dict[str, WebSocket] = {}
        # 儲存每個連接的最後活動時間（用於心跳檢測）
        self.last_activity: Dict[WebSocket, datetime] = {}
        # 心跳超時時間（秒）
        self.heartbeat_timeout = heartbeat_timeout
        # 儲存每個連接對應的用戶名（反向查找）
        self.connection_to_username: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, username: str = None):
        """
        接受新的 WebSocket 連接
        
        Args:
            websocket: WebSocket 連接物件
            username: 可選的用戶名
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        # 記錄連接時間
        self.last_activity[websocket] = datetime.now()
        
        if username:
            self.user_connections[username] = websocket
            self.connection_to_username[websocket] = username
        
        return len(self.active_connections)
    
    def disconnect(self, websocket: WebSocket, username: str = None):
        """
        移除 WebSocket 連接
        
        Args:
            websocket: WebSocket 連接物件
            username: 可選的用戶名
        """
        self.active_connections.discard(websocket)
        
        # 清理活動時間記錄
        if websocket in self.last_activity:
            del self.last_activity[websocket]
        
        # 清理用戶名映射
        if websocket in self.connection_to_username:
            username = self.connection_to_username[websocket]
            if username in self.user_connections:
                del self.user_connections[username]
            del self.connection_to_username[websocket]
        elif username and username in self.user_connections:
            del self.user_connections[username]
    
    def update_activity(self, websocket: WebSocket):
        """
        更新連接的最後活動時間（用於心跳檢測）
        
        Args:
            websocket: WebSocket 連接物件
        """
        if websocket in self.active_connections:
            self.last_activity[websocket] = datetime.now()
    
    async def send_ping(self, websocket: WebSocket):
        """
        發送 Ping 訊息（用於心跳檢測）
        
        Args:
            websocket: WebSocket 連接物件
        """
        try:
            # 使用 WebSocket 的 ping 方法（如果支援）
            # 注意：FastAPI 的 WebSocket 可能不支援原生 ping，所以使用文字訊息
            ping_message = json.dumps({
                "type": "ping",
                "timestamp": datetime.now().isoformat()
            })
            await websocket.send_text(ping_message)
        except Exception as e:
            # 如果發送失敗，標記為斷線
            self.disconnect(websocket)
    
    async def check_heartbeat(self):
        """
        檢查所有連接的心跳狀態，清理超時的連接
        這個方法應該在背景任務中定期調用
        """
        now = datetime.now()
        timeout_connections = []
        
        for websocket, last_time in self.last_activity.items():
            if (now - last_time).total_seconds() > self.heartbeat_timeout:
                timeout_connections.append(websocket)
        
        # 清理超時的連接
        for websocket in timeout_connections:
            username = self.connection_to_username.get(websocket)
            self.disconnect(websocket, username)
        
        return len(timeout_connections)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """
        發送個人訊息（點對點）
        
        Args:
            message: 要發送的訊息
            websocket: 目標 WebSocket 連接
        """
        await websocket.send_text(message)
    
    async def broadcast(self, message: str, exclude: WebSocket = None):
        """
        廣播訊息給所有連接的客戶端
        
        Args:
            message: 要廣播的訊息
            exclude: 要排除的連接（通常是發送者自己）
        """
        # 遍歷所有活躍連接並發送訊息
        disconnected = []
        for connection in self.active_connections:
            try:
                if connection != exclude:
                    await connection.send_text(message)
            except Exception as e:
                # 如果發送失敗，標記為斷線
                disconnected.append(connection)
        
        # 清理斷線的連接
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_to_user(self, message: str, username: str):
        """
        發送訊息給特定用戶
        
        Args:
            message: 要發送的訊息
            username: 目標用戶名
        """
        if username in self.user_connections:
            try:
                await self.user_connections[username].send_text(message)
            except Exception as e:
                # 如果發送失敗，移除該連接
                self.disconnect(self.user_connections[username], username)
    
    def get_connected_count(self) -> int:
        """獲取當前連接數量"""
        return len(self.active_connections)
    
    def get_connected_users(self) -> list:
        """獲取已連接的用戶名列表"""
        return list(self.user_connections.keys())


# 建立全局連接管理器實例
manager = ConnectionManager()


# ========== WebSocket 端點 ==========

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    基礎 WebSocket 端點
    處理單一連接的訊息收發
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # 接收客戶端發送的訊息
            data = await websocket.receive_text()
            
            # 回傳確認訊息
            await manager.send_personal_message(
                f"Server received: {data}",
                websocket
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    聊天室 WebSocket 端點
    支援多用戶實時聊天，包含：
    - 用戶加入/離開通知
    - 訊息廣播
    - 連接管理
    """
    # 接受連接
    await manager.connect(websocket)
    
    # 發送歡迎訊息
    welcome_message = json.dumps({
        "type": "system",
        "message": "歡迎加入聊天室！",
        "connected_count": manager.get_connected_count()
    })
    await manager.send_personal_message(welcome_message, websocket)
    
    # 通知其他用戶有新用戶加入
    join_message = json.dumps({
        "type": "system",
        "message": "有新用戶加入聊天室",
        "connected_count": manager.get_connected_count()
    })
    await manager.broadcast(join_message, exclude=websocket)
    
    try:
        while True:
            # 接收客戶端發送的訊息
            data = await websocket.receive_text()
            
            try:
                # 解析 JSON 訊息
                message_data = json.loads(data)
                message_type = message_data.get("type", "message")
                username = message_data.get("username", "Anonymous")
                message = message_data.get("message", "")
                
                # 構建要廣播的訊息
                broadcast_data = {
                    "type": message_type,
                    "username": username,
                    "message": message,
                    "timestamp": message_data.get("timestamp")
                }
                
                # 廣播給所有連接的客戶端（包括發送者自己）
                await manager.broadcast(
                    json.dumps(broadcast_data),
                    exclude=None  # 不排除任何人，所有人都能收到
                )
                
            except json.JSONDecodeError:
                # 如果不是 JSON 格式，當作純文字處理
                error_message = json.dumps({
                    "type": "error",
                    "message": "Invalid message format"
                })
                await manager.send_personal_message(error_message, websocket)
                
    except WebSocketDisconnect:
        # 用戶斷線時，通知其他用戶
        manager.disconnect(websocket)
        leave_message = json.dumps({
            "type": "system",
            "message": "有用戶離開聊天室",
            "connected_count": manager.get_connected_count()
        })
        await manager.broadcast(leave_message)


@router.websocket("/ws/chat/{username}")
async def websocket_chat_with_username(websocket: WebSocket, username: str):
    """
    帶用戶名的聊天室 WebSocket 端點
    支援用戶名識別和點對點訊息
    
    Args:
        websocket: WebSocket 連接
        username: 路徑參數，用戶名
    """
    # 接受連接並註冊用戶名
    await manager.connect(websocket, username)
    
    # 發送歡迎訊息
    welcome_message = json.dumps({
        "type": "system",
        "message": f"歡迎 {username} 加入聊天室！",
        "username": username,
        "connected_count": manager.get_connected_count(),
        "connected_users": manager.get_connected_users()
    })
    await manager.send_personal_message(welcome_message, websocket)
    
    # 通知其他用戶有新用戶加入
    join_message = json.dumps({
        "type": "system",
        "message": f"{username} 加入了聊天室",
        "username": username,
        "connected_count": manager.get_connected_count()
    })
    await manager.broadcast(join_message, exclude=websocket)
    
    try:
        while True:
            # 接收客戶端發送的訊息
            data = await websocket.receive_text()
            
            try:
                # 解析 JSON 訊息
                message_data = json.loads(data)
                message_type = message_data.get("type", "message")
                target_user = message_data.get("target_user")  # 可選的目標用戶
                message = message_data.get("message", "")
                
                # 如果有目標用戶，發送點對點訊息
                if target_user and target_user in manager.user_connections:
                    private_message = json.dumps({
                        "type": "private",
                        "from": username,
                        "message": message,
                        "timestamp": message_data.get("timestamp")
                    })
                    await manager.send_to_user(private_message, target_user)
                    
                    # 發送確認給發送者
                    confirmation = json.dumps({
                        "type": "confirmation",
                        "message": f"私訊已發送給 {target_user}",
                        "timestamp": message_data.get("timestamp")
                    })
                    await manager.send_personal_message(confirmation, websocket)
                else:
                    # 否則廣播給所有人（包括發送者自己）
                    broadcast_data = {
                        "type": message_type,
                        "username": username,
                        "message": message,
                        "timestamp": message_data.get("timestamp")
                    }
                    await manager.broadcast(
                        json.dumps(broadcast_data),
                        exclude=None  # 不排除任何人，所有人都能收到
                    )
                    
            except json.JSONDecodeError:
                # 如果不是 JSON 格式，當作純文字處理
                error_message = json.dumps({
                    "type": "error",
                    "message": "Invalid message format"
                })
                await manager.send_personal_message(error_message, websocket)
                
    except WebSocketDisconnect:
        # 用戶斷線時，通知其他用戶
        manager.disconnect(websocket, username)
        leave_message = json.dumps({
            "type": "system",
            "message": f"{username} 離開了聊天室",
            "connected_count": manager.get_connected_count()
        })
        await manager.broadcast(leave_message)


# ========== 帶心跳檢測的 WebSocket 端點 ==========

@router.websocket("/ws/chat/{username}/heartbeat")
async def websocket_chat_with_heartbeat(websocket: WebSocket, username: str):
    """
    帶心跳檢測的聊天室 WebSocket 端點
    實現了兩種心跳機制：
    1. 服務器定期發送 ping，客戶端回覆 pong
    2. 客戶端定期發送 heartbeat 訊息
    
    Args:
        websocket: WebSocket 連接
        username: 路徑參數，用戶名
    """
    await manager.connect(websocket, username)
    
    # 發送歡迎訊息
    welcome_message = json.dumps({
        "type": "system",
        "message": f"歡迎 {username} 加入聊天室（已啟用心跳檢測）！",
        "username": username,
        "connected_count": manager.get_connected_count(),
        "heartbeat_interval": 10  # 心跳間隔（秒）
    })
    await manager.send_personal_message(welcome_message, websocket)
    
    # 通知其他用戶
    join_message = json.dumps({
        "type": "system",
        "message": f"{username} 加入了聊天室",
        "username": username,
        "connected_count": manager.get_connected_count()
    })
    await manager.broadcast(join_message, exclude=websocket)
    
    # 啟動心跳任務
    heartbeat_task = asyncio.create_task(
        heartbeat_sender(websocket, username, interval=10)
    )
    
    try:
        while True:
            # 使用 asyncio.wait_for 設置接收超時
            try:
                # 設置 30 秒超時，如果沒有收到任何訊息則超時
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                # 更新活動時間
                manager.update_activity(websocket)
                
                try:
                    message_data = json.loads(data)
                    message_type = message_data.get("type", "message")
                    
                    # 處理心跳回應
                    if message_type == "pong":
                        # 客戶端回應了 ping
                        continue
                    elif message_type == "heartbeat":
                        # 客戶端主動發送心跳
                        # 回覆確認
                        heartbeat_response = json.dumps({
                            "type": "heartbeat_ack",
                            "timestamp": datetime.now().isoformat()
                        })
                        await manager.send_personal_message(heartbeat_response, websocket)
                        continue
                    
                    # 處理普通訊息
                    target_user = message_data.get("target_user")
                    message = message_data.get("message", "")
                    
                    # 使用路徑參數中的用戶名（更可靠）
                    message_username = message_data.get("username", username)
                    
                    if target_user and target_user in manager.user_connections:
                        # 私訊
                        private_message = json.dumps({
                            "type": "private",
                            "from": username,  # 使用路徑參數中的用戶名
                            "message": message,
                            "timestamp": message_data.get("timestamp")
                        })
                        await manager.send_to_user(private_message, target_user)
                    else:
                        # 廣播給所有人（包括發送者自己）
                        # 使用路徑參數中的用戶名，確保一致性
                        broadcast_data = {
                            "type": message_type,
                            "username": username,  # 使用路徑參數中的用戶名
                            "message": message,
                            "timestamp": message_data.get("timestamp")
                        }
                        await manager.broadcast(
                            json.dumps(broadcast_data),
                            exclude=None  # 不排除任何人，所有人都能收到
                        )
                        
                except json.JSONDecodeError:
                    error_message = json.dumps({
                        "type": "error",
                        "message": "Invalid message format"
                    })
                    await manager.send_personal_message(error_message, websocket)
                    
            except asyncio.TimeoutError:
                # 超時：檢查連接是否還活躍
                # 如果超過心跳超時時間沒有活動，關閉連接
                if websocket in manager.last_activity:
                    last_activity = manager.last_activity[websocket]
                    if (datetime.now() - last_activity).total_seconds() > manager.heartbeat_timeout:
                        # 連接超時，關閉
                        break
                # 否則繼續等待
                continue
                
    except WebSocketDisconnect:
        pass
    finally:
        # 取消心跳任務
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
        
        # 清理連接
        manager.disconnect(websocket, username)
        leave_message = json.dumps({
            "type": "system",
            "message": f"{username} 離開了聊天室",
            "connected_count": manager.get_connected_count()
        })
        await manager.broadcast(leave_message)


async def heartbeat_sender(websocket: WebSocket, username: str, interval: int = 10):
    """
    心跳發送器（背景任務）
    定期向客戶端發送 ping 訊息
    
    Args:
        websocket: WebSocket 連接
        username: 用戶名
        interval: 心跳間隔（秒）
    """
    try:
        while True:
            await asyncio.sleep(interval)
            
            # 檢查連接是否還活躍
            if websocket not in manager.active_connections:
                break
            
            # 發送 ping
            await manager.send_ping(websocket)
            
    except asyncio.CancelledError:
        pass
    except Exception as e:
        # 如果發送失敗，連接可能已斷開
        manager.disconnect(websocket, username)


# ========== HTTP 端點（用於查詢連接狀態） ==========

@router.get("/ws/status")
async def get_websocket_status():
    """
    獲取 WebSocket 連接狀態
    """
    # 計算每個連接的活動時間
    connection_status = []
    now = datetime.now()
    
    for websocket, last_time in manager.last_activity.items():
        username = manager.connection_to_username.get(websocket, "Unknown")
        idle_time = (now - last_time).total_seconds()
        connection_status.append({
            "username": username,
            "last_activity": last_time.isoformat(),
            "idle_seconds": round(idle_time, 2)
        })
    
    return {
        "connected_count": manager.get_connected_count(),
        "connected_users": manager.get_connected_users(),
        "heartbeat_timeout": manager.heartbeat_timeout,
        "connections": connection_status,
        "status": "active"
    }

