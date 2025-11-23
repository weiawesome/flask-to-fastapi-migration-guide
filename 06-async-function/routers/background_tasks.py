"""
Background Tasks Router
背景任務示範路由 - Celery 實際使用範例
"""
from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult

router = APIRouter()

# 導入 Celery 任務
try:
    from celery_app import celery_app, long_running_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False


@router.post("/celery/task")
async def create_celery_task(task_id: str, duration: int = 10):
    """
    創建 Celery 任務（完全異步模式）
    
    說明：
    - 用戶立即獲得 200 回應，不需要等待任務完成
    - 任務在獨立的 Worker 進程中執行
    - 任務狀態和結果存儲在 Redis 中
    
    參數：
    - task_id: 任務 ID
    - duration: 任務執行時間（秒），預設 10 秒
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Celery 未配置，請確保已安裝 Celery 並啟動 Worker"
        )
    
    # 提交任務到 Celery
    task = long_running_task.delay(task_id, duration)
    
    return {
        "status": 200,
        "message": "任務已提交，用戶立即獲得回應",
        "task_id": task.id,
        "note": "這是完全異步模式，用戶不需要等待任務完成"
    }


@router.get("/celery/task/{task_id}")
async def get_celery_task_status(task_id: str):
    """
    查詢 Celery 任務狀態
    
    說明：
    - 從 Redis 中查詢任務狀態和結果
    - 任務狀態：PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED
    
    參數：
    - task_id: 任務 ID（從創建任務的響應中獲得）
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Celery 未配置，請確保已安裝 Celery 並啟動 Worker"
        )
    
    # 獲取任務結果
    # 重要：必須傳入 app 參數，確保使用相同的 Backend 配置從 Redis 讀取
    task_result = AsyncResult(task_id, app=celery_app)
    
    # 直接從 Backend 讀取任務狀態（不使用 get()，避免阻塞）
    # 使用 backend.get_task_meta() 直接查詢 Redis，這是最可靠的方法
    try:
        backend = celery_app.backend
        
        # 直接從 Backend 獲取任務元數據（包含狀態和結果）
        # get_task_meta() 會直接從 Redis 讀取，不會阻塞
        task_meta = backend.get_task_meta(task_id)
        
        # 從元數據中獲取狀態
        task_state = task_meta.get('status') if task_meta else None
        
        if not task_state:
            # 如果沒有元數據，任務可能不存在或還在 PENDING
            response = {
                "task_id": task_id,
                "status": "PENDING",
                "info": "任務等待執行中"
            }
        elif task_state == 'SUCCESS':
            # 任務成功完成
            response = {
                "task_id": task_id,
                "status": "SUCCESS",
                "result": task_meta.get('result')
            }
        elif task_state == 'FAILURE':
            # 任務失敗
            response = {
                "task_id": task_id,
                "status": "FAILURE",
                "error": task_meta.get('traceback') or task_meta.get('result') or "任務執行失敗"
            }
        else:
            # 任務還在執行中（STARTED, PENDING 等）
            response = {
                "task_id": task_id,
                "status": task_state,
            }
            
            # 根據狀態添加額外信息
            if task_state == "STARTED":
                response["info"] = "任務正在執行中"
            elif task_state == "PENDING":
                response["info"] = "任務等待執行中"
    except Exception as e:
        # 如果直接讀取失敗，使用 AsyncResult 作為備用
        # 但清除緩存，強制重新讀取
        task_result.forget()
        current_state = task_result.state
        
        response = {
            "task_id": task_id,
            "status": current_state or "UNKNOWN",
            "info": f"使用備用方法查詢，狀態: {current_state}"
        }
    
    return response
