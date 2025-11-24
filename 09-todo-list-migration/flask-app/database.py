"""
Database Configuration
SQLAlchemy 資料庫配置 (同步版本)
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# PostgreSQL 資料庫 URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://todo_user:todo_password@localhost:5432/todo_db"
)

# 創建 SQLAlchemy engine
# 優化：增加連接池大小以支持高並發（100-500 用戶）
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 檢查連接是否有效
    pool_size=50,        # 增加基礎連接數（從 10 增加到 50）
    max_overflow=100,     # 增加最大溢出連接數（從 20 增加到 100）
    pool_timeout=30,      # 連接超時時間（秒）
    echo=False
)

# 創建 SessionLocal 類別
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 創建 Base 類別
Base = declarative_base()


def get_db():
    """
    獲取資料庫 session 的依賴注入函數
    
    使用方式：
    db = next(get_db())
    try:
        # 使用 db session
        pass
    finally:
        db.close()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化資料庫（創建所有表）
    在應用啟動時調用
    """
    # 導入 models 以確保所有表定義都被註冊到 Base.metadata
    from models import User, Todo
    Base.metadata.create_all(bind=engine)

