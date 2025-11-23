"""
Database Configuration
SQLAlchemy 資料庫配置
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# SQLite 資料庫路徑
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./app.db"  # 預設使用 SQLite
)

# 創建 SQLAlchemy engine
# connect_args={"check_same_thread": False} 是 SQLite 專用的設定
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {},
    echo=False  # 設為 True 可以看到 SQL 語句（開發時很有用）
)

# 創建 SessionLocal 類別
# 這是用於依賴注入的 session 工廠
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 創建 Base 類別
# 所有 ORM 模型都會繼承這個 Base
Base = declarative_base()


def get_db():
    """
    獲取資料庫 session 的依賴注入函數
    
    使用方式：
    @router.get("/users")
    def get_users(db: Session = Depends(get_db)):
        # 使用 db session
        pass
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
    Base.metadata.create_all(bind=engine)

