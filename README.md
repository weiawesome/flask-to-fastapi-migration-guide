# Flask to FastAPI Migration Guide

> 一個完整的 Flask 轉換到 FastAPI 的實戰教學指南

## 📚 關於本專案

這是一個系統化的教學專案，旨在幫助開發者從 Flask 遷移到 FastAPI。透過循序漸進的教學和實際範例，讓你掌握 FastAPI 的核心概念與最佳實踐。

本專案使用 AI 協助彙整資料與整理內容，確保資訊的完整性與實用性。

## 📖 教學目錄

### [00 - 為什麼要從 Flask 遷移到 FastAPI？](./00-why-migrate/)
深入分析 Flask 與 FastAPI 的核心差異，包含：
- 框架背景與設計理念比較
- 核心特性與功能對比
- 效能基準測試與分析
- 開發體驗與工具支援
- 生態系統與第三方整合
- 適用場景分析與決策指南
- 遷移評估檢查清單

### [01 - FastAPI 基礎入門](./01-start-fastapi/)
從零開始建立你的第一個 FastAPI 應用，體驗自動文檔生成的強大功能：
- 使用 `uv` 快速建立專案環境
- 安裝 FastAPI 與 Uvicorn 依賴
- 撰寫第一個 FastAPI 應用程式
- OpenAPI 文檔配置與自訂
- 啟動應用的多種方式
- **自動生成的 API 文檔**（Swagger UI / ReDoc）
- Flask vs FastAPI 基本語法對比
- 體驗「寫完程式碼 = 完成文檔」的開發流程

### [02 - 路由與請求處理轉換](./02-routing-and-requests/)
學習如何將 Flask 的路由系統轉換為 FastAPI，並採用 Layered Architecture 設計：
- **Layered Architecture**（分層架構）設計模式
- **APIRouter** 組織和模組化路由
- 路徑參數、查詢參數、請求體的處理方式
- `request.args` → 查詢參數自動解析與驗證
- `request.json` → Pydantic 模型自動驗證
- 回應模型與自訂狀態碼
- **Repository 模式**（資料存取層，目前用記憶體）
- 簡單的依賴注入（Repository 注入）
- Flask Blueprint vs FastAPI APIRouter 完整對比
- 完整的使用者 CRUD 範例（增刪查改）

### [03 - 中間件與錯誤處理](./03-middleware/)
掌握 FastAPI 的中間件系統和統一錯誤處理：
- Flask `before_request` / `after_request` → FastAPI 中間件
- **自定義中間件**（日誌、計時、請求追踪）
- **CORS 跨域設定**（Flask-CORS → CORSMiddleware）
- **統一錯誤處理**（類似 Flask `@app.errorhandler()`）
- 自定義異常類別
- 日誌系統整合與配置
- **效能監控**與指標收集
- 請求追踪（Request ID）
- 中間件執行順序與最佳實踐

### [04 - 認證系統](./04-authenication/)
實現完整的 JWT 認證系統，學習 FastAPI 的認證最佳實踐：
- **JWT Token 創建與驗證**（使用 python-jose）
- **密碼加密**（bcrypt 安全加密）
- **三層架構設計**（Utils → Middleware → Router）
- **認證中間件**（JWT 驗證與 ContextVar 線程安全）
- **依賴注入模式**（`Depends(get_current_user)` 保護路由）
- **用戶註冊與登入**（完整的認證流程）
- **Swagger 文檔整合**（HTTPBearer 自動顯示認證選項）
- Flask-Login / Flask-JWT → FastAPI 認證系統轉換
- 職責分離架構設計原則
- 安全考量與生產環境建議

### [05 - SQLAlchemy ORM 資料庫整合](./05-sql-alchemy/)
從記憶體儲存遷移到真實資料庫，學習 SQLAlchemy ORM 框架的核心概念：
- **SQLAlchemy 基礎導入與配置**（Engine、Session、Base）
- **ORM 模型定義**（Declarative Base、Column 定義）
- **資料庫連接與 Session 管理**（依賴注入模式）
- **Repository 模式與 SQLAlchemy 整合**（CRUD 操作）
- **依賴注入資料庫 Session**（`get_db()` 函數）
- **SQLite 資料庫初始化**（自動創建資料表）
- **SQLAlchemy 查詢語法**（filter、order_by、分頁）
- Flask-SQLAlchemy → FastAPI + SQLAlchemy 轉換
- 資料庫無關設計（輕鬆切換 SQLite → PostgreSQL）
- 生產環境最佳實踐

### [06 - 異步編程實戰](./06-async-function/)
深入理解 FastAPI 的核心優勢：異步編程，學習何時使用異步以及如何正確使用：
- **async/await 基礎概念與語法**（異步函數定義與調用）
- **三種異步模式對比**（`await` 順序執行 vs `asyncio.gather` 並發執行 vs Celery 完全異步）
- **何時該用異步、何時不該用**（I/O 密集型 vs CPU 密集型）
- **`asyncio.gather` 並發執行**（多個獨立操作的並發處理）
- **背景任務處理**（FastAPI BackgroundTasks 與 Celery 分散式任務佇列）
- **Celery 配置與使用**（Redis 作為訊息佇列、任務狀態查詢）
- **異步 I/O 操作**（資料庫、HTTP 請求、檔案 I/O、Redis）
- **錯誤處理與最佳實踐**（異步程式碼的錯誤處理模式）
- 協程（coroutines）vs 線程（threads）概念澄清
- 實戰範例與效能優化建議

