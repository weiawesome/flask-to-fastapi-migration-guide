"""
Async Demo Router
異步編程示範路由 - 展示 await 和 asyncio.gather 的區別
"""
import asyncio
import time
from fastapi import APIRouter

router = APIRouter()


# 模擬異步 I/O 操作
async def mock_io_operation(name: str, duration: float = 1.0):
    """
    模擬異步 I/O 操作（例如：資料庫查詢、HTTP 請求）
    
    Args:
        name: 操作名稱
        duration: 操作耗時（秒）
    
    Returns:
        dict: 操作結果
    """
    await asyncio.sleep(duration)
    return {
        "operation": name,
        "duration": duration,
        "completed_at": time.time()
    }


# ========== 1. await 順序執行 ==========

@router.get("/await-sequential")
async def await_sequential_demo():
    """
    使用 await 順序執行
    
    說明：
    - 使用 await 一個接一個執行操作
    - 等待每個操作完成後才執行下一個
    - 總時間 = 所有操作時間的總和
    """
    start_time = time.time()
    
    # 順序執行：等待第一個完成後才執行第二個
    result1 = await mock_io_operation("操作 1", 1.0)
    result2 = await mock_io_operation("操作 2", 1.0)
    result3 = await mock_io_operation("操作 3", 1.0)
    
    elapsed_time = time.time() - start_time
    
    return {
        "模式": "await 順序執行",
        "執行方式": "一個接一個執行",
        "結果": [result1, result2, result3],
        "總時間": f"{elapsed_time:.2f} 秒",
        "說明": "總時間 = 所有操作時間的總和（約 3 秒）"
    }


# ========== 2. asyncio.gather 並發執行 ==========

@router.get("/gather-concurrent")
async def gather_concurrent_demo():
    """
    使用 asyncio.gather 並發執行
    
    說明：
    - 使用 asyncio.gather 同時啟動多個操作
    - 等待所有操作完成後合併結果
    - 總時間 ≈ 最長操作的時間
    - 注意：這是協程（coroutines）並發，不是線程（threads）
    """
    start_time = time.time()
    
    # 並發執行：同時啟動多個操作
    result1, result2, result3 = await asyncio.gather(
        mock_io_operation("操作 1", 1.0),
        mock_io_operation("操作 2", 1.0),
        mock_io_operation("操作 3", 1.0)
    )
    
    elapsed_time = time.time() - start_time
    
    return {
        "模式": "asyncio.gather 並發執行",
        "執行方式": "同時啟動，等待全部完成",
        "結果": [result1, result2, result3],
        "總時間": f"{elapsed_time:.2f} 秒",
        "說明": "總時間 ≈ 最長操作的時間（約 1 秒）",
        "重要": "這是協程（coroutines）並發，不是線程（threads）"
    }


