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



## 📝 授權

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 文件

---

⭐ 如果這個專案對你有幫助，歡迎給個星星！



