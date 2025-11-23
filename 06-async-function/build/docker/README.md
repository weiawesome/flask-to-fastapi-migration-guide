# Docker Compose 使用說明

## 啟動 Redis

### 方式 1：使用 Docker Compose（推薦）

```bash
# 進入項目根目錄
cd 06-async-function

# 啟動 Redis
docker-compose -f build/docker/docker-compose.yaml up -d

# 查看 Redis 狀態
docker-compose -f build/docker/docker-compose.yaml ps

# 查看 Redis 日誌
docker-compose -f build/docker/docker-compose.yaml logs -f redis

# 停止 Redis
docker-compose -f build/docker/docker-compose.yaml down

# 停止並刪除數據卷
docker-compose -f build/docker/docker-compose.yaml down -v
```

### 方式 2：直接使用 Docker

```bash
docker run -d \
  --name fastapi-redis \
  -p 6379:6379 \
  -v redis_data:/data \
  redis:7-alpine \
  redis-server --appendonly yes
```

## 測試 Redis 連接

```bash
# 使用 redis-cli 測試（如果已安裝）
redis-cli ping
# 應該返回: PONG

# 或使用 Docker 執行
docker exec -it fastapi-redis redis-cli ping
```

## 環境變數配置

1. 複製環境變數範例文件：
   ```bash
   cp env.example .env
   ```

2. 根據需要修改 `.env` 文件中的配置

3. 如果使用 Docker Compose，Redis 會自動啟動在 `localhost:6379`

## 啟動 Celery Worker（可選）

如果使用 Celery 背景任務：

```bash
# 確保 Redis 已啟動
docker-compose -f build/docker/docker-compose.yaml up -d

# 啟動 Celery Worker
celery -A celery_app worker --loglevel=info

# 啟動 Celery Beat（定時任務，如果需要）
celery -A celery_app beat --loglevel=info
```

## 故障排除

### Redis 連接失敗

1. 檢查 Redis 是否運行：
   ```bash
   docker ps | grep redis
   ```

2. 檢查端口是否被占用：
   ```bash
   lsof -i :6379
   ```

3. 檢查防火牆設置

### 數據持久化

Redis 數據會保存在 Docker volume `redis_data` 中，即使容器重啟也不會丟失。

查看 volume：
```bash
docker volume ls | grep redis
```

