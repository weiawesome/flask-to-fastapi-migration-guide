# WSGI vs ASGI 深度對比

## 概述

| 項目 | WSGI | ASGI |
|------|------|------|
| **全名** | Web Server Gateway Interface | Asynchronous Server Gateway Interface |
| **誕生年份** | 2003 (PEP 333) | 2016 |
| **設計目標** | Python Web 應用標準介面 | 支援異步的 Web 標準 |
| **處理模型** | 同步阻塞 | 異步非阻塞 |
| **規範文檔** | [PEP 3333](https://peps.python.org/pep-3333/) | [ASGI Specification](https://asgi.readthedocs.io/) |

## 核心差異

| 維度 | WSGI | ASGI |
|------|------|------|
| **請求處理** | 同步，一個請求阻塞一個線程 | 異步，單線程處理多個請求 |
| **I/O 模型** | 阻塞式 I/O | 非阻塞式 I/O |
| **並發模型** | 多進程 / 多線程 | 事件循環 (Event Loop) |
| **Python 版本** | Python 2.x+ | Python 3.5+ (需 async/await) |
| **向後相容** | - | ✅ 可包裝 WSGI 應用 |

## 協議支援

| 協議類型 | WSGI | ASGI |
|---------|------|------|
| **HTTP/1.0** | ✅ | ✅ |
| **HTTP/1.1** | ✅ | ✅ |
| **HTTP/2** | ❌ | ✅ |
| **HTTP/3** | ❌ | ✅ (部分伺服器) |
| **WebSocket** | ❌ | ✅ |
| **Server-Sent Events** | ⚠️ 困難 | ✅ |
| **長連接** | ⚠️ 資源消耗大 | ✅ 高效 |

## 效能比較

| 指標 | WSGI (Flask + Gunicorn) | ASGI (FastAPI + Uvicorn) | 差異 |
|------|------------------------|-------------------------|------|
| **簡單請求 (無 I/O)** | ~10,000 RPS | ~40,000 RPS | 🔥 **4x** |
| **資料庫查詢** | ~1,000 RPS | ~8,000 RPS | 🔥 **8x** |
| **外部 API 呼叫** | ~500 RPS | ~5,000 RPS | 🔥 **10x** |
| **WebSocket 連接數** | 受限 (~100) | 支援數萬 | 🔥 **100x+** |
| **記憶體使用 (1000 並發)** | ~500 MB | ~100 MB | 💾 **5x 更少** |
| **CPU 使用率** | 低 (I/O 等待) | 高 (充分利用) | ⚡ 更高效 |

*測試環境：Python 3.11, 4 核 CPU, 8GB RAM*

## 框架生態系統

### WSGI 框架

| 框架 | 年份 | 特色 | GitHub Stars |
|------|------|------|-------------|
| **Flask** | 2010 | 微框架，簡單靈活 | ~67K |
| **Django** | 2005 | 全功能框架 | ~78K |
| **Pyramid** | 2010 | 彈性配置 | ~3.9K |
| **Bottle** | 2009 | 極簡單檔 | ~8.3K |

### ASGI 框架

| 框架 | 年份 | 特色 | GitHub Stars |
|------|------|------|-------------|
| **FastAPI** | 2018 | 現代、高效能、自動文檔 | ~73K |
| **Starlette** | 2018 | 輕量異步框架 | ~9.8K |
| **Django (3.0+)** | 2019 | 異步支援 | ~78K |
| **Quart** | 2017 | Flask 異步版本 | ~2.7K |
| **Sanic** | 2016 | 高速異步框架 | ~18K |

## 伺服器對應

### WSGI 伺服器

| 伺服器 | 特色 | 適用場景 | 效能 |
|--------|------|----------|------|
| **Gunicorn** | 穩定成熟、易用 | 生產環境首選 | ⭐⭐⭐ |
| **uWSGI** | 功能豐富、高度配置 | 複雜需求 | ⭐⭐⭐⭐ |
| **mod_wsgi** | Apache 整合 | 傳統 Apache 環境 | ⭐⭐ |
| **Waitress** | 跨平台、純 Python | Windows 環境 | ⭐⭐ |

### ASGI 伺服器

| 伺服器 | 特色 | 適用場景 | 效能 |
|--------|------|----------|------|
| **Uvicorn** | 極快、基於 uvloop | FastAPI 官方推薦 | ⭐⭐⭐⭐⭐ |
| **Hypercorn** | HTTP/2、HTTP/3 支援 | 需要最新協議 | ⭐⭐⭐⭐ |
| **Daphne** | Django Channels 開發 | Django 異步應用 | ⭐⭐⭐ |

## 程式碼對比

### 應用介面

#### WSGI 應用
```python
def application(environ, start_response):
    """
    environ: 請求環境變數 (dict)
    start_response: 回應開始的 callback
    返回: 可迭代的 bytes
    """
    status = '200 OK'
    headers = [('Content-Type', 'application/json')]
    start_response(status, headers)
    return [b'{"message": "Hello WSGI"}']
```

#### ASGI 應用
```python
async def application(scope, receive, send):
    """
    scope: 連接資訊 (dict)
    receive: 接收訊息的 async callable
    send: 發送訊息的 async callable
    """
    await send({
        'type': 'http.response.start',
        'status': 200,
        'headers': [[b'content-type', b'application/json']],
    })
    await send({
        'type': 'http.response.body',
        'body': b'{"message": "Hello ASGI"}',
    })
```

### 框架層級對比

#### Flask (WSGI)
```python
from flask import Flask
import time

app = Flask(__name__)

@app.route('/slow')
def slow_operation():
    # 阻塞操作：線程等待 2 秒
    time.sleep(2)
    return {"status": "done"}

# 1000 並發需要 1000 個線程
```

#### FastAPI (ASGI)
```python
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.get('/slow')
async def slow_operation():
    # 非阻塞：釋放事件循環
    await asyncio.sleep(2)
    return {"status": "done"}

# 單線程處理 1000 並發
```

## 運作原理圖解

### WSGI 處理流程

```
客戶端請求 → Web Server (Nginx) → WSGI Server (Gunicorn)
                                           ↓
                              ┌────────────┴───────────┐
                              │  Worker Process 1     │ (阻塞)
                              │  Worker Process 2     │ (阻塞)
                              │  Worker Process 3     │ (阻塞)
                              │  Worker Process 4     │ (阻塞)
                              └───────────────────────┘
                                     ↓
                              Flask Application
```

**特點**：
- 🔴 每個 Worker 同時只能處理一個請求
- 🔴 I/O 等待時，Worker 閒置
- 🔴 擴展需要增加 Worker 數量

### ASGI 處理流程

```
客戶端請求 → Web Server (Nginx) → ASGI Server (Uvicorn)
                                           ↓
                              ┌────────────┴───────────┐
                              │   Event Loop (單線程)   │
                              │   ┌─────────────────┐  │
                              │   │ 請求 1 (等待)   │  │
                              │   │ 請求 2 (處理中) │  │
                              │   │ 請求 3 (等待)   │  │
                              │   │ 請求 4 (處理中) │  │
                              │   └─────────────────┘  │
                              └───────────────────────┘
                                     ↓
                              FastAPI Application
```

**特點**：
- ✅ 單線程並發處理多個請求
- ✅ I/O 等待時處理其他請求
- ✅ 充分利用 CPU 資源

## 資源消耗對比

### 處理 10,000 個並發連接

| 資源類型 | WSGI (多線程) | ASGI (事件循環) | 差異 |
|---------|--------------|----------------|------|
| **線程/進程數** | 10,000 | 1 | 🔥 **10000x** |
| **記憶體使用** | ~5 GB | ~100 MB | 💾 **50x** |
| **上下文切換** | 頻繁 (高開銷) | 極少 | ⚡ **極少開銷** |
| **建立連接時間** | ~100ms | ~1ms | ⏱️ **100x** |
| **維護成本** | 高 | 低 | 💰 省成本 |

## 適用場景分析

### WSGI 適合的場景

| 場景 | 原因 | 優先級 |
|------|------|--------|
| **傳統 Web 應用** | 模板渲染、同步邏輯 | ⭐⭐⭐⭐⭐ |
| **低並發應用** | < 100 並發，無效能瓶頸 | ⭐⭐⭐⭐ |
| **簡單 CRUD** | 不需要複雜異步處理 | ⭐⭐⭐⭐ |
| **舊有專案維護** | 無遷移需求 | ⭐⭐⭐ |
| **快速原型** | 學習曲線平緩 | ⭐⭐⭐⭐ |

### ASGI 適合的場景

| 場景 | 原因 | 優先級 |
|------|------|--------|
| **RESTful API** | 高並發、需要文檔 | ⭐⭐⭐⭐⭐ |
| **微服務架構** | 輕量、高效能 | ⭐⭐⭐⭐⭐ |
| **實時應用** | WebSocket 原生支援 | ⭐⭐⭐⭐⭐ |
| **高並發系統** | > 1000 並發 | ⭐⭐⭐⭐⭐ |
| **IoT / 流式資料** | 長連接、持續推送 | ⭐⭐⭐⭐⭐ |
| **機器學習 API** | 封裝 ML 模型為服務 | ⭐⭐⭐⭐ |

## 遷移考量

### 從 WSGI 遷移到 ASGI 需要注意

| 項目 | WSGI 方式 | ASGI 方式 | 遷移難度 |
|------|----------|----------|---------|
| **函數定義** | `def view()` | `async def view()` | ⭐ 簡單 |
| **資料庫** | psycopg2, PyMySQL | asyncpg, aiomysql | ⭐⭐⭐ 中等 |
| **HTTP 請求** | requests | httpx, aiohttp | ⭐⭐ 簡單 |
| **Redis** | redis-py | aioredis | ⭐⭐ 簡單 |
| **檔案操作** | open() | aiofiles | ⭐⭐ 簡單 |
| **測試** | 同步測試 | 異步測試 | ⭐⭐⭐ 中等 |
| **思維模式** | 同步思維 | 異步思維 | ⭐⭐⭐⭐ 困難 |

### 不建議遷移的情況

| 情況 | 理由 |
|------|------|
| **CPU 密集型應用** | 異步對 CPU 密集無幫助 |
| **同步資料庫為主** | 無異步驅動支援 |
| **大量同步第三方庫** | 遷移成本過高 |
| **團隊不熟悉異步** | 學習成本高，可能引入 bug |
| **低並發 (<100)** | 收益不明顯 |

## 混合部署策略

### 漸進式遷移

| 階段 | 策略 | WSGI 佔比 | ASGI 佔比 |
|------|------|-----------|-----------|
| **階段 1** | 新 API 用 ASGI | 90% | 10% |
| **階段 2** | 高並發端點遷移 | 70% | 30% |
| **階段 3** | 主要功能遷移 | 40% | 60% |
| **階段 4** | 全面遷移 | 10% | 90% |
| **完成** | 保留舊系統作為後備 | 0-5% | 95-100% |

### 共存架構

```
                    ┌─────────────┐
                    │   Nginx     │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              ↓                         ↓
    ┌─────────────────┐      ┌──────────────────┐
    │  Flask (WSGI)   │      │ FastAPI (ASGI)   │
    │  + Gunicorn     │      │ + Uvicorn        │
    │                 │      │                  │
    │ /admin          │      │ /api/v2/*        │
    │ /legacy/*       │      │ /ws/*            │
    └─────────────────┘      └──────────────────┘
```

## 未來趨勢

| 技術方向 | WSGI | ASGI | 說明 |
|---------|------|------|------|
| **新框架採用** | ❌ 減少 | ✅ 增加 | 新框架多選 ASGI |
| **社群活躍度** | 🔄 穩定 | 📈 增長 | ASGI 快速發展 |
| **協議支援** | 🔒 不變 | 🚀 持續擴展 | HTTP/3, QUIC 等 |
| **效能優化** | 🔒 已成熟 | 📈 持續提升 | 異步生態完善 |
| **企業採用** | 🔄 維持 | 📈 增加 | 大型企業開始採用 |

## 總結建議

### ✅ 建議使用 ASGI (FastAPI) 的情況

- 🎯 開發新的 API 專案
- 🚀 需要高並發處理能力
- 🔌 需要 WebSocket 或實時功能
- 📊 重視效能和資源使用
- 📚 需要自動 API 文檔
- 🌐 微服務架構
- 🤖 機器學習模型服務化

### ⚠️ 可以繼續使用 WSGI (Flask) 的情況

- 🖥️ 傳統 Web 應用（模板渲染）
- 📊 低並發場景（< 100 並發）
- 🔧 現有專案運作良好
- 👥 團隊不熟悉異步編程
- ⏰ 沒有時間進行技術遷移
- 🔌 依賴大量 Flask 特定擴展

---

## 參考資源

- [PEP 3333 - Python Web Server Gateway Interface v1.0.1](https://peps.python.org/pep-3333/)
- [ASGI Specification](https://asgi.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Uvicorn Documentation](https://www.uvicorn.org/)
- [Python async/await Tutorial](https://realpython.com/async-io-python/)

