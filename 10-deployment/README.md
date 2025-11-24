# 10 - 部署與生產環境

## 本章學習重點

本章重點學習如何將 FastAPI 應用部署到生產環境，從傳統的 WSGI 部署方式遷移到現代化的 ASGI 部署，並掌握容器化、編排、監控等生產環境必備技能。

✅ **已包含的內容：**
- Flask Gunicorn (WSGI) → FastAPI Uvicorn/Hypercorn (ASGI) 遷移
- Docker 容器化部署策略
- Kubernetes 編排與水平擴展 (HPA)
- 環境變數管理與配置
- 健康檢查端點實現
- 監控與日誌系統 (Prometheus, Grafana)
- 生產環境最佳實踐

## 目錄

- [概述](#概述)
- [部署決策樹](#部署決策樹)
- [Flask vs FastAPI 部署對比](#flask-vs-fastapi-部署對比)
- [詳細文檔](#詳細文檔)
  - [服務器部署 (Gunicorn → Uvicorn/Hypercorn)](./server.md)
  - [Docker 容器化](./docker.md)
  - [Kubernetes 編排](./kubernetes.md)
  - [環境變數管理](./environment.md)
  - [監控與日誌](./monitoring.md)
  - [生產環境最佳實踐](./production-best-practices.md)

## 概述

從 Flask 遷移到 FastAPI 不僅僅是程式碼的改變，更重要的是部署方式的現代化。FastAPI 基於 ASGI，提供了比 WSGI 更強大的非同步處理能力，這在生產環境中可以帶來顯著的效能提升。

### 核心改變

| 方面 | Flask 傳統部署 | FastAPI 現代部署 |
|------|--------------|----------------|
| **服務器** | Gunicorn (WSGI) | Uvicorn/Hypercorn (ASGI) |
| **部署方式** | 傳統 VM + 手動配置 | 容器化 + 編排 |
| **擴展策略** | 垂直擴展為主 | 水平擴展優先 |
| **監控方式** | 手動日誌分析 | 自動化監控與告警 |
| **配置管理** | 環境變數散亂 | 統一配置管理 |
| **健康檢查** | 簡單 HTTP 檢查 | 完整的健康檢查端點 |

### 學習目標

完成本章後，你將能夠：

1. ✅ 理解 WSGI 與 ASGI 在部署上的差異
2. ✅ 掌握 Uvicorn 和 Hypercorn 的配置與優化
3. ✅ 使用 Docker 容器化 FastAPI 應用
4. ✅ 在 Kubernetes 上部署和擴展應用
5. ✅ 管理不同環境的配置和機密資訊
6. ✅ 設置完整的監控和日誌系統
7. ✅ 實現生產級的健康檢查和自動擴展

## 部署決策樹

根據你的需求和資源，選擇最適合的部署方式：

```
你的應用規模如何？
├─ 小型專案（< 10 併發用戶）
│   ├─ 是否需要簡單部署？
│   │   ├─ 是 → ✅ Uvicorn 單體部署
│   │   └─ 否 → ✅ Docker 容器化
│   └─ 是否需要隔離環境？
│       ├─ 是 → ✅ Docker Compose
│       └─ 否 → ✅ 傳統 VPS 部署
│
├─ 中型專案（10-1000 併發用戶）
│   ├─ 是否有容器化經驗？
│   │   ├─ 是 → ✅ Docker + 反向代理（Nginx）
│   │   └─ 否 → ✅ Uvicorn + Gunicorn（學習過渡）
│   └─ 是否需要自動擴展？
│       ├─ 是 → ✅ Kubernetes 基礎部署
│       └─ 否 → ✅ Docker Swarm 或單機 Docker
│
└─ 大型專案（> 1000 併發用戶）
    ├─ 是否需要高可用性？
    │   ├─ 是 → ✅ Kubernetes + HPA + 多區域部署
    │   └─ 否 → ✅ Kubernetes 單集群部署
    ├─ 是否需要微服務架構？
    │   ├─ 是 → ✅ Kubernetes + Service Mesh (Istio)
    │   └─ 否 → ✅ Kubernetes + 單體應用
    └─ 雲端服務商？
        ├─ AWS → ✅ EKS + ALB
        ├─ GCP → ✅ GKE + Cloud Load Balancing
        └─ Azure → ✅ AKS + Azure Load Balancer
```

### 部署策略對比

| 部署方式 | 適用規模 | 複雜度 | 擴展能力 | 維護成本 | 推薦場景 |
|---------|---------|--------|---------|---------|---------|
| **Uvicorn 單體** | 小型 | ⭐ 簡單 | ⭐⭐ 有限 | ⭐ 低 | 開發、測試、小型專案 |
| **Uvicorn + Gunicorn** | 中小型 | ⭐⭐ 中等 | ⭐⭐⭐ 中等 | ⭐⭐ 中低 | 過渡期、傳統伺服器 |
| **Docker Compose** | 中小型 | ⭐⭐ 中等 | ⭐⭐⭐ 中等 | ⭐⭐ 中低 | 本地開發、小型生產 |
| **Docker + Nginx** | 中小型 | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐ 良好 | ⭐⭐⭐ 中等 | 傳統 VPS、單機生產 |
| **Kubernetes** | 中大型 | ⭐⭐⭐⭐ 較高 | ⭐⭐⭐⭐⭐ 優秀 | ⭐⭐⭐⭐ 較高 | 生產環境、微服務 |
| **K8s + HPA** | 大型 | ⭐⭐⭐⭐⭐ 高 | ⭐⭐⭐⭐⭐ 極佳 | ⭐⭐⭐⭐⭐ 高 | 大規模生產、雲端 |

## Flask vs FastAPI 部署對比

### 服務器層面對比

| 特性 | Flask + Gunicorn | FastAPI + Uvicorn | 優勢 |
|------|----------------|-------------------|------|
| **協議標準** | WSGI | ASGI | FastAPI 支援 HTTP/2、WebSocket |
| **併發模型** | 多進程/多線程 | 異步事件循環 | FastAPI 更高效能 |
| **連接數** | 受限於 worker 數 | 數千併發連接 | FastAPI 可處理更多請求 |
| **記憶體使用** | 每個 worker 獨立記憶體 | 共享事件循環 | FastAPI 更省記憶體 |
| **啟動時間** | 較慢（多進程） | 較快（單進程） | FastAPI 啟動更快 |
| **熱重載** | 支援 | 支援 | 兩者都支援 |
| **SSL/TLS** | 需反向代理 | 原生支援 | FastAPI 可直連 HTTPS |

### 部署架構對比

**Flask 傳統架構：**
```
Internet
  ↓
Nginx (反向代理 + SSL)
  ↓
Gunicorn (WSGI 服務器)
  ├─ Worker 1 (進程)
  ├─ Worker 2 (進程)
  └─ Worker N (進程)
  ↓
Flask 應用
```

**FastAPI 現代架構：**
```
Internet
  ↓
Nginx (反向代理 + SSL) [可選]
  ↓
Uvicorn (ASGI 服務器)
  ├─ 主事件循環 (單進程)
  └─ 多協程處理請求
  ↓
FastAPI 應用
```

### 效能對比

| 指標 | Flask + Gunicorn | FastAPI + Uvicorn | 提升 |
|------|----------------|-------------------|------|
| **RPS (簡單 API)** | ~10,000 | ~40,000+ | **4x** |
| **併發連接** | 受 worker 限制 | 數千連接 | **10x+** |
| **記憶體使用** | 每 worker ~50MB | 總共 ~100MB | **減少 50%+** |
| **延遲 (P99)** | ~10ms | ~2.5ms | **4x** |

*測試環境：4 核 CPU，簡單 JSON API，1000 併發請求*

### 配置複雜度對比

**Flask + Gunicorn 配置：**
```bash
# gunicorn_config.py
workers = 4
worker_class = 'sync'
bind = '0.0.0.0:8000'
timeout = 30
```

**FastAPI + Uvicorn 配置：**
```bash
# 更簡單的配置
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
# 或使用配置文件
uvicorn main:app --config uvicorn.json
```

FastAPI 配置更簡單，因為 ASGI 原生支援異步，不需要複雜的 worker 配置。

## 詳細文檔

### [1. 服務器部署：Gunicorn → Uvicorn/Hypercorn](./server.md)
深入學習如何從 Gunicorn (WSGI) 遷移到 Uvicorn/Hypercorn (ASGI)，包含：
- WSGI vs ASGI 部署差異
- Uvicorn 配置與優化
- Hypercorn 替代方案
- 多種部署方式對比
- 效能調優技巧

### [2. Docker 容器化](./docker.md)
掌握 FastAPI 應用的容器化策略，包含：
- Flask vs FastAPI Dockerfile 對比
- 多階段構建優化
- Docker Compose 配置
- 生產環境 Docker 最佳實踐
- 健康檢查與自動重啟

### [3. Kubernetes 編排](./kubernetes.md)
學習如何在 Kubernetes 上部署和管理 FastAPI 應用，包含：
- Deployment 和 Service 配置
- ConfigMap 和 Secret 管理
- Horizontal Pod Autoscaler (HPA) 設置
- Liveness 和 Readiness Probes
- 滾動更新與回滾策略

### [4. 環境變數管理](./environment.md)
了解生產環境的配置管理策略，包含：
- Pydantic Settings 配置類別
- 12-Factor App 原則
- 不同環境的配置策略
- 機密資訊管理 (Vault, K8s Secrets)
- 配置驗證與最佳實踐

### [5. 監控與日誌](./monitoring.md)
建立完整的監控和日誌系統，包含：
- Prometheus 指標收集
- Grafana 儀表板設置
- 結構化日誌 (JSON)
- 健康檢查端點實現
- 告警規則配置
- APM 工具整合

### [6. 生產環境最佳實踐](./production-best-practices.md)
掌握生產環境的全面最佳實踐，包含：
- 生產就緒檢查清單
- 安全性最佳實踐
- 效能優化策略
- 資料庫連接池配置
- 快取策略
- 零停機部署
- 災難恢復計劃

## 常見問題

### Q: 我應該選擇 Uvicorn 還是 Hypercorn？
**A:** Uvicorn 更成熟且使用更廣泛，建議優先選擇。Hypercorn 適合需要 HTTP/2 或更進階功能的場景。

### Q: 生產環境一定要用 Docker 嗎？
**A:** 不是必須的，但 Docker 提供了更好的隔離性、可移植性和部署一致性，強烈建議使用。

### Q: 小型專案也需要 Kubernetes 嗎？
**A:** 不需要。Kubernetes 適合中大型專案。小型專案使用 Docker Compose 或簡單的 Uvicorn 部署即可。

### Q: 如何實現零停機部署？
**A:** 使用 Kubernetes 的滾動更新、藍綠部署或金絲雀部署策略。詳見 [Kubernetes 編排](./kubernetes.md)。

### Q: FastAPI 的效能真的比 Flask 好嗎？
**A:** 在 I/O 密集型場景下，FastAPI 的異步處理能力可以帶來 2-4 倍的效能提升。但在 CPU 密集型任務中差異不大。


## 參考資源

- [FastAPI - Deployment](https://fastapi.tiangolo.com/deployment/)
- [Uvicorn Documentation](https://www.uvicorn.org/)
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

