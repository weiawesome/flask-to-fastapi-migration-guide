# 前端介面說明

## 概述

這是一個完整的 TO-DO List 前端應用，使用原生 HTML/CSS/JavaScript 開發，通過 Nginx 提供靜態文件服務，並代理後端 API 請求。

## 功能特性

- ✅ 用戶註冊/登入/登出
- ✅ 切換 Flask (v1) 和 FastAPI (v2) API
- ✅ TODO CRUD 操作（創建、讀取、更新、刪除）
- ✅ 標記完成/未完成
- ✅ 響應式設計（支援手機和桌面）
- ✅ 本地存儲 Token（刷新頁面不丟失登入狀態）

## 專案結構

```
frontend/
├── static/              # 靜態文件
│   ├── index.html       # 主頁面
│   ├── styles.css       # 樣式文件
│   └── app.js          # JavaScript 邏輯
├── nginx/              # Nginx 配置
│   └── nginx.conf      # Nginx 配置文件
└── README.md           # 本文件
```

## 使用方式

### 使用 Docker Compose（推薦）

```bash
# 在專案根目錄執行
docker-compose up -d

# 訪問前端
# http://localhost
```

### 本地開發（不使用 Docker）

如果需要本地開發前端：

1. **安裝 Nginx**（macOS）:
```bash
brew install nginx
```

2. **複製配置文件**:
```bash
sudo cp frontend/nginx/nginx.conf /usr/local/etc/nginx/servers/todo-frontend.conf
```

3. **修改配置文件中的代理地址**:
```nginx
# 將容器名稱改為 localhost
proxy_pass http://localhost:5000/api/v1/;  # Flask
proxy_pass http://localhost:8000/api/v2/;  # FastAPI
```

4. **啟動 Nginx**:
```bash
sudo nginx
```

5. **訪問前端**:
```
http://localhost
```

## API 切換

前端提供了一個 API 選擇器，可以在 Flask (v1) 和 FastAPI (v2) 之間切換：

- **Flask (v1)**: 同步架構，使用 `/api/v1/*` 端點
- **FastAPI (v2)**: 異步架構，使用 `/api/v2/*` 端點

切換 API 時，會顯示提示訊息，並且會使用對應的後端服務。

## 功能說明

### 認證流程

1. **註冊**: 輸入用戶名、郵件和密碼創建新帳號
2. **登入**: 使用郵件和密碼登入
3. **登出**: 清除本地 Token 並調用登出 API

### TODO 操作

1. **新增**: 輸入標題和描述（選填）創建新的待辦事項
2. **查看**: 自動載入當前用戶的所有待辦事項
3. **完成/未完成**: 點擊按鈕切換完成狀態
4. **刪除**: 點擊刪除按鈕（會確認後刪除）

## Nginx 配置說明

### 靜態文件服務

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

所有請求都會嘗試匹配靜態文件，如果不存在則返回 `index.html`（支援前端路由）。

### API 代理

```nginx
# Flask API
location /api/v1/ {
    proxy_pass http://flask-app:5000/api/v1/;
}

# FastAPI API
location /api/v2/ {
    proxy_pass http://fastapi-app:8000/api/v2/;
}
```

所有 `/api/v1/*` 請求會被代理到 Flask 應用，`/api/v2/*` 請求會被代理到 FastAPI 應用。

### CORS 處理

Nginx 配置中已經包含了 CORS headers，允許跨域請求。

## 瀏覽器相容性

- Chrome/Edge (最新版本)
- Firefox (最新版本)
- Safari (最新版本)
- 移動瀏覽器（iOS Safari, Chrome Mobile）

## 開發建議

### 本地開發（不使用 Docker）

如果需要在本地開發前端，可以：

1. 使用簡單的 HTTP 服務器：
```bash
cd frontend/static
python3 -m http.server 8080
```

2. 修改 `app.js` 中的 API 配置為完整 URL：
```javascript
const API_CONFIG = {
    flask: {
        baseUrl: 'http://localhost:5000/api/v1',
        name: 'Flask (v1) - 同步'
    },
    fastapi: {
        baseUrl: 'http://localhost:8000/api/v2',
        name: 'FastAPI (v2) - 異步'
    }
};
```

3. 注意 CORS：如果直接訪問 `file://` 協議，會遇到 CORS 問題，必須使用 HTTP 服務器。

## 故障排除

### 無法連接到 API

1. 檢查後端服務是否運行：
```bash
docker-compose ps
```

2. 檢查 Nginx 日誌：
```bash
docker-compose logs nginx
```

3. 檢查瀏覽器控制台的錯誤訊息

### Token 過期

如果 Token 過期，前端會自動清除本地存儲並返回登入頁面。用戶需要重新登入。

### API 切換不生效

確保瀏覽器沒有緩存舊的 JavaScript 文件。可以：
- 強制刷新（Ctrl+F5 或 Cmd+Shift+R）
- 清除瀏覽器緩存

