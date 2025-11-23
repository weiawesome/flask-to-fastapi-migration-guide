# 06 - 異步編程實戰

## 本章學習重點

本章重點學習 **異步編程 (Async/Await)**，這是 FastAPI 的核心優勢之一。我們將深入理解異步編程的概念、使用場景，並實戰演練各種異步操作。

✅ **已包含的內容：**
- async/await 基礎概念與語法
- `await` 順序執行 vs `asyncio.gather` 並發執行對比
- 何時該用異步、何時不該用（重要！）
- 背景任務（FastAPI BackgroundTasks 與 Celery）

## 目錄

- [專案結構](#專案結構)
- [異步編程基礎概念](#異步編程基礎概念)
- [三種異步模式對比](#三種異步模式對比)
- [何時該用異步、何時不該用](#何時該用異步何時不該用)
- [背景任務](#背景任務)
- [使用方式](#使用方式)
- [常見問題](#常見問題)

## 專案結構

```
06-async-function/
├── main.py                    # 應用程式入口
├── celery_app.py              # Celery 配置（可選）
├── env.example                 # 環境變數範例
├── build/docker/              # Docker 配置
│   ├── docker-compose.yaml    # Redis Docker Compose
│   └── README.md              # Docker 使用說明
├── core/                      # 核心模組
│   ├── __init__.py
│   ├── exceptions.py
│   └── error_handlers.py
├── utils/                     # 工具模組
│   ├── __init__.py
│   └── logger.py
├── routers/                   # 路由層
│   ├── __init__.py
│   ├── async_demo.py          # await vs asyncio.gather 對比 ⭐
│   └── background_tasks.py    # 背景任務示範 ⭐
└── README.md
```

## 異步編程基礎概念

### 什麼是異步編程？

異步編程是一種**非阻塞的編程模式**，允許程式在等待 I/O 操作（如資料庫查詢、HTTP 請求）時，繼續處理其他任務。

### 三種異步模式對比

在 FastAPI 中，有三種主要的異步處理方式，理解它們的區別非常重要：

#### 1. `await` - 等待後執行（順序執行）

```python
# 模式 1：使用 await 順序執行
async def sequential_example():
    # 等待第一個操作完成後，才執行第二個
    result1 = await database_query()    # 等待 1 秒
    result2 = await http_request()      # 等待 1 秒（在 result1 完成後才開始）
    result3 = await redis_get()         # 等待 1 秒（在 result2 完成後才開始）
    # 總時間：3 秒（順序執行）
    return [result1, result2, result3]
```

**特點：**
- ✅ 等待每個操作完成後才執行下一個
- ✅ 可以根據前一個操作的結果決定下一步
- ❌ 總時間 = 所有操作時間的總和
- ❌ 適合：需要依賴前一個結果的操作

#### 2. `asyncio.gather` - 並發執行（協程並發）

```python
# 模式 2：使用 asyncio.gather 並發執行
async def concurrent_example():
    # 同時啟動多個操作，等待所有完成後合併結果
    result1, result2, result3 = await asyncio.gather(
        database_query(),    # 1 秒（同時開始）
        http_request(),      # 1 秒（同時開始）
        redis_get()         # 1 秒（同時開始）
    )
    # 總時間：約 1 秒（並發執行，等待最長的操作）
    return [result1, result2, result3]
```

**特點：**
- ✅ 同時啟動多個操作（**不是線程，是協程**）
- ✅ 總時間 ≈ 最長操作的時間
- ✅ 適合：多個獨立操作，不需要互相依賴
- ⚠️ **注意**：這是協程（coroutines）並發，不是多線程（threads）

**重要澄清：**
- `asyncio.gather` 使用的是**協程（coroutines）**，不是線程（threads）
- 協程在**同一個事件循環**中運行，由事件循環調度
- 線程是多個執行緒，需要線程切換開銷
- 協程是單線程內的並發，切換開銷更小

#### 3. Celery - 完全異步任務（立即返回）

```python
# 模式 3：使用 Celery 完全異步
@router.post("/celery/task")
async def celery_example(task_id: str):
    # 立即返回 200，任務在背景執行
    task = long_running_task.delay(task_id, duration=60)
    return {
        "status": 200,
        "message": "任務已提交",
        "task_id": task.id  # 立即返回，不等待任務完成
    }
    # 用戶立即獲得回應，任務在 Worker 中執行
```

**特點：**
- ✅ **用戶立即獲得 200 回應**，不需要等待任務完成
- ✅ 任務在獨立的 Worker 進程中執行
- ✅ 適合：長時間運行的任務（幾分鐘到幾小時）
- ✅ 支援任務狀態查詢、重試、排程
- ⚠️ 需要額外配置（Redis/RabbitMQ + Celery Worker）

### 三種模式對比表

| 特性 | `await` 順序執行 | `asyncio.gather` 並發執行 | Celery 完全異步 |
|------|-----------------|-------------------------|----------------|
| **執行方式** | 一個接一個執行 | 同時啟動，等待全部完成 | 立即返回，背景執行 |
| **總時間** | 所有操作時間總和 | ≈ 最長操作時間 | 立即返回（0 秒） |
| **用戶等待** | 需要等待所有操作 | 需要等待所有操作 | **立即獲得回應** |
| **適用場景** | 有依賴關係的操作 | 多個獨立操作 | 長時間任務 |
| **任務時長** | 短時間（< 幾秒） | 短時間（< 幾秒） | 長時間（無限制） |
| **狀態查詢** | 不需要 | 不需要 | 支援 |
| **實現方式** | 協程 | 協程（同事件循環） | 獨立進程 |

### 同步 vs 異步對比

#### 同步（阻塞）方式

```python
# 同步方式 - 順序執行，總時間 = 各操作時間之和
def sync_example():
    result1 = database_query()      # 等待 1 秒
    result2 = http_request()          # 等待 1 秒
    result3 = redis_get()             # 等待 1 秒
    # 總時間：3 秒
```

#### 異步（非阻塞）方式

```python
# 異步方式 - 並發執行，總時間 ≈ 最長操作時間
async def async_example():
    result1, result2, result3 = await asyncio.gather(
        database_query(),    # 1 秒
        http_request(),       # 1 秒
        redis_get()          # 1 秒
    )
    # 總時間：約 1 秒（並發執行）
```

### 核心語法

#### 1. 定義異步函數

```python
# 使用 async def 定義異步函數
async def my_async_function():
    # 異步操作
    await some_async_operation()
    return "完成"
```

#### 2. 等待異步操作

```python
# 使用 await 等待異步操作完成
result = await database.query()
```

#### 3. 並發執行多個異步操作

```python
# 使用 asyncio.gather() 並發執行
results = await asyncio.gather(
    task1(),
    task2(),
    task3()
)
```

#### 4. 異步上下文管理器

```python
# 使用 async with 管理異步資源
async with database.session() as session:
    result = await session.execute(query)
```

## 何時該用異步、何時不該用

### ✅ 適合使用異步的場景

#### 1. I/O 密集型操作

**資料庫操作**
```python
# ✅ 適合：資料庫查詢、插入、更新
async def get_user(db: AsyncSession):
    result = await db.execute(select(User))
    return result.scalars().all()
```

**HTTP 請求**
```python
# ✅ 適合：API 請求、爬蟲、微服務調用
async def fetch_data():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com")
        return response.json()
```

**檔案 I/O**
```python
# ✅ 適合：讀寫檔案、上傳下載
async def read_file():
    async with aiofiles.open("file.txt", "r") as f:
        content = await f.read()
        return content
```

**Redis/快取操作**
```python
# ✅ 適合：快取讀寫、計數器
async def get_cache(redis: Redis):
    value = await redis.get("key")
    return value
```

**WebSocket 連接**
```python
# ✅ 適合：即時通訊、推送通知
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # 處理 WebSocket 訊息
```

#### 2. 高並發場景

當你的應用需要同時處理**大量請求**時，異步可以大幅提升效能：

```python
# ✅ 適合：高並發 API、即時系統
@app.get("/api/data")
async def get_data():
    # 可以同時處理數千個請求
    data = await fetch_from_database()
    return data
```

#### 3. 多個 I/O 操作的組合

當你需要**同時執行多個 I/O 操作**時：

```python
# ✅ 適合：需要同時調用多個 API、查詢多個資料庫
async def aggregate_data():
    user_data, order_data, product_data = await asyncio.gather(
        get_user_data(),
        get_order_data(),
        get_product_data()
    )
    return combine(user_data, order_data, product_data)
```

### ❌ 不適合使用異步的場景

#### 1. CPU 密集型操作

**數學計算**
```python
# ❌ 不適合：CPU 密集型計算
def calculate_fibonacci(n):
    # 這會阻塞事件循環
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

# ✅ 解決方案：使用多進程（multiprocessing）
from multiprocessing import Process
process = Process(target=calculate_fibonacci, args=(30,))
process.start()
```

**圖像處理**
```python
# ❌ 不適合：圖像處理、壓縮
def process_image(image):
    # PIL、OpenCV 等操作會阻塞
    resized = image.resize((800, 600))
    return resized

# ✅ 解決方案：使用線程池或進程池
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor() as executor:
    result = executor.submit(process_image, image)
```

**資料加密/解密**
```python
# ❌ 不適合：加密運算
def encrypt_data(data):
    # 加密運算會阻塞事件循環
    return hashlib.sha256(data).hexdigest()

# ✅ 解決方案：使用線程池
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor()
result = await loop.run_in_executor(executor, encrypt_data, data)
```

#### 2. 簡單的同步操作

如果操作**非常簡單且快速**，不需要異步：

```python
# ❌ 不需要異步：簡單的資料處理
def format_data(data):
    return data.upper()  # 非常快，不需要異步

# ✅ 保持同步即可
@app.get("/format")
def format_endpoint(data: str):
    return format_data(data)
```

#### 3. 已經有同步實現且運作良好

如果現有的同步代碼**運作良好且沒有效能問題**，不需要強制改為異步：

```python
# ❌ 不需要：如果同步版本已經足夠快
def simple_query():
    return db.query(User).all()  # 已經很快了

# 除非有明確的效能問題，否則不需要改為異步
```

### 📊 決策流程圖

```
開始
  ↓
是 I/O 操作嗎？
  ├─ 是 → 需要等待嗎？
  │      ├─ 是 → ✅ 使用異步
  │      └─ 否 → 保持同步
  │
  └─ 否 → 是 CPU 密集型嗎？
         ├─ 是 → ❌ 使用多進程/線程
         └─ 否 → 保持同步
```

### 💡 實戰建議

1. **預設使用異步**：在 FastAPI 中，如果涉及 I/O 操作，預設使用異步
2. **測量效能**：如果不確定，先測量同步和異步版本的效能
3. **混合使用**：可以在異步函數中調用同步函數（使用 `run_in_executor`）
4. **避免過度使用**：不是所有函數都需要異步，簡單操作保持同步即可

## 三種異步模式總結

### 快速對比

| 模式 | 執行方式 | 用戶等待 | 總時間 | 適用場景 |
|------|---------|---------|--------|---------|
| **`await` 順序執行** | 一個接一個執行 | 需要等待所有操作 | 所有操作時間總和 | 有依賴關係的操作 |
| **`asyncio.gather` 並發執行** | 同時啟動多個協程 | 需要等待所有操作 | ≈ 最長操作時間 | 多個獨立操作 |
| **Celery 完全異步** | 立即返回 200 | **立即獲得回應** | **立即返回（0 秒）** | 長時間運行的任務 |

### 重要澄清

#### 1. `asyncio.gather` 不是多線程

```python
# ❌ 錯誤理解：asyncio.gather 開多個 thread
# ✅ 正確理解：asyncio.gather 開多個協程（coroutines）

# 協程 vs 線程：
# - 協程：在同一個事件循環中運行，由事件循環調度
# - 線程：多個執行緒，需要線程切換開銷
# - 協程切換開銷更小，更適合 I/O 密集型操作
```

#### 2. Celery 是完全異步事件

```python
# ✅ Celery 模式：用戶立即獲得 200 回應
@router.post("/task")
async def create_task():
    task = long_task.delay()  # 立即返回，不等待
    return {"task_id": task.id}  # 用戶立即獲得 200 回應
    # 任務在 Worker 中執行，用戶不需要等待
```

### 實際範例對比

#### 範例：發送郵件

```python
# 方式 1：await 順序執行（需要等待）
async def send_emails_sequential():
    await send_email("user1@example.com")  # 等待 2 秒
    await send_email("user2@example.com")  # 等待 2 秒（在 user1 完成後）
    await send_email("user3@example.com")  # 等待 2 秒（在 user2 完成後）
    # 總時間：6 秒，用戶需要等待 6 秒

# 方式 2：asyncio.gather 並發執行（需要等待）
async def send_emails_concurrent():
    await asyncio.gather(
        send_email("user1@example.com"),  # 2 秒（同時開始）
        send_email("user2@example.com"),  # 2 秒（同時開始）
        send_email("user3@example.com")   # 2 秒（同時開始）
    )
    # 總時間：約 2 秒，用戶需要等待 2 秒

# 方式 3：Celery 完全異步（立即返回）
@router.post("/send-emails")
async def send_emails_celery():
    task = send_emails_task.delay(["user1", "user2", "user3"])
    return {"task_id": task.id}  # 用戶立即獲得 200 回應（0 秒）
    # 郵件在 Worker 中發送，用戶不需要等待
```

## 背景任務

### FastAPI BackgroundTasks

#### 適用場景

- ✅ **輕量級任務**：發送郵件、清理臨時檔案、記錄日誌
- ✅ **短時間任務**：任務執行時間 < 幾分鐘
- ✅ **不需要狀態查詢**：任務執行後不需要查詢狀態
- ✅ **簡單場景**：不需要分散式、重試等功能

#### 使用方式

```python
# routers/background_tasks.py
from fastapi import BackgroundTasks

def send_email_task(email: str, message: str):
    # 同步函數，在背景執行
    print(f"發送郵件到 {email}: {message}")
    # 實際發送郵件的邏輯

@router.post("/send-email")
async def send_email(
    email: str,
    message: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(send_email_task, email, message)
    return {"message": "郵件已加入背景任務佇列"}
```

#### 異步背景任務

```python
async def async_background_task(data: str):
    # 異步函數，可以在背景執行異步操作
    await asyncio.sleep(5)
    await database.save(data)

@router.post("/async-task")
async def create_async_task(
    data: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(async_background_task, data)
    return {"message": "異步任務已加入佇列"}
```

### Celery（分散式任務佇列）

#### 適用場景

- ✅ **長時間運行的任務**：任務執行時間 > 幾分鐘
- ✅ **需要狀態查詢**：需要查詢任務執行狀態
- ✅ **需要重試機制**：任務失敗後需要重試
- ✅ **需要排程**：定時執行任務
- ✅ **分散式執行**：多個 Worker 執行任務

#### 配置 Celery

```python
# celery_app.py
from celery import Celery

celery_app = Celery(
    "fastapi_tasks",
    broker="redis://localhost:6379/0",    # 任務佇列
    backend="redis://localhost:6379/0"    # 結果儲存
)

@celery_app.task
def long_running_task(task_id: str, duration: int = 60):
    import time
    time.sleep(duration)
    return f"任務 {task_id} 已完成"
```

#### 在 FastAPI 中使用

```python
# routers/background_tasks.py
from celery_app import long_running_task

@router.post("/celery/task")
async def create_celery_task(task_id: str):
    task = long_running_task.delay(task_id, duration=60)
    return {
        "task_id": task.id,
        "status": "pending"
    }

@router.get("/celery/task/{task_id}")
async def get_celery_task_status(task_id: str):
    task = long_running_task.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }
```

#### 啟動 Celery Worker

```bash
# 啟動 Celery Worker
celery -A celery_app worker --loglevel=info

# 啟動 Celery Beat（定時任務）
celery -A celery_app beat --loglevel=info
```

### 對比總結

| 特性 | FastAPI BackgroundTasks | Celery |
|------|------------------------|--------|
| **設置複雜度** | 簡單（內建） | 複雜（需要額外配置） |
| **依賴** | 無 | Redis/RabbitMQ |
| **任務時長** | 短時間（< 幾分鐘） | 長時間（無限制） |
| **狀態查詢** | 不支援 | 支援 |
| **重試機制** | 不支援 | 支援 |
| **分散式** | 不支援 | 支援 |
| **排程** | 不支援 | 支援（Celery Beat） |
| **適用場景** | 輕量級任務 | 複雜任務 |

## 使用方式

### 1. 安裝依賴

```bash
# 使用 uv（推薦）
cd 06-async-function
uv sync

# 或使用 pip
pip install -r requirements.txt
```

### 2. 啟動應用

```bash
# 啟動 FastAPI 應用
uvicorn main:app --reload

# 或直接運行
python main.py
```

### 3. 訪問 API 文檔

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 4. 啟動 Redis（用於 Celery，可選）

```bash
# 使用 Docker Compose 啟動 Redis
docker-compose -f build/docker/docker-compose.yaml up -d

# 或使用系統安裝的 Redis
redis-server
```

### 5. 測試異步端點

```bash
# 測試 await 順序執行
curl http://localhost:8000/async/await-sequential

# 測試 asyncio.gather 並發執行
curl http://localhost:8000/async/gather-concurrent

# 測試背景任務
curl -X POST http://localhost:8000/tasks/background/simple?task_id=test123&duration=5

# 查詢背景任務狀態
curl http://localhost:8000/tasks/background/status/test123

# 測試 Celery 任務（需要啟動 Celery Worker）
curl -X POST http://localhost:8000/tasks/celery/task?task_id=celery123&duration=60
```

### 6. 啟動 Celery Worker（可選）

```bash
# 確保 Redis 已啟動
docker-compose -f build/docker/docker-compose.yaml up -d

# 啟動 Celery Worker
celery -A celery_app worker --loglevel=info

# 啟動 Celery Beat（定時任務，如果需要）
celery -A celery_app beat --loglevel=info
```

## 常見問題

### Q1: 異步函數中可以使用同步函數嗎？

**A:** 可以，但需要注意：

```python
# ❌ 錯誤：直接調用同步函數會阻塞事件循環
async def bad_example():
    time.sleep(5)  # 這會阻塞整個事件循環！

# ✅ 正確：使用 run_in_executor
async def good_example():
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, time.sleep, 5)  # 在線程池中執行
```

### Q2: `asyncio.gather` 和 `await` 有什麼區別？

**A:** 主要區別在於執行方式：

```python
# await 順序執行：一個接一個
async def sequential():
    result1 = await operation1()  # 等待完成
    result2 = await operation2()  # 等待完成
    # 總時間 = operation1 時間 + operation2 時間

# asyncio.gather 並發執行：同時啟動
async def concurrent():
    result1, result2 = await asyncio.gather(
        operation1(),  # 同時開始
        operation2()  # 同時開始
    )
    # 總時間 ≈ max(operation1 時間, operation2 時間)
```

### Q3: 如何選擇 BackgroundTasks 還是 Celery？

**A:** 根據需求選擇：

- **使用 BackgroundTasks**：簡單任務、短時間、不需要狀態查詢
- **使用 Celery**：複雜任務、長時間、需要狀態查詢、需要分散式

### Q4: 異步程式碼的錯誤處理？

**A:** 使用 try-except 處理：

```python
async def example():
    try:
        result = await some_async_operation()
        return result
    except SomeException as e:
        # 處理特定錯誤
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        # 處理其他錯誤
        logger.error(f"Unexpected error: {e}")
        raise
```

### Q5: 如何測試異步端點？

**A:** 使用 `pytest` 和 `httpx`：

```python
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_async_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/async/basic")
        assert response.status_code == 200
```

## 總結

### 關鍵要點

1. **`await` 順序執行**：適合有依賴關係的操作，總時間 = 所有操作時間總和
2. **`asyncio.gather` 並發執行**：適合獨立操作，總時間 ≈ 最長操作時間
3. **Celery 完全異步**：用戶立即獲得回應，任務在背景執行
4. **異步適合 I/O 密集型操作**：資料庫、HTTP、檔案 I/O、Redis
5. **異步不適合 CPU 密集型操作**：計算、圖像處理、加密
6. **根據任務複雜度選擇 BackgroundTasks 或 Celery**
