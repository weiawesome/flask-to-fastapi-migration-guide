"""
Database Configuration
SQLAlchemy 資料庫配置 (異步版本)
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os

# PostgreSQL 資料庫 URL (異步)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://todo_user:todo_password@localhost:5432/todo_db"
)

# 創建異步 SQLAlchemy engine
# 優化：增加連接池大小以支持高並發（100-500 用戶）
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=50,        # 增加基礎連接數（從 10 增加到 50）
    max_overflow=100,    # 增加最大溢出連接數（從 20 增加到 100）
    pool_timeout=30,     # 連接超時時間（秒）
    echo=False
)

# 創建 AsyncSessionLocal 類別
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 創建 Base 類別
Base = declarative_base()


async def get_db():
    """
    獲取資料庫 session 的依賴注入函數（異步）
    
    使用方式：
    @router.get("/users")
    async def get_users(db: AsyncSession = Depends(get_db)):
        # 使用 db session
        pass
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    初始化資料庫（創建所有表）
    在應用啟動時調用
    """
    async with engine.begin() as conn:
        from models import User, Todo
        await conn.run_sync(Base.metadata.create_all)

