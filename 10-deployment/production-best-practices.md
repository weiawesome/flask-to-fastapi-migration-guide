# 生產環境最佳實踐

## 概述

本文檔提供 FastAPI 應用部署到生產環境的完整最佳實踐指南，涵蓋安全性、效能、可靠性、可維護性等各個方面。

## 目錄

- [生產就緒檢查清單](#生產就緒檢查清單)
- [安全性最佳實踐](#安全性最佳實踐)
- [效能優化](#效能優化)
- [可靠性設計](#可靠性設計)
- [資料庫優化](#資料庫優化)
- [快取策略](#快取策略)
- [零停機部署](#零停機部署)
- [災難恢復](#災難恢復)
- [成本優化](#成本優化)
- [常見陷阱與解決方案](#常見陷阱與解決方案)

## 生產就緒檢查清單

### 應用程式層面

- [ ] **健康檢查端點** - 實現 `/health`, `/health/live`, `/health/ready`
- [ ] **錯誤處理** - 統一錯誤處理和錯誤回應格式
- [ ] **日誌系統** - 結構化日誌，包含 request_id 追蹤
- [ ] **配置管理** - 使用環境變數，無硬編碼配置
- [ ] **API 文檔** - OpenAPI 文檔完整且準確
- [ ] **速率限制** - 防止濫用和 DDoS 攻擊
- [ ] **輸入驗證** - 所有輸入都經過 Pydantic 驗證
- [ ] **輸出序列化** - 使用回應模型，不洩露敏感資訊

### 部署層面

- [ ] **容器化** - 使用 Docker，多階段構建
- [ ] **非 root 用戶** - 容器以非 root 用戶運行
- [ ] **資源限制** - 設置 CPU 和記憶體限制
- [ ] **健康檢查** - 配置 Liveness 和 Readiness Probes
- [ ] **自動重啟** - 設置自動重啟策略
- [ ] **滾動更新** - 支持零停機更新
- [ ] **回滾機制** - 測試並準備回滾流程

### 監控層面

- [ ] **指標收集** - Prometheus 指標端點
- [ ] **日誌聚合** - 集中式日誌收集
- [ ] **告警規則** - 設置關鍵指標告警
- [ ] **儀表板** - Grafana 監控儀表板
- [ ] **APM 工具** - 應用性能監控（可選）

### 安全層面

- [ ] **HTTPS** - 強制使用 HTTPS
- [ ] **CORS** - 正確配置 CORS 策略
- [ ] **認證授權** - JWT 或其他認證機制
- [ ] **機密管理** - 使用 Secret 管理系統
- [ ] **依賴掃描** - 定期掃描依賴漏洞
- [ ] **安全標頭** - 設置安全 HTTP 標頭

## 安全性最佳實踐

### 1. HTTPS 和 SSL/TLS

**必須使用 HTTPS：**

```python
# 使用 Nginx 處理 SSL（推薦）
# Nginx 配置
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    # 強制使用現代 TLS 版本
    ssl_protocols TLSv1.2 TLSv1.3;
}
```

**安全標頭中間件：**

```python
# middleware/security_headers.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # 安全標頭
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
```

### 2. 認證和授權

```python
# 使用強密碼策略
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Token 過期時間設置
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 較短的過期時間
REFRESH_TOKEN_EXPIRE_DAYS = 7

# 實現 Token 黑名單（登出時使 Token 失效）
# 使用 Redis 存儲黑名單
```

### 3. 輸入驗證和清理

```python
# 使用 Pydantic 驗證所有輸入
from pydantic import BaseModel, validator, EmailStr

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    @validator('username')
    def validate_username(cls, v):
        # 防止 SQL 注入和 XSS
        if not v.isalnum() and '_' not in v:
            raise ValueError('Username must be alphanumeric')
        return v
```

### 4. 速率限制

```python
# middleware/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/users")
@limiter.limit("100/minute")
async def get_users(request: Request):
    # ...
```

### 5. 依賴漏洞掃描

```bash
# 使用 safety 掃描依賴
pip install safety
safety check

# 或使用 pip-audit
pip install pip-audit
pip-audit

# 整合到 CI/CD
# .github/workflows/security.yml
```

### 6. 機密資訊管理

```python
# ❌ 錯誤：硬編碼密碼
SECRET_KEY = "hardcoded-secret-key"

# ✅ 正確：從環境變數讀取
SECRET_KEY = os.getenv("SECRET_KEY")

# ✅ 更好：使用 Secret 管理系統
# Kubernetes Secrets, HashiCorp Vault, AWS Secrets Manager
```

## 效能優化

### 1. 資料庫連接池

```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # 連接池大小
    max_overflow=10,       # 最大溢出連接
    pool_pre_ping=True,    # 連接前檢查
    pool_recycle=3600,     # 1 小時後回收連接
    echo=False             # 生產環境關閉 SQL 日誌
)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
```

### 2. 異步 I/O 優化

```python
# ✅ 正確：使用異步 I/O
async def get_user(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

# ❌ 錯誤：阻塞操作
def get_user(user_id: int):
    # 同步操作會阻塞事件循環
    time.sleep(1)
    return session.query(User).get(user_id)
```

### 3. 響應壓縮

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 4. 靜態文件優化

```python
# 使用 Nginx 服務靜態文件（更高效）
# 或使用 FastAPI StaticFiles
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")
```

### 5. 查詢優化

```python
# ✅ 正確：使用 select_related 避免 N+1 查詢
from sqlalchemy.orm import selectinload

users = await session.execute(
    select(User)
    .options(selectinload(User.posts))
    .where(User.active == True)
)

# ❌ 錯誤：N+1 查詢問題
for user in users:
    posts = await session.execute(select(Post).where(Post.user_id == user.id))
```

### 6. 背景任務

```python
# 使用 FastAPI BackgroundTasks 處理非關鍵任務
from fastapi import BackgroundTasks

@app.post("/users")
async def create_user(user: UserCreate, background_tasks: BackgroundTasks):
    # 創建用戶
    new_user = await create_user_in_db(user)
    
    # 發送郵件作為背景任務
    background_tasks.add_task(send_welcome_email, new_user.email)
    
    return new_user

# 對於複雜任務，使用 Celery
from celery import Celery

celery_app = Celery('tasks', broker='redis://localhost:6379')

@celery_app.task
def process_large_file(file_path: str):
    # 長時間運行的任務
    pass
```

## 可靠性設計

### 1. 重試機制

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def call_external_api():
    # 自動重試的外部 API 調用
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
        response.raise_for_status()
        return response.json()
```

### 2. 斷路器模式

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_unreliable_service():
    # 失敗 5 次後開啟斷路器，60 秒後嘗試恢復
    pass
```

### 3. 優雅降級

```python
@app.get("/data")
async def get_data():
    try:
        # 嘗試從外部服務獲取數據
        data = await fetch_from_external_service()
        return data
    except Exception:
        # 降級到緩存數據
        cached_data = await get_from_cache("data")
        if cached_data:
            return cached_data
        # 最後降級到默認數據
        return {"status": "degraded", "data": get_default_data()}
```

### 4. 超時設置

```python
import asyncio

# 設置操作超時
try:
    result = await asyncio.wait_for(
        slow_operation(),
        timeout=5.0  # 5 秒超時
    )
except asyncio.TimeoutError:
    return {"error": "Operation timeout"}
```

## 資料庫優化

### 1. 連接池配置

```python
# 生產環境推薦配置
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # = (CPU cores × 2) + 1
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)
```

### 2. 索引優化

```python
# models.py
from sqlalchemy import Index

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)  # 唯一索引
    created_at = Column(DateTime, index=True)  # 普通索引

# 複合索引
Index('idx_user_status_created', User.status, User.created_at)
```

### 3. 查詢優化

```python
# ✅ 正確：只查詢需要的字段
users = await session.execute(
    select(User.id, User.name).where(User.active == True)
)

# ✅ 正確：使用分頁
users = await session.execute(
    select(User)
    .where(User.active == True)
    .limit(20)
    .offset(0)
)

# ✅ 正確：批量操作
await session.execute(
    update(User)
    .where(User.inactive_days > 365)
    .values(status='archived')
)
```

### 4. 資料庫遷移

```bash
# 使用 Alembic 進行資料庫遷移
alembic revision --autogenerate -m "Add user table"
alembic upgrade head

# 生產環境遷移流程
# 1. 備份資料庫
# 2. 測試遷移腳本
# 3. 在維護窗口執行遷移
# 4. 驗證遷移結果
```

## 快取策略

### 1. Redis 快取

```python
import aioredis

redis = aioredis.from_url("redis://localhost:6379")

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    # 1. 嘗試從緩存獲取
    cached_user = await redis.get(f"user:{user_id}")
    if cached_user:
        return json.loads(cached_user)
    
    # 2. 從資料庫獲取
    user = await get_user_from_db(user_id)
    
    # 3. 存入緩存（設置過期時間）
    await redis.setex(
        f"user:{user_id}",
        300,  # 5 分鐘
        json.dumps(user.dict())
    )
    
    return user
```

### 2. 快取失效策略

```python
# 更新數據時清除相關緩存
@app.put("/users/{user_id}")
async def update_user(user_id: int, user_data: UserUpdate):
    # 更新資料庫
    user = await update_user_in_db(user_id, user_data)
    
    # 清除緩存
    await redis.delete(f"user:{user_id}")
    await redis.delete("users:list")  # 清除列表緩存
    
    return user
```

### 3. 快取穿透、擊穿、雪崩防護

```python
# 防止快取穿透：使用布隆過濾器或緩存空值
# 防止快取擊穿：使用互斥鎖
# 防止快取雪崩：設置隨機過期時間

import asyncio

async def get_user_with_cache(user_id: int):
    # 嘗試獲取緩存
    cached = await redis.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)
    
    # 使用分布式鎖防止擊穿
    lock_key = f"lock:user:{user_id}"
    lock = await redis.set(lock_key, "1", nx=True, ex=10)  # 10 秒鎖
    
    if lock:
        try:
            # 查詢資料庫
            user = await get_user_from_db(user_id)
            
            # 存入緩存（隨機過期時間防止雪崩）
            import random
            expire_time = 300 + random.randint(0, 60)  # 300-360 秒
            await redis.setex(
                f"user:{user_id}",
                expire_time,
                json.dumps(user.dict() if user else {})
            )
            
            return user
        finally:
            await redis.delete(lock_key)
    else:
        # 等待其他進程完成後重試
        await asyncio.sleep(0.1)
        return await get_user_with_cache(user_id)
```

## 零停機部署

### 1. 滾動更新

```yaml
# Kubernetes Deployment
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1          # 最多新增 1 個 Pod
      maxUnavailable: 0    # 確保始終有可用 Pod
```

### 2. 藍綠部署

```yaml
# 藍色版本（當前）
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app-blue
spec:
  replicas: 3

---
# 綠色版本（新版本）
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app-green
spec:
  replicas: 0  # 初始為 0
```

### 3. 金絲雀部署

```yaml
# 使用 Istio 或 Flagger 進行金絲雀部署
# 逐步將流量從舊版本切換到新版本
```

### 4. 健康檢查和就緒探針

```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 15
  periodSeconds: 5
  failureThreshold: 3
```

## 災難恢復

### 1. 資料庫備份

```bash
# 定期備份資料庫
# 使用 cron 任務或 Kubernetes CronJob

# PostgreSQL 備份
pg_dump -h db_host -U user db_name > backup_$(date +%Y%m%d).sql

# 備份到雲端存儲（S3, GCS）
aws s3 cp backup.sql s3://backup-bucket/daily/
```

### 2. 備份策略

- **全量備份**: 每天一次
- **增量備份**: 每小時一次
- **保留策略**: 
  - 最近 7 天：每日備份
  - 最近 4 周：每週備份
  - 最近 12 個月：每月備份

### 3. 災難恢復計劃

1. **識別關鍵系統和數據**
2. **定義恢復時間目標 (RTO)** - 例如：4 小時
3. **定義恢復點目標 (RPO)** - 例如：1 小時
4. **定期測試恢復流程**
5. **文檔化恢復步驟**

## 成本優化

### 1. 資源優化

```yaml
# 設置合理的資源限制
resources:
  requests:
    memory: "256Mi"  # 根據實際使用調整
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### 2. 自動擴縮容

```yaml
# HPA 根據實際負載擴縮容
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  minReplicas: 2     # 最小副本數
  maxReplicas: 10    # 最大副本數
```

### 3. 使用 Spot 實例（雲端）

```yaml
# Kubernetes Node Selector
spec:
  template:
    spec:
      nodeSelector:
        instance-type: spot
```

### 4. 快取減少資料庫負載

```python
# 使用 Redis 快取減少資料庫查詢
# 降低資料庫成本
```

## 常見陷阱與解決方案

### 1. 記憶體洩漏

**問題：** 應用記憶體持續增長

**解決方案：**
- 定期重啟 worker（使用 `max-requests`）
- 檢查是否有未釋放的資源（資料庫連接、文件句柄）
- 使用記憶體分析工具（memory_profiler）

### 2. 資料庫連接耗盡

**問題：** 錯誤 "too many connections"

**解決方案：**
- 使用連接池並設置合理的池大小
- 確保連接正確關閉
- 設置連接超時和回收時間

### 3. N+1 查詢問題

**問題：** 查詢效率低，資料庫負載高

**解決方案：**
```python
# 使用 selectinload 或 joinedload
from sqlalchemy.orm import selectinload

users = await session.execute(
    select(User).options(selectinload(User.posts))
)
```

### 4. 同步操作阻塞事件循環

**問題：** 異步應用效能差

**解決方案：**
```python
# ❌ 錯誤
time.sleep(1)

# ✅ 正確
await asyncio.sleep(1)
```

### 5. 配置硬編碼

**問題：** 不同環境需要不同配置

**解決方案：** 使用環境變數和 Pydantic Settings

## 總結

### 關鍵原則

1. ✅ **安全性優先** - 總是考慮安全影響
2. ✅ **監控一切** - 無法監控就無法改進
3. ✅ **設計容錯** - 假設一切都會失敗
4. ✅ **自動化部署** - 減少人為錯誤
5. ✅ **文檔化** - 記錄所有重要決策和流程

### 持續改進

生產環境最佳實踐不是一次性的，而是持續改進的過程：

- 📊 **定期檢討監控指標**
- 🔍 **分析效能瓶頸**
- 🔐 **更新安全措施**
- 📝 **更新文檔和流程**
- 🧪 **定期進行災難恢復演練**

## 參考資源

- [FastAPI Production Checklist](https://fastapi.tiangolo.com/deployment/#production-checklist)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [12-Factor App](https://12factor.net/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/cluster-administration/manage-deployment/)
- [Database Connection Pooling](https://docs.sqlalchemy.org/en/14/core/pooling.html)

