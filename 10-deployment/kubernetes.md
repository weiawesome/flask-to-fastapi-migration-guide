# Kubernetes 編排

## 概述

Kubernetes (K8s) 是生產環境部署 FastAPI 應用的最佳選擇，提供了自動擴展、負載均衡、滾動更新等強大功能。本章將學習如何在 Kubernetes 上部署和管理 FastAPI 應用。

## 目錄

- [Kubernetes 基礎概念](#kubernetes-基礎概念)
- [Deployment 配置](#deployment-配置)
- [Service 配置](#service-配置)
- [ConfigMap 和 Secret](#configmap-和-secret)
- [Horizontal Pod Autoscaler (HPA)](#horizontal-pod-autoscaler-hpa)
- [Ingress 配置](#ingress-配置)
- [健康檢查 (Probes)](#健康檢查-probes)
- [滾動更新與回滾](#滾動更新與回滾)
- [生產環境最佳實踐](#生產環境最佳實踐)

## Kubernetes 基礎概念

### 核心組件

| 組件 | 說明 | 用途 |
|------|------|------|
| **Pod** | 最小部署單元 | 運行一個或多個容器 |
| **Deployment** | 管理 Pod 的副本 | 聲明式管理應用 |
| **Service** | 服務發現和負載均衡 | 暴露應用服務 |
| **ConfigMap** | 配置管理 | 存儲非機密配置 |
| **Secret** | 機密管理 | 存儲密碼、token 等 |
| **Ingress** | HTTP/HTTPS 路由 | 外部訪問入口 |
| **HPA** | 水平自動擴展 | 根據指標自動擴縮容 |

### 架構對比

**傳統部署：**
```
Load Balancer
  ↓
Nginx
  ↓
Application Servers (固定數量)
```

**Kubernetes 部署：**
```
Ingress
  ↓
Service (負載均衡)
  ↓
Deployment
  ├─ Pod 1 (可動態擴展)
  ├─ Pod 2
  ├─ Pod 3
  └─ Pod N
```

## Deployment 配置

### 基礎 Deployment

`k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
  namespace: default
  labels:
    app: fastapi-app
    version: v1.0.0
spec:
  replicas: 3  # Pod 副本數
  selector:
    matchLabels:
      app: fastapi-app
  template:
    metadata:
      labels:
        app: fastapi-app
        version: v1.0.0
    spec:
      containers:
      - name: fastapi
        image: your-registry/fastapi-app:v1.0.0
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
          protocol: TCP
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: fastapi-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: fastapi-config
              key: redis-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
```

### 生產環境 Deployment

`k8s/deployment-prod.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
  namespace: production
  labels:
    app: fastapi-app
    component: api
    tier: backend
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1          # 滾動更新時最多新增的 Pod 數
      maxUnavailable: 0    # 滾動更新時最多不可用的 Pod 數（確保零停機）
  selector:
    matchLabels:
      app: fastapi-app
  template:
    metadata:
      labels:
        app: fastapi-app
        component: api
        tier: backend
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      # 使用非 root 用戶
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: fastapi
        image: your-registry/fastapi-app:v1.0.0
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
          protocol: TCP
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: fastapi-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: fastapi-config
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        startupProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 30  # 最多等待 5 分鐘
        volumeMounts:
        - name: config
          mountPath: /app/config
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: fastapi-config
      # 拉取鏡像的認證
      imagePullSecrets:
      - name: registry-secret
```

### 應用 Deployment

```bash
# 創建 Deployment
kubectl apply -f k8s/deployment.yaml

# 查看狀態
kubectl get deployments
kubectl get pods -l app=fastapi-app

# 查看詳細信息
kubectl describe deployment fastapi-app

# 查看 Pod 日誌
kubectl logs -f deployment/fastapi-app
```

## Service 配置

Service 提供穩定的 IP 和 DNS 名稱，用於服務發現和負載均衡。

### ClusterIP Service（內部訪問）

`k8s/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
  namespace: default
  labels:
    app: fastapi-app
spec:
  type: ClusterIP  # 集群內部訪問
  selector:
    app: fastapi-app
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
    name: http
  sessionAffinity: ClientIP  # 會話親和性
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800
```

### LoadBalancer Service（雲端外部訪問）

`k8s/service-lb.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service-lb
  namespace: production
  labels:
    app: fastapi-app
spec:
  type: LoadBalancer
  selector:
    app: fastapi-app
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
    name: http
  # 雲端特定註釋（以 AWS 為例）
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-backend-protocol: "tcp"
```

### NodePort Service（直接訪問節點）

`k8s/service-nodeport.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service-np
  namespace: default
spec:
  type: NodePort
  selector:
    app: fastapi-app
  ports:
  - port: 80
    targetPort: 8000
    nodePort: 30080  # 30000-32767 範圍
    protocol: TCP
    name: http
```

## ConfigMap 和 Secret

### ConfigMap（非機密配置）

`k8s/configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fastapi-config
  namespace: default
data:
  # 鍵值對配置
  redis-url: "redis://redis-service:6379"
  log-level: "INFO"
  
  # 文件配置
  app-config.yaml: |
    app:
      name: FastAPI App
      version: "1.0.0"
    database:
      pool-size: 10
      timeout: 30
```

創建和應用：

```bash
# 從文件創建
kubectl create configmap fastapi-config \
  --from-file=config.yaml \
  --from-literal=redis-url=redis://redis-service:6379

# 或使用 YAML
kubectl apply -f k8s/configmap.yaml

# 查看
kubectl get configmap fastapi-config -o yaml
```

### Secret（機密資訊）

`k8s/secret.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: fastapi-secrets
  namespace: default
type: Opaque
data:
  # Base64 編碼的值
  database-url: cG9zdGdyZXNxbDovL3VzZXI6cGFzc0BkYjoxMjM0L215ZGI=
  api-key: YWJjZGVmZ2hpams=
  jwt-secret: eW91ci1qd3Qtc2VjcmV0LWhlcmU=
```

**注意：** Secret 中的值是 Base64 編碼的。

創建 Secret：

```bash
# 從命令行創建
kubectl create secret generic fastapi-secrets \
  --from-literal=database-url='postgresql://user:pass@db:5432/mydb' \
  --from-literal=api-key='abc123'

# 或從文件創建
kubectl create secret generic fastapi-secrets \
  --from-file=./secrets/database-url.txt

# 或使用 YAML（需要 Base64 編碼）
echo -n 'your-value' | base64
# 然後放入 YAML 文件
kubectl apply -f k8s/secret.yaml
```

**安全最佳實踐：**
- ✅ 使用 Kubernetes Secrets 或外部 Secret 管理工具（如 HashiCorp Vault）
- ✅ 不要將 Secret 提交到 Git
- ✅ 使用 RBAC 限制 Secret 訪問
- ✅ 定期輪換密鑰

## Horizontal Pod Autoscaler (HPA)

HPA 根據 CPU、記憶體或自定義指標自動擴縮容 Pod。

### 基礎 HPA（CPU/記憶體）

`k8s/hpa.yaml`:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-hpa
  namespace: default
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-app
  minReplicas: 3        # 最小副本數
  maxReplicas: 10       # 最大副本數
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70  # CPU 使用率目標 70%
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80  # 記憶體使用率目標 80%
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # 縮容等待 5 分鐘
      policies:
      - type: Percent
        value: 50           # 每次最多縮減 50%
        periodSeconds: 60   # 每 60 秒評估一次
    scaleUp:
      stabilizationWindowSeconds: 0    # 立即擴容
      policies:
      - type: Percent
        value: 100          # 每次最多增加 100%
        periodSeconds: 15   # 每 15 秒評估一次
      - type: Pods
        value: 2            # 或每次增加 2 個 Pod
        periodSeconds: 15
      selectPolicy: Max     # 選擇最大擴展策略
```

### 高級 HPA（自定義指標）

需要安裝 Metrics Server 和 Prometheus Adapter：

`k8s/hpa-custom.yaml`:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-hpa-custom
  namespace: default
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-app
  minReplicas: 3
  maxReplicas: 20
  metrics:
  # CPU 指標
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  # 自定義指標：請求速率
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"  # 每個 Pod 處理 100 req/s
  # 外部指標：隊列長度
  - type: External
    external:
      metric:
        name: queue_length
        selector:
          matchLabels:
            queue: task-queue
      target:
        type: AverageValue
        averageValue: "50"   # 平均隊列長度 50
```

應用和查看：

```bash
# 應用 HPA
kubectl apply -f k8s/hpa.yaml

# 查看 HPA 狀態
kubectl get hpa fastapi-hpa

# 查看詳細信息
kubectl describe hpa fastapi-hpa

# 查看擴容事件
kubectl get events --sort-by='.lastTimestamp' | grep fastapi-hpa
```

### HPA 最佳實踐

1. **設置合理的 min/max replicas**
   - min: 確保高可用性（至少 2-3 個）
   - max: 根據資源限制設置上限

2. **調整擴縮容速度**
   - 快速擴容：及時應對流量高峰
   - 慢速縮容：避免頻繁擴縮容

3. **使用多個指標**
   - CPU + 記憶體 + 自定義指標（請求速率）

4. **監控 HPA 行為**
   - 觀察擴縮容頻率
   - 調整目標值避免抖動

## Ingress 配置

Ingress 提供 HTTP/HTTPS 路由，外部訪問應用的入口。

### 基礎 Ingress

`k8s/ingress.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fastapi-ingress
  namespace: default
  annotations:
    # 使用 Nginx Ingress Controller
    kubernetes.io/ingress.class: "nginx"
    # SSL 重定向
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    # 會話親和性
    nginx.ingress.kubernetes.io/affinity: "cookie"
    # 客戶端上傳大小限制
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
spec:
  tls:
  - hosts:
    - api.example.com
    secretName: fastapi-tls
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: fastapi-service
            port:
              number: 80
```

### 生產環境 Ingress（多域名、速率限制）

`k8s/ingress-prod.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fastapi-ingress-prod
  namespace: production
  annotations:
    kubernetes.io/ingress.class: "nginx"
    # SSL 配置
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    # 速率限制（每個 IP 每分鐘 100 請求）
    nginx.ingress.kubernetes.io/limit-rps: "100"
    nginx.ingress.kubernetes.io/limit-connections: "10"
    # CORS
    nginx.ingress.kubernetes.io/enable-cors: "true"
    nginx.ingress.kubernetes.io/cors-allow-origin: "https://frontend.example.com"
    # WebSocket 支援
    nginx.ingress.kubernetes.io/websocket-services: "fastapi-service"
    # 日誌格式
    nginx.ingress.kubernetes.io/log-format: |
      '$remote_addr - $remote_user [$time_local] "$request" '
      '$status $body_bytes_sent "$http_referer" '
      '"$http_user_agent" "$http_x_forwarded_for" '
      'rt=$request_time uct="$upstream_connect_time" '
      'uht="$upstream_header_time" urt="$upstream_response_time"'
spec:
  tls:
  - hosts:
    - api.example.com
    - api-prod.example.com
    secretName: fastapi-tls
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /api/v1
        pathType: Prefix
        backend:
          service:
            name: fastapi-service
            port:
              number: 80
  - host: api-prod.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: fastapi-service
            port:
              number: 80
```

## 健康檢查 (Probes)

Kubernetes 提供三種探針來監控 Pod 健康狀態。

### 1. Liveness Probe（存活探針）

檢查容器是否還在運行，如果失敗會重啟容器。

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30    # 容器啟動 30 秒後開始檢查
  periodSeconds: 10          # 每 10 秒檢查一次
  timeoutSeconds: 5          # 超時時間 5 秒
  failureThreshold: 3        # 連續失敗 3 次後重啟
  successThreshold: 1        # 成功 1 次就認為健康
```

### 2. Readiness Probe（就緒探針）

檢查容器是否準備好接收流量，如果失敗會從 Service 中移除。

```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

### 3. Startup Probe（啟動探針）

檢查容器是否已啟動，適合啟動較慢的應用。

```yaml
startupProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 30       # 最多等待 2.5 分鐘（30 × 5）
```

### FastAPI 健康檢查端點實現

```python
# main.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import asyncio

app = FastAPI()

# 全局健康狀態
healthy = True

@app.get("/health/live")
async def liveness():
    """Liveness 探針：檢查應用是否運行"""
    if healthy:
        return {"status": "alive"}
    else:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy"}
        )

@app.get("/health/ready")
async def readiness():
    """Readiness 探針：檢查應用是否準備好接收請求"""
    # 檢查資料庫連接
    try:
        # await check_database_connection()
        pass
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "reason": "database"}
        )
    
    # 檢查 Redis 連接
    try:
        # await check_redis_connection()
        pass
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "reason": "redis"}
        )
    
    return {"status": "ready"}

@app.get("/health/startup")
async def startup():
    """Startup 探針：檢查應用是否已啟動"""
    # 檢查必要的初始化是否完成
    return {"status": "started"}
```

## 滾動更新與回滾

### 滾動更新策略

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1          # 滾動更新時最多新增 1 個 Pod
      maxUnavailable: 0    # 確保零停機（至少 3 個 Pod 可用）
```

更新流程：

```bash
# 更新鏡像版本
kubectl set image deployment/fastapi-app \
  fastapi=your-registry/fastapi-app:v1.1.0

# 或編輯 Deployment
kubectl edit deployment fastapi-app

# 查看滾動更新狀態
kubectl rollout status deployment/fastapi-app

# 查看更新歷史
kubectl rollout history deployment/fastapi-app
```

### 回滾

```bash
# 回滾到上一個版本
kubectl rollout undo deployment/fastapi-app

# 回滾到特定版本
kubectl rollout undo deployment/fastapi-app --to-revision=2

# 查看特定版本的配置
kubectl rollout history deployment/fastapi-app --revision=2
```

### 藍綠部署

使用兩個 Deployment 進行藍綠部署：

```yaml
# 藍色版本（當前版本）
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app-blue
spec:
  replicas: 3
  # ...

---
# 綠色版本（新版本）
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app-green
spec:
  replicas: 0  # 初始為 0
  # ...
```

切換流量：

```bash
# 擴展綠色版本
kubectl scale deployment fastapi-app-green --replicas=3

# 更新 Service selector 指向綠色版本
kubectl patch service fastapi-service -p \
  '{"spec":{"selector":{"version":"green"}}}'

# 如果沒問題，刪除藍色版本
kubectl delete deployment fastapi-app-blue
```

## 生產環境最佳實踐

### 1. 資源管理

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

**建議：**
- ✅ requests 應該設置為正常運行所需資源
- ✅ limits 應該設置為最大允許資源
- ✅ 避免過度配置（浪費資源）或配置不足（性能問題）

### 2. 命名空間組織

```bash
# 創建不同環境的命名空間
kubectl create namespace development
kubectl create namespace staging
kubectl create namespace production

# 在特定命名空間部署
kubectl apply -f k8s/deployment.yaml -n production
```

### 3. 標籤和選擇器

```yaml
metadata:
  labels:
    app: fastapi-app
    component: api
    tier: backend
    version: v1.0.0
    environment: production
```

### 4. 日誌管理

使用 DaemonSet 收集日誌（如 Fluentd、Filebeat）：

```yaml
# 註釋添加到 Pod
metadata:
  annotations:
    fluentd.org/log: "true"
```

### 5. 監控和告警

整合 Prometheus 監控：

```yaml
metadata:
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8000"
    prometheus.io/path: "/metrics"
```

## 完整部署示例

### 目錄結構

```
k8s/
├── namespace.yaml
├── configmap.yaml
├── secret.yaml
├── deployment.yaml
├── service.yaml
├── ingress.yaml
├── hpa.yaml
└── README.md
```

### 部署步驟

```bash
# 1. 創建命名空間
kubectl apply -f k8s/namespace.yaml

# 2. 創建 ConfigMap 和 Secret
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# 3. 創建 Deployment
kubectl apply -f k8s/deployment.yaml

# 4. 創建 Service
kubectl apply -f k8s/service.yaml

# 5. 創建 Ingress
kubectl apply -f k8s/ingress.yaml

# 6. 創建 HPA
kubectl apply -f k8s/hpa.yaml

# 7. 檢查狀態
kubectl get all -l app=fastapi-app
```

## 總結

### 關鍵要點

1. ✅ **Deployment 管理 Pod 副本和更新**
2. ✅ **Service 提供服務發現和負載均衡**
3. ✅ **ConfigMap 和 Secret 管理配置和機密**
4. ✅ **HPA 實現自動擴縮容**
5. ✅ **Ingress 提供外部訪問入口**
6. ✅ **健康檢查確保應用可靠性**
7. ✅ **滾動更新實現零停機部署**

### 生產環境檢查清單

- [ ] 設置合理的資源 requests 和 limits
- [ ] 配置 Liveness 和 Readiness Probes
- [ ] 設置 HPA 自動擴縮容
- [ ] 配置 Ingress 和 TLS
- [ ] 使用 Secret 管理機密資訊
- [ ] 設置滾動更新策略
- [ ] 配置日誌收集
- [ ] 設置監控和告警
- [ ] 測試回滾流程
- [ ] 進行負載測試

## 參考資源

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kubernetes HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [Kubernetes Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/setup/best-practices/)

