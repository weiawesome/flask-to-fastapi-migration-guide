"""
Celery Application Configuration
Celery 應用程式配置 - 分散式任務佇列

使用方式：
1. 啟動 Redis: redis-server
2. 啟動 Celery Worker: celery -A celery_app worker --loglevel=info
3. 在 FastAPI 中使用: from celery_app import your_task
"""
from celery import Celery
import os

# Redis 連接配置（從環境變數讀取）
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB = os.getenv("REDIS_DB", "0")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# Celery Broker 和 Backend URL（優先使用環境變數）
# 建議：Broker 和 Backend 使用不同的 Redis DB 以避免衝突
CELERY_BROKER_URL = os.getenv(
    "CELERY_BROKER_URL",
    f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"  # Broker 使用 DB 0
)
CELERY_BACKEND_URL = os.getenv(
    "CELERY_BACKEND_URL",
    f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"  # Backend 使用相同的 DB（或可以改用 DB 1）
)

# 如果有密碼，更新 URL
if REDIS_PASSWORD:
    CELERY_BROKER_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    CELERY_BACKEND_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# 創建 Celery 應用
celery_app = Celery(
    "fastapi_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BACKEND_URL
    # 任務定義在當前文件中，不需要 include
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,  # 追蹤任務開始時間
    task_time_limit=30 * 60,  # 任務超時時間（30 分鐘）
    task_soft_time_limit=25 * 60,  # 任務軟超時時間（25 分鐘）
    result_backend=CELERY_BACKEND_URL,  # 明確指定結果後端
    result_expires=3600,  # 結果過期時間（1 小時）
    result_persistent=True,  # 持久化結果
)

# 範例任務
# 重要：不要設置 ignore_result=True，否則結果不會存儲到 Backend
@celery_app.task(name="tasks.long_running_task", ignore_result=False)
def long_running_task(task_id: str, duration: int = 60):
    """
    長時間運行的任務範例
    
    Args:
        task_id: 任務 ID
        duration: 任務執行時間（秒）
    
    Returns:
        str: 任務完成訊息
    """
    import time
    time.sleep(duration)
    return f"任務 {task_id} 已完成，耗時 {duration} 秒"


@celery_app.task(name="tasks.send_email")
def send_email_task(to: str, subject: str, body: str):
    """
    發送郵件任務範例
    
    Args:
        to: 收件人
        subject: 郵件主題
        body: 郵件內容
    
    Returns:
        dict: 任務結果
    """
    # 這裡應該實際發送郵件
    # 例如使用 sendgrid, smtp 等
    import time
    time.sleep(2)  # 模擬發送郵件
    
    return {
        "status": "sent",
        "to": to,
        "subject": subject,
        "message": "郵件已發送"
    }

