# 服務器部署：Gunicorn → Uvicorn/Hypercorn

## 概述

在生產環境中，Flask 應用通常使用 Gunicorn (WSGI 服務器) 來運行，而 FastAPI 作為 ASGI 應用，需要使用 ASGI 服務器（如 Uvicorn 或 Hypercorn）。本章將深入探討如何從 Gunicorn 遷移到現代化的 ASGI 服務器。

## 目錄

- [WSGI vs ASGI 服務器對比](#wsgi-vs-asgi-服務器對比)
- [Uvicorn 部署](#uvicorn-部署)
- [Hypercorn 部署](#hypercorn-部署)
- [多種部署方式對比](#多種部署方式對比)
- [效能調優](#效能調優)
- [故障排除](#故障排除)

## WSGI vs ASGI 服務器對比

### Flask + Gunicorn (WSGI)

```python
# Flask 應用
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return {'message': 'Hello World'}

# 使用 Gunicorn 啟動
# gunicorn app:app --bind 0.0.0.0:8000 --workers 4
```

**Gunicorn 特性：**
- ✅ 多進程模型（每個 worker 是獨立進程）
- ✅ 支援同步和異步 worker（gevent、eventlet）
- ✅ 成熟的穩定性
- ❌ 不原生支援 ASGI
- ❌ 每個 worker 需要獨立記憶體

### FastAPI + Uvicorn (ASGI)

```python
# FastAPI 應用
from fastapi import FastAPI
app = FastAPI()

@app.get('/')
def hello():
    return {'message': 'Hello World'}

# 使用 Uvicorn 啟動
# uvicorn main:app --host 0.0.0.0 --port 8000
```

**Uvicorn 特性：**
- ✅ 基於 uvloop 和 httptools 的高效能
- ✅ 原生支援 ASGI 和非同步
- ✅ 支援 HTTP/2 和 WebSocket
- ✅ 單進程多協程，記憶體效率高
- ✅ 快速啟動時間

### 架構差異

**WSGI (Gunicorn) 架構：**
```
請求
  ↓
Gunicorn 主進程（監聽器）
  ↓
分配給 Worker 進程（N 個獨立進程）
  ├─ Worker 1 → Flask App（同步）
  ├─ Worker 2 → Flask App（同步）
  └─ Worker N → Flask App（同步）
```

**ASGI (Uvicorn) 架構：**
```
請求
  ↓
Uvicorn（單進程事件循環）
  ↓
asyncio 事件循環
  ├─ 協程 1 → FastAPI App（異步）
  ├─ 協程 2 → FastAPI App（異步）
  ├─ 協程 3 → FastAPI App（異步）
  └─ ... （數千個協程）
```

### 效能對比

| 指標 | Gunicorn (4 workers) | Uvicorn (單進程) | 提升 |
|------|---------------------|----------------|------|
| **RPS** | ~10,000 | ~40,000+ | **4x** |
| **併發連接** | 受限於 worker 數 | 數千連接 | **10x+** |
| **記憶體使用** | ~200MB (4 workers) | ~50MB | **75% 減少** |
| **啟動時間** | ~5 秒 | ~1 秒 | **5x 更快** |
| **延遲 (P50)** | ~5ms | ~2ms | **2.5x** |

*測試環境：4 核 CPU，簡單 JSON API*

## Uvicorn 部署

### 1. 基礎部署

#### 開發環境（熱重載）

```bash
# 安裝 Uvicorn
pip install uvicorn

# 啟動應用（開發模式，自動重載）
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 生產環境（單進程）

```bash
# 生產模式啟動
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. 多進程部署（使用 Workers）

雖然 Uvicorn 是單進程異步，但在 CPU 密集型場景下，可以使用多 worker 來利用多核：

```bash
# 使用 4 個 worker（每個 worker 是獨立進程）
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**注意：** 
- 每個 worker 是獨立的 Uvicorn 進程
- 每個 worker 有自己的事件循環
- 適用於多核 CPU，但會增加記憶體使用

### 3. Uvicorn 配置文件

創建 `uvicorn.json` 配置文件：

```json
{
  "app": "main:app",
  "host": "0.0.0.0",
  "port": 8000,
  "workers": 4,
  "log_level": "info",
  "access_log": true,
  "timeout_keep_alive": 5,
  "limit_concurrency": 1000,
  "backlog": 2048
}
```

使用配置文件啟動：

```bash
uvicorn main:app --config uvicorn.json
```

### 4. Python 程式碼啟動

在 `main.py` 或單獨的啟動腳本中：

```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        log_level="info",
        access_log=True,
        reload=False  # 生產環境設為 False
    )
```

啟動：

```bash
python main.py
```

### 5. Gunicorn + Uvicorn Workers（推薦用於生產）

這是最接近傳統 Gunicorn 部署的方式，但使用 Uvicorn worker：

```bash
# 安裝 Gunicorn 和 Uvicorn
pip install gunicorn uvicorn[standard]

# 使用 Gunicorn 作為進程管理器，Uvicorn 作為 worker
gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50
```

**Gunicorn 配置檔案 `gunicorn_config.py`：**

```python
# gunicorn_config.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
preload_app = True
```

使用配置檔案：

```bash
gunicorn main:app -c gunicorn_config.py
```

**優點：**
- ✅ Gunicorn 提供進程管理和重啟機制
- ✅ 可以利用多核 CPU
- ✅ 自動重啟崩潰的 worker
- ✅ 優雅的關閉和重載

### 6. Systemd 服務配置

創建 `/etc/systemd/system/fastapi.service`：

```ini
[Unit]
Description=FastAPI Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/fastapi-app
Environment="PATH=/opt/fastapi-app/venv/bin"
ExecStart=/opt/fastapi-app/venv/bin/gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --config gunicorn_config.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

啟用服務：

```bash
sudo systemctl daemon-reload
sudo systemctl enable fastapi
sudo systemctl start fastapi
sudo systemctl status fastapi
```

## Hypercorn 部署

Hypercorn 是另一個 ASGI 服務器，相比 Uvicorn 的優勢是：

- ✅ 原生支援 HTTP/2
- ✅ 更好的 HTTP/2 Server Push
- ✅ 更進階的配置選項

### 安裝

```bash
pip install hypercorn
```

### 基礎使用

```bash
# 基礎啟動
hypercorn main:app --bind 0.0.0.0:8000

# 使用 HTTP/2
hypercorn main:app --bind 0.0.0.0:8000 --http2

# 多進程
hypercorn main:app --bind 0.0.0.0:8000 --workers 4
```

### Hypercorn 配置文件

創建 `hypercorn.toml`：

```toml
bind = ["0.0.0.0:8000"]
workers = 4
worker_class = "asyncio"
log_level = "info"
access_log = "-"
keep_alive_timeout = 5
graceful_timeout = 30
```

使用配置文件：

```bash
hypercorn main:app --config hypercorn.toml
```

### Hypercorn vs Uvicorn

| 特性 | Uvicorn | Hypercorn | 推薦 |
|------|---------|-----------|------|
| **效能** | ⭐⭐⭐⭐⭐ 極佳 | ⭐⭐⭐⭐ 優秀 | Uvicorn |
| **HTTP/2 支援** | ⚠️ 需要額外配置 | ✅ 原生支援 | Hypercorn |
| **成熟度** | ⭐⭐⭐⭐⭐ 非常成熟 | ⭐⭐⭐⭐ 成熟 | Uvicorn |
| **社群活躍度** | ⭐⭐⭐⭐⭐ 非常高 | ⭐⭐⭐ 中等 | Uvicorn |
| **配置選項** | ⭐⭐⭐⭐ 豐富 | ⭐⭐⭐⭐⭐ 更豐富 | Hypercorn |

**建議：** 
- 一般情況選擇 **Uvicorn**（更成熟、效能更好）
- 需要 HTTP/2 原生支援時選擇 **Hypercorn**

## 多種部署方式對比

### 1. Uvicorn 單進程（開發/小型專案）

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

**適用場景：**
- ✅ 開發環境
- ✅ 小型專案（< 100 併發）
- ✅ 測試環境

**優點：**
- 簡單快速
- 記憶體使用少
- 啟動快

**缺點：**
- 無法利用多核
- 單點故障風險

### 2. Uvicorn 多 Workers（中小型專案）

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**適用場景：**
- ✅ 中小型專案（100-1000 併發）
- ✅ 多核 CPU 環境
- ✅ 需要更高可用性

**優點：**
- 利用多核 CPU
- 提高併發處理能力
- 一個 worker 崩潰不影響其他

**缺點：**
- 記憶體使用增加
- 需要反向代理做負載均衡

### 3. Gunicorn + Uvicorn Workers（生產推薦）

```bash
gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

**適用場景：**
- ✅ 生產環境（推薦）
- ✅ 需要進程管理
- ✅ 需要優雅重啟

**優點：**
- Gunicorn 提供進程管理
- 自動重啟崩潰的 worker
- 優雅的關閉和重載
- 成熟的生產環境工具

**缺點：**
- 配置稍微複雜
- 需要額外依賴

### 4. Nginx + Uvicorn（生產標準）

**架構：**
```
Internet
  ↓
Nginx (反向代理 + SSL)
  ↓ (負載均衡)
Uvicorn/Gunicorn (應用服務器)
  ↓
FastAPI App
```

**Nginx 配置 `/etc/nginx/sites-available/fastapi`：**

```nginx
upstream fastapi_backend {
    # 多個 Uvicorn 實例（不同端口）
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 80;
    server_name your-domain.com;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    client_max_body_size 10M;

    location / {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支援
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超時設定
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 靜態文件
    location /static {
        alias /opt/fastapi-app/static;
    }
}
```

**啟動多個 Uvicorn 實例：**

```bash
# 使用 systemd 啟動多個實例
uvicorn main:app --host 127.0.0.1 --port 8000 &
uvicorn main:app --host 127.0.0.1 --port 8001 &
uvicorn main:app --host 127.0.0.1 --port 8002 &
uvicorn main:app --host 127.0.0.1 --port 8003 &
```

或使用 supervisor 管理多個進程。

## 效能調優

### 1. Worker 數量計算

**公式：**
```
workers = (2 × CPU cores) + 1
```

例如：4 核 CPU → 9 workers

**但對於 I/O 密集型 FastAPI 應用：**
```
workers = CPU cores (或稍多)
```

因為異步 I/O 已經很高效，不需要太多 workers。

### 2. 連接數限制

```python
# uvicorn.json
{
  "limit_concurrency": 1000,  # 最大併發連接數
  "backlog": 2048,             # TCP backlog
  "timeout_keep_alive": 5      # Keep-alive 超時
}
```

### 3. 記憶體優化

```bash
# 使用 preload_app 共享記憶體
gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --preload-app \
    --max-requests 1000 \      # 處理 1000 請求後重啟
    --max-requests-jitter 50   # 隨機 jitter 避免同時重啟
```

### 4. 日誌優化

```bash
# 使用結構化日誌
uvicorn main:app \
    --log-config logging.json \
    --access-log \
    --log-level info
```

### 5. SSL/TLS 優化

```python
# main.py
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8443,
        ssl_keyfile="/path/to/key.pem",
        ssl_certfile="/path/to/cert.pem",
        ssl_ca_certs="/path/to/ca.pem",  # 可選
        ssl_version=2  # TLS 1.2
    )
```

**建議：** 在生產環境中，使用 Nginx 處理 SSL，而不是在 Uvicorn 層面。

## 故障排除

### 問題 1: "Address already in use"

```bash
# 檢查端口占用
lsof -i :8000

# 殺死進程
kill -9 <PID>
```

### 問題 2: Worker 頻繁重啟

**可能原因：**
- 記憶體洩漏
- 請求超時
- 異常未處理

**解決方案：**
```bash
# 增加超時時間
--timeout 120

# 檢查日誌
journalctl -u fastapi -f
```

### 問題 3: 高併發下效能下降

**解決方案：**
1. 增加 workers
2. 優化資料庫連接池
3. 使用快取
4. 檢查是否存在 CPU 密集型操作阻塞事件循環

### 問題 4: WebSocket 連接失敗

**解決方案：**
確保 Nginx 配置了 WebSocket 支援（見上方 Nginx 配置）

### 問題 5: 優雅關閉失敗

**解決方案：**
```python
# 在應用中添加優雅關閉處理
import signal
import asyncio

async def shutdown():
    # 關閉資料庫連接
    # 清理資源
    pass

def signal_handler():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(shutdown())

signal.signal(signal.SIGTERM, signal_handler)
```

## 部署檢查清單

- [ ] 選擇合適的部署方式（參考決策樹）
- [ ] 配置正確的 worker 數量
- [ ] 設置反向代理（Nginx）
- [ ] 配置 SSL/TLS 證書
- [ ] 設置日誌輪轉
- [ ] 配置監控和告警
- [ ] 實現健康檢查端點
- [ ] 設置自動重啟機制
- [ ] 測試優雅關閉
- [ ] 進行負載測試

## 總結

### Flask → FastAPI 服務器遷移總結

| 項目 | Flask + Gunicorn | FastAPI + Uvicorn | 遷移難度 |
|------|-----------------|-------------------|---------|
| **啟動命令** | `gunicorn app:app` | `uvicorn main:app` | ⭐ 簡單 |
| **Worker 配置** | `--workers 4` | `--workers 4` | ⭐ 相同 |
| **配置文件** | `gunicorn_config.py` | `uvicorn.json` | ⭐⭐ 簡單 |
| **反向代理** | 相同 (Nginx) | 相同 (Nginx) | ✅ 無需改變 |
| **系統服務** | systemd | systemd | ✅ 相同 |
| **效能優化** | 多進程模型 | 異步 + 可選多進程 | ⭐⭐⭐ 中等 |

### 關鍵要點

1. ✅ **Uvicorn 是 FastAPI 的標準 ASGI 服務器**
2. ✅ **生產環境推薦使用 Gunicorn + Uvicorn Workers**
3. ✅ **異步 I/O 使得單進程也能處理高併發**
4. ✅ **Worker 數量不需要像 Gunicorn 那麼多**
5. ✅ **使用 Nginx 作為反向代理處理 SSL 和負載均衡**

## 參考資源

- [Uvicorn Documentation](https://www.uvicorn.org/)
- [Gunicorn + Uvicorn Workers](https://www.uvicorn.org/deployment/#gunicorn)
- [Hypercorn Documentation](https://hypercorn.readthedocs.io/)
- [ASGI Specification](https://asgi.readthedocs.io/)

