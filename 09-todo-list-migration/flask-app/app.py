"""
Flask Application
Flask 應用程式入口
"""
import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 導入模組
# 注意：必須先導入 models 以確保表定義被註冊
from models import User, Todo  # noqa: F401
from database import init_db
from blueprints import auth_bp, todos_bp
from core.error_handlers import register_error_handlers
from middleware.jwt_middleware import jwt_middleware

# 創建 Flask 應用
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'secret-key')

# CORS 設定
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 註冊錯誤處理器
register_error_handlers(app)

# 註冊 JWT 中間件
jwt_middleware(app)

# 註冊 Blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(todos_bp)

# 初始化資料庫（在導入所有 models 之後）
init_db()


@app.route('/')
def index():
    """根路徑"""
    return {
        "message": "Flask TO-DO List API",
        "version": "v1",
        "docs": "Use /api/v1/auth/* and /api/v1/todos/* endpoints"
    }


@app.route('/health')
def health():
    """健康檢查"""
    return {"status": "healthy"}, 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

