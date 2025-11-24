# 監控與日誌

## 概述

完整的監控和日誌系統是生產環境運維的基礎。本章將學習如何為 FastAPI 應用設置監控（Prometheus、Grafana）和日誌系統，確保應用的可觀測性。

## 目錄

- [監控架構概覽](#監控架構概覽)
- [健康檢查端點](#健康檢查端點)
- [Prometheus 指標收集](#prometheus-指標收集)
- [Grafana 儀表板](#grafana-儀表板)
- [日誌系統](#日誌系統)
- [告警配置](#告警配置)
- [APM 工具整合](#apm-工具整合)
- [最佳實踐](#最佳實踐)

## 監控架構概覽

### 完整監控堆棧

```
FastAPI 應用
  ├─ 健康檢查端點 (/health)
  ├─ Prometheus 指標端點 (/metrics)
  ├─ 結構化日誌
  │
  ↓
Prometheus (指標收集)
  ├─ 抓取 /metrics 端點
  ├─ 存儲時間序列數據
  └─ 告警規則評估
  │
  ↓
Grafana (可視化)
  ├─ 儀表板展示
  ├─ 查詢 Prometheus
  └─ 告警通知
  │
  ↓
告警管理器 (AlertManager)
  ├─ 告警路由
  ├─ 去重和分組
  └─ 通知 (Email, Slack, PagerDuty)
```

### 三支柱模型

| 支柱 | 工具 | 用途 |
|------|------|------|
| **指標 (Metrics)** | Prometheus | 數值時間序列數據 |
| **日誌 (Logs)** | ELK / Loki | 文本日誌記錄 |
| **追蹤 (Traces)** | Jaeger / Zipkin | 請求分佈式追蹤 |

## 健康檢查端點

健康檢查端點是監控系統的基礎，用於判斷應用是否正常運行。

### 基礎健康檢查

```python
# main.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime

app = FastAPI()

@app.get("/health")
async def health():
    """基礎健康檢查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
```

### 詳細健康檢查

```python
# routers/health.py
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Dict, Any
import asyncio

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    """基礎健康檢查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@router.get("/live")
async def liveness():
    """Liveness 探針：檢查應用是否運行"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/ready")
async def readiness():
    """Readiness 探針：檢查應用是否準備好接收請求"""
    checks: Dict[str, Any] = {
        "database": await check_database(),
        "redis": await check_redis(),
        "external_api": await check_external_api()
    }
    
    all_healthy = all(check["status"] == "ok" for check in checks.values())
    
    status_code = 200 if all_healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_healthy else "not ready",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks
        }
    )

async def check_database() -> Dict[str, Any]:
    """檢查資料庫連接"""
    try:
        # 實際的資料庫檢查邏輯
        # await db.execute("SELECT 1")
        return {"status": "ok", "response_time_ms": 10}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def check_redis() -> Dict[str, Any]:
    """檢查 Redis 連接"""
    try:
        # 實際的 Redis 檢查邏輯
        # await redis.ping()
        return {"status": "ok", "response_time_ms": 5}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def check_external_api() -> Dict[str, Any]:
    """檢查外部 API 連接"""
    try:
        # 實際的外部 API 檢查邏輯
        return {"status": "ok", "response_time_ms": 50}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/startup")
async def startup():
    """Startup 探針：檢查應用是否已啟動"""
    # 檢查必要的初始化是否完成
    return {
        "status": "started",
        "timestamp": datetime.utcnow().isoformat()
    }
```

### 在主應用中註冊

```python
# main.py
from fastapi import FastAPI
from routers import health

app = FastAPI()

app.include_router(health.router)
```

## Prometheus 指標收集

Prometheus 是業界標準的指標監控系統，FastAPI 可以輕鬆集成。

### 1. 安裝依賴

```bash
pip install prometheus-client prometheus-fastapi-instrumentator
```

### 2. 基礎指標收集

```python
# main.py
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# 自動收集標準指標
Instrumentator().instrument(app).expose(app)
```

這會自動暴露 `/metrics` 端點，並收集以下指標：
- `http_requests_total` - 請求總數
- `http_request_duration_seconds` - 請求耗時
- `http_request_size_bytes` - 請求大小
- `http_response_size_bytes` - 回應大小

### 3. 自定義指標

```python
# utils/metrics.py
from prometheus_client import Counter, Histogram, Gauge
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# 定義自定義指標
REQUEST_COUNT = Counter(
    'fastapi_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'fastapi_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

ACTIVE_CONNECTIONS = Gauge(
    'fastapi_active_connections',
    'Number of active connections'
)

DATABASE_CONNECTIONS = Gauge(
    'fastapi_database_connections',
    'Number of database connections',
    ['state']  # idle, active
)

# 指標收集中間件
from starlette.middleware.base import BaseHTTPMiddleware
import time

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        
        # 處理請求
        response = await call_next(request)
        
        # 記錄指標
        duration = time.time() - start_time
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response

# 暴露指標端點
async def metrics_endpoint():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

### 4. 在應用中使用

```python
# main.py
from fastapi import FastAPI
from utils.metrics import MetricsMiddleware, metrics_endpoint
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# 添加指標中間件
app.add_middleware(MetricsMiddleware)

# 自動收集標準指標
Instrumentator().instrument(app).expose(app)

# 自定義指標端點（可選）
@app.get("/metrics")
async def metrics():
    from utils.metrics import generate_latest, CONTENT_TYPE_LATEST
    from fastapi import Response
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

### 5. Prometheus 配置

`prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'fastapi-app'
    scrape_interval: 10s
    metrics_path: '/metrics'
    static_configs:
      - targets: ['fastapi-app:8000']
        labels:
          app: 'fastapi-app'
          environment: 'production'

  - job_name: 'fastapi-app-kubernetes'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
```

### 6. Docker Compose 整合

`docker-compose.monitoring.yml`:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "9090:9090"
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    depends_on:
      - prometheus
    networks:
      - monitoring

volumes:
  prometheus_data:
  grafana_data:

networks:
  monitoring:
```

## Grafana 儀表板

Grafana 提供強大的可視化功能，可以創建豐富的監控儀表板。

### 1. 數據源配置

`grafana/datasources/prometheus.yml`:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
```

### 2. 儀表板配置

`grafana/dashboards/fastapi-dashboard.json`:

```json
{
  "dashboard": {
    "title": "FastAPI Application Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(fastapi_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Request Duration (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(fastapi_request_duration_seconds_bucket[5m]))",
            "legendFormat": "p95"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(fastapi_requests_total{status_code=~'5..'}[5m])",
            "legendFormat": "5xx errors"
          }
        ]
      }
    ]
  }
}
```

### 3. 常用 Prometheus 查詢

```promql
# 請求速率（每秒請求數）
rate(fastapi_requests_total[5m])

# 錯誤率
rate(fastapi_requests_total{status_code=~"5.."}[5m]) / rate(fastapi_requests_total[5m])

# P95 延遲
histogram_quantile(0.95, rate(fastapi_request_duration_seconds_bucket[5m]))

# 活躍連接數
fastapi_active_connections

# 資料庫連接數
fastapi_database_connections
```

## 日誌系統

結構化日誌是生產環境日誌管理的標準做法。

### 1. 結構化日誌配置

```python
# utils/logger.py
import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """JSON 格式的日誌格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加異常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 添加額外字段
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        return json.dumps(log_data)

def setup_logger(
    name: str = "fastapi_app",
    level: int = logging.INFO,
    log_file: str | None = None
) -> logging.Logger:
    """設置日誌系統"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()
    
    # Console Handler (JSON 格式)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # File Handler (可選)
    if log_file:
        from pathlib import Path
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    
    return logger
```

### 2. 日誌中間件

```python
# middleware/logging_middleware.py
import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("fastapi_app")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", "unknown")
        
        # 記錄請求開始
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
            }
        )
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # 記錄請求完成
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration * 1000,
                }
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # 記錄錯誤
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "duration_ms": duration * 1000,
                },
                exc_info=True
            )
            raise
```

### 3. 在應用中使用

```python
# main.py
from fastapi import FastAPI
from utils.logger import setup_logger
from middleware.logging_middleware import LoggingMiddleware

# 設置日誌
logger = setup_logger("fastapi_app", level=logging.INFO)

app = FastAPI()

# 添加日誌中間件
app.add_middleware(LoggingMiddleware)

@app.on_event("startup")
async def startup_event():
    logger.info("Application started")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown")
```

### 4. Loki 日誌聚合

使用 Grafana Loki 收集和查詢日誌：

`docker-compose.logging.yml`:

```yaml
version: '3.8'

services:
  loki:
    image: grafana/loki:latest
    container_name: loki
    ports:
      - "3100:3100"
    volumes:
      - ./loki/loki-config.yml:/etc/loki/local-config.yaml
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml

  promtail:
    image: grafana/promtail:latest
    container_name: promtail
    volumes:
      - ./promtail/promtail-config.yml:/etc/promtail/config.yml
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    command: -config.file=/etc/promtail/config.yml

volumes:
  loki_data:
```

## 告警配置

### 1. Prometheus 告警規則

`prometheus/alerts.yml`:

```yaml
groups:
  - name: fastapi_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: |
          rate(fastapi_requests_total{status_code=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanize }} errors/second"

      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, rate(fastapi_request_duration_seconds_bucket[5m])) > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "P95 latency is {{ $value }}s"

      - alert: ApplicationDown
        expr: |
          up{job="fastapi-app"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Application is down"
          description: "FastAPI application is not responding"
```

### 2. AlertManager 配置

`alertmanager/alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'

receivers:
  - name: 'default'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#alerts'
        title: 'Alert'
        text: '{{ .GroupLabels.alertname }}: {{ .CommonAnnotations.summary }}'

  - name: 'critical-alerts'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#critical-alerts'
    email_configs:
      - to: 'oncall@example.com'
        from: 'alerts@example.com'
        smarthost: 'smtp.example.com:587'
        auth_username: 'alerts@example.com'
        auth_password: 'password'
```

## APM 工具整合

### 1. Sentry 錯誤追蹤

```python
# main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn="YOUR_SENTRY_DSN",
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
    ],
    traces_sample_rate=0.1,  # 10% 的請求追蹤
    environment="production",
)

app = FastAPI()
```

### 2. DataDog APM

```python
# main.py
from ddtrace import patch_all
from ddtrace.contrib.fastapi import TraceMiddleware

patch_all()

app = FastAPI()
app.add_middleware(TraceMiddleware, service="fastapi-app")
```

## 最佳實踐

### 1. 監控指標選擇

**必須監控：**
- ✅ 請求速率（RPS）
- ✅ 錯誤率（4xx, 5xx）
- ✅ 延遲（P50, P95, P99）
- ✅ 應用健康狀態

**建議監控：**
- ✅ 資料庫連接數
- ✅ 快取命中率
- ✅ 隊列長度
- ✅ 資源使用率（CPU、記憶體）

### 2. 日誌級別使用

- **DEBUG**: 詳細調試信息（開發環境）
- **INFO**: 正常運行的關鍵事件（生產環境）
- **WARNING**: 警告但不影響運行
- **ERROR**: 錯誤但應用可以恢復
- **CRITICAL**: 嚴重錯誤，應用可能無法繼續運行

### 3. 日誌收集建議

- ✅ 使用結構化日誌（JSON）
- ✅ 包含 request_id 便於追蹤
- ✅ 不要記錄敏感資訊（密碼、token）
- ✅ 設置日誌輪轉防止磁盤滿
- ✅ 使用日誌聚合工具（Loki, ELK）

### 4. 告警規則設計

- ✅ 設置合理的閾值（避免告警風暴）
- ✅ 使用告警分組減少通知
- ✅ 區分警告和嚴重告警
- ✅ 定期檢討和調整告警規則

## 總結

### 關鍵要點

1. ✅ **健康檢查端點是監控基礎**
2. ✅ **Prometheus 是標準的指標監控系統**
3. ✅ **Grafana 提供強大的可視化**
4. ✅ **結構化日誌便於分析和查詢**
5. ✅ **告警規則需要定期檢討**

### 監控檢查清單

- [ ] 實現健康檢查端點
- [ ] 配置 Prometheus 指標收集
- [ ] 設置 Grafana 儀表板
- [ ] 配置結構化日誌
- [ ] 設置日誌聚合（可選）
- [ ] 配置告警規則
- [ ] 整合 APM 工具（可選）
- [ ] 測試告警通知

## 參考資源

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus FastAPI Instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator)
- [Grafana Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Sentry Python SDK](https://docs.sentry.io/platforms/python/)

