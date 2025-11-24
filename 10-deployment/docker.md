# Docker 容器化

## 概述

Docker 容器化是現代應用部署的標準做法。本章將學習如何將 FastAPI 應用容器化，從 Flask 的 Docker 設置遷移到 FastAPI 的容器化部署。

## 目錄

- [Flask vs FastAPI Dockerfile 對比](#flask-vs-fastapi-dockerfile-對比)
- [基礎 Dockerfile](#基礎-dockerfile)
- [多階段構建優化](#多階段構建優化)
- [Docker Compose 配置](#docker-compose-配置)
- [生產環境優化](#生產環境優化)
- [健康檢查](#健康檢查)
- [最佳實踐](#最佳實踐)

## Flask vs FastAPI Dockerfile 對比

### Flask 傳統 Dockerfile

```dockerfile
# Flask Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "4"]
```

### FastAPI 現代 Dockerfile

```dockerfile
# FastAPI Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**主要差異：**
- ✅ FastAPI 使用 ASGI 服務器（Uvicorn）
- ✅ 端口通常改為 8000（FastAPI 默認）
- ✅ 啟動命令更簡單（不需要 worker 配置）

## 基礎 Dockerfile

### 1. 最簡單的 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴文件
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 暴露端口
EXPOSE 8000

# 啟動命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 使用非 root 用戶（安全性）

```dockerfile
FROM python:3.11-slim

# 創建非 root 用戶
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴文件
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 更改文件所有權
RUN chown -R appuser:appuser /app

# 切換到非 root 用戶
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. 開發環境 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴文件
COPY requirements.txt requirements-dev.txt ./

# 安裝依賴（包含開發依賴）
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-dev.txt

# 複製應用程式碼
COPY . .

EXPOSE 8000

# 開發模式：熱重載
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

## 多階段構建優化

多階段構建可以大幅減少最終鏡像大小，提高安全性。

### 生產環境多階段構建

```dockerfile
# 第一階段：構建階段
FROM python:3.11-slim as builder

WORKDIR /app

# 安裝構建依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴文件
COPY requirements.txt .

# 創建虛擬環境並安裝依賴
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 第二階段：運行階段
FROM python:3.11-slim

# 創建非 root 用戶
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# 從構建階段複製虛擬環境
COPY --from=builder /opt/venv /opt/venv

# 設置環境變數
ENV PATH="/opt/venv/bin:$PATH"

# 複製應用程式碼
COPY --chown=appuser:appuser . .

# 切換到非 root 用戶
USER appuser

EXPOSE 8000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**優勢：**
- ✅ 最終鏡像不包含構建工具（gcc, g++）
- ✅ 鏡像大小減少 50-70%
- ✅ 更安全（減少攻擊面）
- ✅ 構建和運行環境分離

### 優化後的版本（更小鏡像）

```dockerfile
# 第一階段：構建
FROM python:3.11-slim as builder

WORKDIR /app

# 只安裝構建時需要的依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 使用 pip 的 --user 模式安裝到用戶目錄
RUN pip install --no-cache-dir --user -r requirements.txt

# 第二階段：運行
FROM python:3.11-slim

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# 從構建階段複製 Python 包
COPY --from=builder /root/.local /home/appuser/.local

# 設置環境變數
ENV PATH=/home/appuser/.local/bin:$PATH

# 複製應用程式碼
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Docker Compose 配置

### 1. 開發環境 docker-compose.yml

```yaml
version: '3.8'

services:
  # FastAPI 應用
  api:
    build:
      context: .
      dockerfile: Dockerfile.dev
    container_name: fastapi-app
    ports:
      - "8000:8000"
    volumes:
      - .:/app  # 掛載代碼，支持熱重載
      - /app/__pycache__  # 排除緩存
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/mydb
      - REDIS_URL=redis://redis:6379
      - DEBUG=True
    depends_on:
      - db
      - redis
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  # PostgreSQL 資料庫
  db:
    image: postgres:15-alpine
    container_name: fastapi-db
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=mydb
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis 快取
  redis:
    image: redis:7-alpine
    container_name: fastapi-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

### 2. 生產環境 docker-compose.yml

```yaml
version: '3.8'

services:
  # FastAPI 應用
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: fastapi-app
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:${DB_PASSWORD}@db:5432/mydb
      - REDIS_URL=redis://redis:6379
      - ENV=production
    env_file:
      - .env.production
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - app-network

  # Nginx 反向代理
  nginx:
    image: nginx:alpine
    container_name: fastapi-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./static:/usr/share/nginx/html/static:ro
    depends_on:
      - api
    networks:
      - app-network

  # PostgreSQL 資料庫
  db:
    image: postgres:15-alpine
    container_name: fastapi-db
    restart: unless-stopped
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=mydb
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network

  # Redis 快取
  redis:
    image: redis:7-alpine
    container_name: fastapi-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

### 3. Nginx 配置文件

`nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream fastapi_backend {
        server api:8000;
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

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

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
            alias /usr/share/nginx/html/static;
        }
    }
}
```

## 生產環境優化

### 1. 使用 .dockerignore

`.dockerignore`:

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv
pip-log.txt
pip-delete-this-directory.txt
.git
.gitignore
README.md
.env
.env.*
*.md
.pytest_cache
.coverage
htmlcov/
.DS_Store
*.log
logs/
```

### 2. 優化構建緩存

```dockerfile
# 先複製 requirements.txt（變化較少）
COPY requirements.txt .

# 安裝依賴（會被緩存）
RUN pip install --no-cache-dir -r requirements.txt

# 最後複製代碼（變化較多）
COPY . .
```

### 3. 使用特定版本的基礎鏡像

```dockerfile
# 使用特定版本，不要使用 latest
FROM python:3.11.5-slim

# 或使用 SHA 摘要（最安全）
FROM python:3.11.5-slim@sha256:abc123...
```

### 4. 設置資源限制

`docker-compose.yml`:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 5. 日誌管理

```yaml
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 健康檢查

### 1. 在 FastAPI 中實現健康檢查端點

```python
# main.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "healthy"}

@app.get("/health/live")
async def liveness():
    """Liveness 探針：檢查應用是否運行"""
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness():
    """Readiness 探針：檢查應用是否準備好接收請求"""
    # 檢查資料庫連接
    # 檢查 Redis 連接
    # 檢查其他依賴服務
    return {"status": "ready"}
```

### 2. Docker 健康檢查

```dockerfile
# Dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

### 3. Docker Compose 健康檢查

```yaml
services:
  api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## 最佳實踐

### 1. 安全性

- ✅ **使用非 root 用戶運行**
- ✅ **最小化基礎鏡像**
- ✅ **定期更新依賴**
- ✅ **掃描鏡像漏洞**（使用 `docker scan` 或 Trivy）
- ✅ **不要在鏡像中存儲機密**（使用 secrets）

### 2. 效能

- ✅ **使用多階段構建**
- ✅ **優化構建緩存**
- ✅ **使用 .dockerignore**
- ✅ **選擇最小的基礎鏡像**（alpine, slim）
- ✅ **設置資源限制**

### 3. 可維護性

- ✅ **使用明確的標籤**（不要使用 `latest`）
- ✅ **編寫清晰的註釋**
- ✅ **分離開發和生產 Dockerfile**
- ✅ **使用環境變數配置**

### 4. 監控和日誌

- ✅ **實現健康檢查端點**
- ✅ **配置日誌輪轉**
- ✅ **使用結構化日誌**
- ✅ **整合監控工具**

### 5. 構建和部署

**構建鏡像：**
```bash
# 開發環境
docker build -t fastapi-app:dev -f Dockerfile.dev .

# 生產環境
docker build -t fastapi-app:v1.0.0 -f Dockerfile .
```

**標記和推送：**
```bash
# 標記鏡像
docker tag fastapi-app:v1.0.0 registry.example.com/fastapi-app:v1.0.0

# 推送到鏡像倉庫
docker push registry.example.com/fastapi-app:v1.0.0
```

**運行容器：**
```bash
# 開發環境
docker-compose -f docker-compose.dev.yml up

# 生產環境
docker-compose -f docker-compose.prod.yml up -d
```

### 6. 備份和恢復

```yaml
# docker-compose.yml
services:
  db:
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups

  # 備份服務（可選）
  backup:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    command: |
      sh -c "
      while true; do
        PGPASSWORD=$${DB_PASSWORD} pg_dump -h db -U user mydb > /backups/backup-$$(date +%Y%m%d-%H%M%S).sql
        sleep 86400
      done
      "
    depends_on:
      - db
```

## 常見問題

### Q: 鏡像太大怎麼辦？
**A:** 使用多階段構建、選擇更小的基礎鏡像（alpine, slim）、清理構建緩存。

### Q: 如何處理環境變數？
**A:** 使用 `.env` 文件或 Docker secrets，不要在代碼中硬編碼。

### Q: 如何實現零停機部署？
**A:** 使用 Docker Compose 的滾動更新、藍綠部署或金絲雀部署。

### Q: 開發時如何實現熱重載？
**A:** 使用 volumes 掛載代碼目錄，並使用 `--reload` 參數。

### Q: 如何管理多個環境？
**A:** 使用不同的 docker-compose 文件（dev.yml, staging.yml, prod.yml）和環境變數文件。

## 總結

### Flask → FastAPI Docker 遷移總結

| 項目 | Flask | FastAPI | 變化 |
|------|-------|---------|------|
| **服務器** | Gunicorn | Uvicorn | 需要改變 CMD |
| **端口** | 5000 | 8000 | 可選更改 |
| **構建方式** | 相同 | 相同 | 無需改變 |
| **Docker Compose** | 相同 | 相同 | 無需改變 |

### 關鍵要點

1. ✅ **FastAPI 的 Dockerfile 更簡單**（不需要複雜的 worker 配置）
2. ✅ **使用多階段構建減少鏡像大小**
3. ✅ **生產環境使用非 root 用戶**
4. ✅ **實現健康檢查端點**
5. ✅ **使用 Docker Compose 管理多服務**

## 參考資源

- [Docker Documentation](https://docs.docker.com/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [FastAPI Deployment - Docker](https://fastapi.tiangolo.com/deployment/docker/)
- [.dockerignore Best Practices](https://docs.docker.com/engine/reference/builder/#dockerignore-file)