### [07 - 測試框架](./07-test-framework/)
掌握 FastAPI 測試的最佳實踐，從 Flask 測試方式遷移到 FastAPI，建立完整的測試策略：
- **Flask test_client → FastAPI TestClient** 完整對比與遷移指南
- **異步測試設定**（pytest-asyncio、AsyncClient 使用）
- **依賴覆寫在測試中的應用**（覆寫 Repository、Service 依賴）
- **Mock Service 依賴**（Service 層相互依賴設計，便於測試中 Mock）
- **測試覆蓋率自動計算**（pytest-cov 配置，達到 100% 覆蓋率）⭐
- **完整架構示例**（Router → Service → Repository → Memory）
- **測試組織方式**（獨立 `tests/` 目錄，Python 社區標準做法）
- **測試 Fixtures 與共享配置**（conftest.py 最佳實踐）
- **CI/CD 整合**（GitHub Actions 自動測試配置）
- Flask 與 FastAPI 測試差異詳解與實戰範例

### [08 - WebSocket 與實時通訊](./08-realtime-websocket/)
從 Flask-SocketIO 遷移到 FastAPI 原生的 WebSocket 支援，建立完整的實時通訊系統：
- **Flask-SocketIO → FastAPI WebSocket** 完整遷移對比與差異分析
- **WebSocket 基礎概念與語法**（連接、接收、發送訊息）
- **連接管理（ConnectionManager）**（追蹤所有活躍連接、用戶識別）
- **訊息廣播機制**（一對多廣播，包括發送者自己）⭐
- **點對點私訊功能**（用戶名識別與定向發送）
- **心跳檢測 (Heartbeat)** - 必須自己實現，FastAPI 沒有內建 ⭐
- **前端 HTML/JavaScript 整合**（完整的聊天室範例）
- **消息顯示樣式**（自己的消息顯示在右側，別人的在左側）⭐
- **超時檢測與自動清理**（30 秒無活動自動斷開連接）
- **雙向心跳機制**（服務器 ping/pong + 客戶端 heartbeat/heartbeat_ack）
- 生產環境最佳實踐（Redis 多服務器廣播、認證、速率限制）

### [09 - 實戰案例：TO-DO List API 完整遷移](./09-todo-list-migration/)
完整的生產級實戰案例，展示如何將一個完整的 Flask 應用遷移到 FastAPI，包含完整的 TO-DO List API：
- **完整的 Flask 應用（同步架構）** vs **完整的 FastAPI 應用（異步架構）** 並行對比
- **分層架構設計**（Router → Service → Repository）完整實作
- **PostgreSQL 資料庫整合**（同步 SQLAlchemy vs 異步 SQLAlchemy + asyncpg）
- **Redis 快取策略**（解決快取雪崩、穿透、擊穿三大問題）⭐
- **JWT 認證系統**（用戶註冊、登入、登出，JWT 黑名單）
- **TO-DO List CRUD**（完整的增刪查改操作）
- **前端介面**（Nginx 靜態網站 + API 代理，可切換 Flask/FastAPI）⭐
- **Docker Compose 容器化部署**（一鍵啟動所有服務）
- **性能測試與對比**（k6 負載測試，驗證異步在高並發下的優勢）⭐
- **異步架構優勢分析**（並發量越大，優勢越明顯）⭐
- 生產環境最佳實踐（連接池優化、Redis 連接預初始化、監控建議）

### [10 - 部署與生產環境](./10-deployment/)
完整的生產環境部署指南，從傳統 WSGI 部署遷移到現代化的容器化與編排部署：
- **Gunicorn → Uvicorn/Hypercorn**（WSGI 到 ASGI 服務器遷移）
- **Docker 容器化**（多階段構建、最佳實踐、健康檢查）
- **Kubernetes 編排**（Deployment、Service、ConfigMap、Secret 管理）
- **Horizontal Pod Autoscaler (HPA)**（自動擴縮容配置）⭐
- **環境變數管理**（Pydantic Settings、12-Factor App、機密資訊管理）
- **健康檢查端點**（Liveness、Readiness、Startup Probes）
- **監控與日誌**（Prometheus 指標收集、Grafana 儀表板、結構化日誌）
- **生產環境最佳實踐**（安全性、效能優化、可靠性設計、災難恢復）
- 部署決策樹（根據規模選擇最適合的部署方式）
- Flask vs FastAPI 部署架構對比與遷移指南

## 📝 授權

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 文件

---

⭐ 如果這個專案對你有幫助，歡迎給個星星！



