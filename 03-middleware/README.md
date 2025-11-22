# 03 - 中間件與錯誤處理

## 本章學習重點

本章重點學習 FastAPI 的**中間件（Middleware）**和**錯誤處理（Error Handling）**，這些是建構生產級 API 的關鍵功能。

✅ **已包含的內容：**
- Flask `before_request` / `after_request` → FastAPI 中間件
- 自訂中間件（日誌、計時、請求追蹤）
- CORS 跨域設定（Flask-CORS → CORSMiddleware）
- 統一錯誤處理（類似 Flask `@app.errorhandler()`）
- 自訂例外類別
- 日誌系統整合
- 效能監控與指標收集

## 目錄
- [專案結構](#專案結構)
- [Flask vs FastAPI 中間件對比](#flask-vs-fastapi-中間件對比)
- [自訂中間件](#自訂中間件)
- [CORS 跨域設定](#cors-跨域設定)
- [錯誤處理](#錯誤處理)
- [日誌系統](#日誌系統)
- [效能監控](#效能監控)
- [啟動與測試](#啟動與測試)

## 專案結構

```
03-middleware/
├── main.py                    # 應用程式入口
├── core/                     # 核心模組（應用基礎設施）
│   ├── __init__.py
│   ├── exceptions.py            # 自訂例外
│   └── error_handlers.py        # 錯誤處理器
├── middleware/               # 中間件層
│   ├── __init__.py
│   ├── logging_middleware.py    # 日誌中間件
│   ├── timing_middleware.py     # 計時中間件
│   └── request_id_middleware.py # 請求追蹤
├── utils/                    # 共用工具
│   ├── __init__.py
│   ├── logger.py                # 日誌配置
│   └── metrics.py               # 效能指標收集
├── routers/                  # 路由層
│   └── users.py
├── schemas/                  # Pydantic 模型
│   └── user.py
├── repositories/             # 資料存取層
│   └── user_repository.py
└── README.md
```

### 為什麼這樣組織？

| 目錄/檔案 | 用途 | 理由 |
|----------|------|------|
| `core/` | 應用核心基礎設施 | 包含全域的例外定義和錯誤處理，是應用的「基礎層」 |
| `middleware/` | 請求/回應攔截邏輯 | 處理橫切關注點（logging, timing, CORS） |
| `utils/` | 可重用的工具函數 | 日誌配置、指標收集等輔助功能 |
| `routers/` | API 端點定義 | 業務邏輯的入口 |
| `schemas/` | 資料驗證模型 | Pydantic 模型定義 |
| `repositories/` | 資料存取 | 與資料儲存互動的邏輯 |

## Flask vs FastAPI 中間件對比

### Flask 的做法

```python
from flask import Flask, request, g
import time

app = Flask(__name__)

@app.before_request
def before_request():
    """請求前執行"""
    g.start_time = time.time()
    print(f"Incoming: {request.method} {request.path}")

@app.after_request
def after_request(response):
    """請求後執行"""
    duration = time.time() - g.start_time
    print(f"Response: Status {response.status_code}, Duration: {duration:.3f}s")
    response.headers['X-Process-Time'] = str(duration)
    return response

@app.errorhandler(404)
def handle_404(e):
    """處理 404 錯誤"""
    return {"error": "Not found"}, 404

@app.errorhandler(Exception)
def handle_exception(e):
    """處理所有例外"""
    return {"error": "Internal server error"}, 500
```

### FastAPI 的做法

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time

app = FastAPI()

# 1. 自訂中间件（取代 before_request 和 after_request）
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Before request
        start_time = time.time()
        print(f"Incoming: {request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # After request
        duration = time.time() - start_time
        print(f"Response: Status {response.status_code}, Duration: {duration:.3f}s")
        response.headers['X-Process-Time'] = str(duration)
        
        return response

app.add_middleware(LoggingMiddleware)

# 2. 錯誤處理器（取代 errorhandler）
@app.exception_handler(404)
async def handle_404(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found"}
    )

@app.exception_handler(Exception)
async def handle_exception(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )
```

### 核心差異

| 特性 | Flask | FastAPI |
|------|-------|---------|
| **請求前處理** | `@app.before_request` | 中間件的 `dispatch` 前半部 |
| **請求後處理** | `@app.after_request` | 中間件的 `dispatch` 後半部 |
| **錯誤處理** | `@app.errorhandler()` | `app.add_exception_handler()` |
| **中間件註冊** | ❌ 無內建中間件系統 | ✅ `app.add_middleware()` |
| **非同步支援** | ❌ 同步 | ✅ 非同步（`async def`） |
| **執行順序** | before → handler → after | 多個中間件可堆疊 |

## 自訂中間件

### 1. 日誌中間件（Logging Middleware）

記錄所有請求和回應的詳細資訊。

```python
# middleware/logging_middleware.py
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # ===== Before Request =====
        start_time = time.time()
        logger.info(f"📨 {request.method} {request.url}")
        
        # ===== Process Request =====
        response = await call_next(request)
        
        # ===== After Request =====
        duration = time.time() - start_time
        logger.info(f"📤 Status: {response.status_code}, Time: {duration:.3f}s")
        response.headers["X-Process-Time"] = str(duration)
        
        return response
```

**輸出範例：**
```
📨 GET http://localhost:8000/users/1
📤 Status: 200, Time: 0.023s
```

### 2. 計時中间件（Timing Middleware）

監控每个端点的效能。

```python
# middleware/timing_middleware.py
import time
from starlette.middleware.base import BaseHTTPMiddleware
from utils.metrics import metrics_collector

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        # 記錄到指標收集器
        metrics_collector.record_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=duration
        )
        
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        return response
```

### 3. 請求追蹤中间件（Request ID Middleware）

为每个請求生成唯一 ID，方便追蹤和除錯。

```python
# middleware/request_id_middleware.py
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar('request_id', default='')

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # 从請求头获取或生成新的 ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request_id_var.set(request_id)
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

**使用方式：**
```python
from middleware.request_id_middleware import get_request_id

def some_function():
    request_id = get_request_id()
    logger.info(f"Processing request {request_id}")
```

### 中间件注册（注意顺序！）

```python
# main.py
from fastapi import FastAPI
from middleware import LoggingMiddleware, TimingMiddleware, RequestIDMiddleware

app = FastAPI()

# 中间件执行顺序：后添加的先执行
# 实际执行：RequestID → Timing → Logging
app.add_middleware(LoggingMiddleware)    # 第一个添加，最后执行
app.add_middleware(TimingMiddleware)     # 第二个添加
app.add_middleware(RequestIDMiddleware)  # 最后添加，最先执行
```

**执行流程：**
```
Request
  → RequestIDMiddleware (before)
    → TimingMiddleware (before)
      → LoggingMiddleware (before)
        → Route Handler
      ← LoggingMiddleware (after)
    ← TimingMiddleware (after)
  ← RequestIDMiddleware (after)
← Response
```

## CORS 跨域设定

### Flask 方式（Flask-CORS）

```python
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)

# 方式 1：全局设定
CORS(app)

# 方式 2：详细设定
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

### FastAPI 方式（内建 CORSMiddleware）

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://example.com"
    ],  # 允许的来源
    allow_credentials=True,      # 允许 cookies
    allow_methods=["*"],         # 允许所有 HTTP 方法
    allow_headers=["*"],         # 允许所有請求头
    expose_headers=["X-Request-ID"]  # 暴露自訂回應头
)
```

### 对比

| 特性 | Flask-CORS | FastAPI CORSMiddleware |
|------|-----------|----------------------|
| **安装** | 需额外安装 `flask-cors` | 内建，无需安装 |
| **设定方式** | 装饰器或全局设定 | 中间件方式 |
| **效能** | 同步處理 | 异步處理 |
| **灵活性** | 可针对特定路由设定 | 全局设定 |

### 生产环境建议

```python
# ❌ 开发环境（允许所有来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 生产环境（明确指定来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend.com",
        "https://app.your-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)
```

## 錯誤處理

### 1. 自訂例外类

```python
# core/exceptions.py
from fastapi import HTTPException, status

class UserNotFoundException(HTTPException):
    """使用者不存在例外"""
    def __init__(self, user_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

class UserAlreadyExistsException(HTTPException):
    """使用者已存在例外"""
    def __init__(self, username: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User '{username}' already exists"
        )
```

**使用方式：**
```python
# routers/users.py
from core import UserNotFoundException

@router.get("/{user_id}")
def get_user(user_id: int, repo: UserRepository = Depends(get_user_repository)):
    user = repo.get_by_id(user_id)
    if not user:
        raise UserNotFoundException(user_id)  # 👈 使用自訂例外
    return user.to_dict()
```

### 2. 統一錯誤處理器

```python
# core/error_handlers.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from middleware.request_id_middleware import get_request_id
import logging

logger = logging.getLogger(__name__)

# 處理 HTTP 例外
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = get_request_id()
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail} (Request ID: {request_id})")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "status_code": exc.status_code,
                "message": exc.detail,
                "request_id": request_id
            }
        }
    )

# 處理驗證错误
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = get_request_id()
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "status_code": 422,
                "message": "Validation failed",
                "details": errors,
                "request_id": request_id
            }
        }
    )

# 處理所有未預期的例外
async def general_exception_handler(request: Request, exc: Exception):
    request_id = get_request_id()
    logger.error(
        f"Unexpected Error: {type(exc).__name__}: {str(exc)} (Request ID: {request_id})",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "status_code": 500,
                "message": "Internal server error",
                "type": type(exc).__name__,
                "request_id": request_id
            }
        }
    )
```

### 3. 注册錯誤處理器

```python
# main.py
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from core import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)

app = FastAPI()

# 注册錯誤處理器
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
```

### 错误回應范例

**404 Not Found:**
```json
{
  "error": {
    "status_code": 404,
    "message": "User with ID 999 not found",
    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
}
```

**422 Validation Error:**
```json
{
  "error": {
    "status_code": 422,
    "message": "Validation failed",
    "details": [
      {
        "field": "body -> email",
        "message": "value is not a valid email address",
        "type": "value_error.email"
      }
    ],
    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
}
```

## 日誌系統

### 統一日志配置

```python
# utils/logger.py
import logging
import sys
from pathlib import Path

def setup_logger(
    name: str = "fastapi_app",
    level: int = logging.INFO,
    log_file: str | None = None
) -> logging.Logger:
    """设定日誌系統"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 日志格式
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler（可选）
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
```

**使用方式：**
```python
# main.py
from utils import setup_logger

# 设定日志
setup_logger("fastapi_app", level=logging.INFO, log_file="logs/app.log")

# 在任何地方使用
import logging
logger = logging.getLogger("fastapi_app")
logger.info("Application started")
logger.error("An error occurred", exc_info=True)
```

## 效能監控

### 效能指標收集器

```python
# utils/metrics.py
from collections import defaultdict
import statistics

class MetricsCollector:
    """收集 API 效能指標"""
    
    def __init__(self):
        self.response_times = defaultdict(list)
        self.request_counts = defaultdict(int)
        self.status_codes = defaultdict(int)
    
    def record_request(self, method: str, path: str, status_code: int, duration: float):
        """記錄請求指標"""
        endpoint = f"{method} {path}"
        self.response_times[endpoint].append(duration)
        self.request_counts[endpoint] += 1
        self.status_codes[status_code] += 1
    
    def get_stats(self, endpoint: str | None = None):
        """获取统计資料"""
        if endpoint:
            times = self.response_times.get(endpoint, [])
            return {
                "endpoint": endpoint,
                "total_requests": self.request_counts[endpoint],
                "avg_response_time": statistics.mean(times),
                "min_response_time": min(times),
                "max_response_time": max(times),
            }
        else:
            return {
                "total_requests": sum(self.request_counts.values()),
                "endpoints": [
                    {
                        "endpoint": ep,
                        "requests": count,
                        "avg_time": statistics.mean(self.response_times[ep])
                    }
                    for ep, count in self.request_counts.items()
                ],
                "status_codes": dict(self.status_codes)
            }

metrics_collector = MetricsCollector()
```

### 監控端点

```python
# main.py
from utils import metrics_collector

@app.get("/metrics", tags=["monitoring"])
def get_metrics():
    """获取效能指標"""
    return metrics_collector.get_stats()
```

**回應范例：**
```json
{
  "total_requests": 150,
  "endpoints": [
    {
      "endpoint": "GET /users",
      "requests": 50,
      "avg_time": 0.023
    },
    {
      "endpoint": "POST /users",
      "requests": 10,
      "avg_time": 0.045
    }
  ],
  "status_codes": {
    "200": 140,
    "404": 8,
    "422": 2
  }
}
```

## 啟動与測試

### 1. 安裝依賴

```bash
cd 03-middleware
uv sync
```

### 2. 啟動应用

```bash
uv run uvicorn main:app --reload
```

### 3. 測試中间件

#### 查看日志输出

```bash
# 发送請求
curl http://localhost:8000/users

# 终端会显示：
# 📨 Incoming request: GET http://localhost:8000/users from 127.0.0.1
# 📤 Response: GET http://localhost:8000/users Status: 200 Duration: 0.023s
```

#### 检查回應头

```bash
curl -I http://localhost:8000/users

# 回應头会包含：
# X-Request-ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
# X-Process-Time: 0.023
# X-Response-Time: 0.023s
```

#### 測試錯誤處理

```bash
# 404 错误
curl http://localhost:8000/users/999

# 返回：
# {
#   "error": {
#     "status_code": 404,
#     "message": "User with ID 999 not found",
#     "request_id": "..."
#   }
# }

# 驗證错误
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"username": "ab", "email": "invalid"}'

# 返回：
# {
#   "error": {
#     "status_code": 422,
#     "message": "Validation failed",
#     "details": [...]
#   }
# }
```

#### 查看效能指標

```bash
curl http://localhost:8000/metrics

# 返回所有端点的统计資料
```

## 總結

### Flask → FastAPI 迁移检查清单

| 功能 | Flask 做法 | FastAPI 做法 | 难度 |
|------|-----------|-------------|------|
| **請求前處理** | `@app.before_request` | 中间件 `dispatch` 前半部 | ⭐⭐ 简单 |
| **請求后處理** | `@app.after_request` | 中间件 `dispatch` 后半部 | ⭐⭐ 简单 |
| **CORS 设定** | Flask-CORS 套件 | 内建 CORSMiddleware | ⭐ 简单 |
| **錯誤處理** | `@app.errorhandler()` | `add_exception_handler()` | ⭐⭐ 简单 |
| **日志記錄** | Flask 内建日志 | Python logging + 中间件 | ⭐⭐⭐ 中等 |
| **效能監控** | 需第三方工具 | 自訂中间件 + 指標收集 | ⭐⭐⭐ 中等 |

### 关键优势

**FastAPI 中间件系统的优势：**

- ✅ **統一的中间件接口**：所有中间件都用同样的方式编写
- ✅ **异步支援**：充分利用异步 I/O 提升效能
- ✅ **可堆叠**：多个中间件可以组合使用
- ✅ **Request ID 追蹤**：方便分布式系统除錯
- ✅ **統一错误格式**：所有错误都用相同格式回應
- ✅ **内建 CORS**：无需额外安装套件

### 生产环境建议

1. **日志**：
   - 使用结构化日志（JSON 格式）
   - 将日志发送到集中式日誌系統（如 ELK、Loki）
   
2. **監控**：
   - 整合 Prometheus + Grafana
   - 设定告警规则
   
3. **错误追蹤**：
   - 整合 Sentry 或 Rollbar
   - 自动回报生产环境错误
   
4. **效能**：
   - 使用 APM 工具（如 New Relic、DataDog）
   - 设定效能基准线和告警

## 参考资源

- [FastAPI - Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
- [FastAPI - CORS](https://fastapi.tiangolo.com/tutorial/cors/)
- [FastAPI - Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [Starlette - Middleware](https://www.starlette.io/middleware/)
