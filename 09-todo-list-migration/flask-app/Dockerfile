FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴文件
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 創建日誌目錄
RUN mkdir -p logs

# 設置環境變數
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# 暴露端口
EXPOSE 5000

# 使用 Gunicorn 啟動應用
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "--timeout", "120", "app:app"]

