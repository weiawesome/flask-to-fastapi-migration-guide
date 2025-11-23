# 05 - SQLAlchemy ORM 資料庫整合

## 本章學習重點

本章重點學習 **SQLAlchemy ORM 框架**，這是 Python 中最流行的 ORM（Object-Relational Mapping）框架。我們將學習如何從記憶體儲存遷移到真實的資料庫，並展示 SQLAlchemy 的核心概念與最佳實踐。

✅ **已包含的內容：**
- SQLAlchemy 基礎導入與配置
- ORM 模型定義（Declarative Base）
- 資料庫連接與 Session 管理
- Repository 模式與 SQLAlchemy 整合
- 依賴注入資料庫 Session
- SQLite 資料庫初始化
- Flask-SQLAlchemy → FastAPI + SQLAlchemy 轉換

## 目錄

- [專案結構](#專案結構)
- [SQLAlchemy 核心概念](#sqlalchemy-核心概念)
- [資料庫配置 (database.py)](#資料庫配置-databasepy)
- [ORM 模型定義 (models.py)](#orm-模型定義-modelspy)
- [Repository 模式與 SQLAlchemy](#repository-模式與-sqlalchemy)
- [依賴注入資料庫 Session](#依賴注入資料庫-session)
- [Flask vs FastAPI 對比](#flask-vs-fastapi-對比)
- [使用方式](#使用方式)
- [常見問題](#常見問題)

## 專案結構

```
05-sql-alchemy/
├── main.py                    # 應用程式入口（包含資料庫初始化）
├── database.py                # SQLAlchemy 資料庫配置 ⭐
├── models.py                  # ORM 模型定義 ⭐
├── core/                      # 核心模組
│   ├── __init__.py
│   ├── exceptions.py
│   └── error_handlers.py
├── middleware/               # 中間件層
│   ├── __init__.py
│   ├── logging_middleware.py
│   ├── timing_middleware.py
│   ├── request_id_middleware.py
│   └── jwt_middleware.py
├── utils/                    # 共用工具
│   ├── __init__.py
│   ├── logger.py
│   ├── metrics.py
│   └── jwt.py
├── routers/                  # 路由層
│   ├── __init__.py
│   ├── users.py
│   └── auth.py
├── schemas/                  # Pydantic 模型
│   ├── __init__.py
│   ├── user.py
│   └── auth.py
├── repositories/             # 資料存取層（使用 SQLAlchemy）⭐
│   ├── __init__.py
│   ├── user_repository.py
│   └── auth_repository.py
└── README.md
```

## SQLAlchemy 核心概念

### 什麼是 SQLAlchemy？

SQLAlchemy 是 Python 中最流行的 **ORM（Object-Relational Mapping）框架**，它允許你：

1. **用 Python 類別定義資料表結構**（而不是寫 SQL）
2. **用 Python 物件操作資料**（而不是寫 SQL 語句）
3. **自動處理資料庫連接和事務管理**

### 為什麼使用 SQLAlchemy？

| 優點 | 說明 |
|------|------|
| **類型安全** | 使用 Python 類型提示，IDE 可以自動補全 |
| **資料庫無關** | 可以輕鬆切換不同的資料庫（SQLite → PostgreSQL） |
| **自動遷移** | 可以使用 Alembic 進行資料庫版本控制 |
| **關係映射** | 輕鬆處理表之間的關係（一對多、多對多） |
| **查詢構建** | 使用 Python 語法構建複雜查詢 |

### SQLAlchemy 核心組件

```
┌─────────────────────────────────────────┐
│         Engine (資料庫引擎)              │
│  - 管理資料庫連接                        │
│  - 執行 SQL 語句                         │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│      Session (會話管理)                  │
│  - 管理物件狀態                          │
│  - 處理事務（Transaction）              │
│  - 快取查詢結果                          │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│      ORM Models (模型定義)               │
│  - 定義資料表結構                        │
│  - 映射 Python 類別到資料表              │
└─────────────────────────────────────────┘
```

## 資料庫配置 (database.py)

**檔案：`database.py`**

這是 SQLAlchemy 的核心配置文件，定義了資料庫連接、Session 管理和 Base 類別。

### 核心導入

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
```

**學習重點：**

1. **`create_engine`**：創建資料庫引擎，管理連接池
2. **`declarative_base`**：創建 Base 類別，所有 ORM 模型都繼承它
3. **`sessionmaker`**：創建 Session 工廠，用於依賴注入

### 完整實現

```python
# database.py
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
```

### 關鍵概念解釋

#### 1. Engine（引擎）

```python
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 專用
    echo=False  # 設為 True 可以看到所有 SQL 語句
)
```

- **作用**：管理資料庫連接池
- **`connect_args`**：SQLite 需要 `check_same_thread=False`（因為 SQLite 預設不允許多線程）
- **`echo=True`**：開發時很有用，可以看到所有執行的 SQL 語句

#### 2. SessionLocal（Session 工廠）

```python
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

**⚠️ 重要：這不是用戶登入的 Session！**

SQLAlchemy 的 `sessionmaker` 和用戶登入的 "session" 是**完全不同的概念**：

| SQLAlchemy Session | 用戶登入 Session |
|-------------------|----------------|
| 用於資料庫操作（查詢、插入、更新） | 用於存儲用戶認證狀態 |
| 每個 HTTP 請求一個 | 跨多個 HTTP 請求 |
| 請求結束後自動關閉 | 持續到用戶登出 |
| 生命週期：幾毫秒到幾秒 | 生命週期：數小時到數天 |

**`sessionmaker` 的作用：**
- **工廠函數**：用於創建資料庫 Session 的模板
- **統一配置**：一次性設定，之後每次創建 Session 都使用相同配置
- **線程安全**：每個請求都有獨立的 Session，不會互相干擾

**參數說明：**
- **`autocommit=False`**：需要手動 commit（更安全）
- **`autoflush=False`**：需要手動 flush（更可控）
- **`bind=engine`**：綁定到特定的 engine

**使用方式：**
```python
# 創建 Session 工廠
SessionLocal = sessionmaker(bind=engine)

# 每次需要時創建新的 Session
db = SessionLocal()  # 創建一個新的資料庫會話
# ... 使用 db 進行資料庫操作 ...
db.close()  # 關閉 Session
```

#### 3. Base（基礎類別）

```python
Base = declarative_base()
```

- **作用**：所有 ORM 模型都繼承這個 Base
- **好處**：自動註冊模型，可以用 `Base.metadata.create_all()` 創建所有表

#### 4. get_db()（依賴注入函數）

```python
def get_db():
    db = SessionLocal()
    try:
        yield db  # 提供 session
    finally:
        db.close()  # 確保關閉連接
```

- **`yield`**：使用生成器模式，確保 session 在使用後自動關閉
- **FastAPI 依賴注入**：FastAPI 會自動調用這個函數並管理 session 生命週期

## ORM 模型定義 (models.py)

**檔案：`models.py`**

使用 SQLAlchemy 的 Declarative 模式定義資料表結構。

### 核心導入

```python
# models.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base
```

**學習重點：**

1. **`Column`**：定義資料表的欄位
2. **`Integer, String, DateTime`**：資料類型
3. **`func`**：SQL 函數（如 `func.now()`）
4. **`Base`**：從 `database.py` 導入的基礎類別

### 完整實現

```python
# models.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base


class User(Base):
    """
    使用者模型
    對應到 users 表
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def to_dict(self):
        """轉換為字典（不包含密碼）"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "created_at": self.created_at
        }


class AuthUser(Base):
    """
    認證使用者模型
    對應到 auth_users 表
    """
    __tablename__ = "auth_users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)  # bcrypt 加密後的密碼
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def to_dict(self):
        """轉換為字典"""
        return {
            "id": self.id,
            "email": self.email,
            "created_at": self.created_at
        }
```

### 關鍵概念解釋

#### 1. 繼承 Base

```python
class User(Base):
    __tablename__ = "users"
```

- **必須繼承 `Base`**：這樣 SQLAlchemy 才能識別這個模型
- **`__tablename__`**：指定資料表名稱（如果不指定，會使用類別名稱的小寫）

#### 2. Column 定義

```python
id = Column(Integer, primary_key=True, index=True)
username = Column(String(50), unique=True, index=True, nullable=False)
```

**常用參數：**

| 參數 | 說明 | 範例 |
|------|------|------|
| `primary_key=True` | 主鍵 | `id = Column(Integer, primary_key=True)` |
| `index=True` | 創建索引（加速查詢） | `username = Column(String(50), index=True)` |
| `unique=True` | 唯一約束 | `email = Column(String(255), unique=True)` |
| `nullable=False` | 不允許 NULL | `username = Column(String(50), nullable=False)` |
| `server_default` | 資料庫層面的預設值 | `created_at = Column(DateTime, server_default=func.now())` |

#### 3. 資料類型

```python
Column(Integer)        # 整數
Column(String(50))     # 字串（最大長度 50）
Column(DateTime)       # 日期時間
Column(Boolean)        # 布林值
Column(Float)          # 浮點數
Column(Text)           # 長文字
```

#### 4. 自動時間戳記

```python
created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

- **`timezone=True`**：包含時區資訊
- **`server_default=func.now()`**：資料庫自動設置當前時間（不需要 Python 代碼設置）

## Repository 模式與 SQLAlchemy

**檔案：`repositories/user_repository.py`**

Repository 模式封裝了資料存取邏輯，使用 SQLAlchemy Session 進行資料庫操作。

### 核心導入

```python
# repositories/user_repository.py
from typing import Optional, List
from fastapi import Depends
from sqlalchemy.orm import Session

from models import User
from database import get_db
```

**學習重點：**

1. **`Session`**：SQLAlchemy 的 Session 類型（用於類型提示）
2. **`Depends(get_db)`**：FastAPI 依賴注入，自動提供 Session

### 完整實現範例

```python
# repositories/user_repository.py
from typing import Optional, List
from fastapi import Depends
from sqlalchemy.orm import Session

from models import User
from database import get_db


class UserRepository:
    """
    使用者資料存取層
    使用 SQLAlchemy ORM 與資料庫互動
    """
    
    def __init__(self, db: Session):
        """初始化 Repository"""
        self.db = db
    
    def create(self, username: str, email: str, password: str, full_name: Optional[str] = None) -> User:
        """建立新使用者"""
        user = User(
            username=username,
            email=email,
            password=password,
            full_name=full_name
        )
        self.db.add(user)           # 添加到 session
        self.db.commit()            # 提交事務
        self.db.refresh(user)       # 刷新物件（獲取自動生成的 id）
        return user
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """根據 ID 獲取使用者"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """根據 email 獲取使用者"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """獲取所有使用者（支援分頁）"""
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def update(self, user_id: int, **kwargs) -> Optional[User]:
        """更新使用者資料"""
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        # 更新欄位
        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete(self, user_id: int) -> bool:
        """刪除使用者"""
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        return True


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """
    獲取 UserRepository 實例
    這是一個依賴注入函數，FastAPI 會自動調用
    """
    return UserRepository(db)
```

### SQLAlchemy 查詢語法

#### 1. 基本查詢

```python
# 查詢所有
users = db.query(User).all()

# 查詢單一（根據 ID）
user = db.query(User).filter(User.id == user_id).first()

# 查詢單一（根據條件）
user = db.query(User).filter(User.email == email).first()
```

#### 2. 過濾條件

```python
# 等於
db.query(User).filter(User.email == email)

# 不等於
db.query(User).filter(User.email != email)

# 包含（LIKE）
db.query(User).filter(User.email.like("%@example.com"))

# IN
db.query(User).filter(User.id.in_([1, 2, 3]))

# AND
db.query(User).filter(User.email == email, User.active == True)

# OR
from sqlalchemy import or_
db.query(User).filter(or_(User.email == email, User.username == username))
```

#### 3. 分頁

```python
# offset 和 limit
users = db.query(User).offset(skip).limit(limit).all()
```

#### 4. 排序

```python
# 升序
users = db.query(User).order_by(User.created_at).all()

# 降序
users = db.query(User).order_by(User.created_at.desc()).all()
```

#### 5. 計數

```python
count = db.query(User).count()
```

### CRUD 操作模式

#### Create（創建）

```python
user = User(username="john", email="john@example.com")
db.add(user)        # 添加到 session
db.commit()        # 提交事務
db.refresh(user)   # 刷新物件（獲取自動生成的 id）
```

#### Read（讀取）

```python
# 根據 ID
user = db.query(User).filter(User.id == user_id).first()

# 根據條件
user = db.query(User).filter(User.email == email).first()

# 所有
users = db.query(User).all()
```

#### Update（更新）

```python
user = db.query(User).filter(User.id == user_id).first()
user.username = "new_username"
db.commit()
db.refresh(user)
```

#### Delete（刪除）

```python
user = db.query(User).filter(User.id == user_id).first()
db.delete(user)
db.commit()
```

## 依賴注入資料庫 Session

### 在 Repository 中使用

```python
# repositories/user_repository.py
def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """依賴注入函數"""
    return UserRepository(db)
```

### 在 Router 中使用

```python
# routers/users.py
from repositories.user_repository import UserRepository, get_user_repository

@router.get("/users")
def get_users(
    repo: UserRepository = Depends(get_user_repository)
):
    """獲取使用者列表"""
    users = repo.get_all()
    return [user.to_dict() for user in users]
```

**工作流程：**

```
1. FastAPI 調用 get_user_repository()
   ↓
2. get_user_repository() 調用 Depends(get_db)
   ↓
3. get_db() 創建 SessionLocal() 實例
   ↓
4. 提供 Session 給 UserRepository
   ↓
5. 請求結束後，get_db() 的 finally 區塊關閉 Session
```

## Flask vs FastAPI 對比

### Flask-SQLAlchemy

```python
# Flask
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))

@app.route('/users')
def get_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])
```

### FastAPI + SQLAlchemy

```python
# FastAPI
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User

app = FastAPI()

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [u.to_dict() for u in users]
```

### 主要差異

| 特性 | Flask-SQLAlchemy | FastAPI + SQLAlchemy |
|------|------------------|---------------------|
| **配置** | `app.config['SQLALCHEMY_DATABASE_URI']` | 獨立的 `database.py` 文件 |
| **Base** | `db.Model` | `declarative_base()` |
| **查詢** | `User.query.all()` | `db.query(User).all()` |
| **Session** | 自動管理 | 手動管理（透過依賴注入） |
| **類型提示** | 不支援 | 完整支援（`Session` 類型） |

## 使用方式

### 1. 安裝依賴

```bash
cd 05-sql-alchemy
uv sync
```

### 2. 啟動應用

```bash
uv run uvicorn main:app --reload
```

應用啟動時會自動：
- 創建 `app.db` SQLite 資料庫文件
- 創建所有資料表（`users` 和 `auth_users`）

### 3. 查看資料庫

```bash
# 使用 sqlite3 命令行工具
sqlite3 app.db

# 查看所有表
.tables

# 查看表結構
.schema users

# 查看資料
SELECT * FROM users;
```

### 4. 測試 API

```bash
# 創建使用者
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "secret123",
    "full_name": "John Doe"
  }'

# 獲取使用者列表
curl http://localhost:8000/users

# 獲取單一使用者
curl http://localhost:8000/users/1
```

## 常見問題

### 1. 為什麼需要 `check_same_thread=False`？

SQLite 預設不允許多線程訪問同一個連接。FastAPI 是異步框架，需要這個設定。

```python
connect_args={"check_same_thread": False}
```

**注意：** 生產環境使用 PostgreSQL 或 MySQL 時不需要這個設定。

### 2. 什麼時候使用 `commit()`？

- **創建、更新、刪除**：需要 `commit()` 才能保存到資料庫
- **查詢**：不需要 `commit()`

```python
# 創建（需要 commit）
user = User(username="john")
db.add(user)
db.commit()  # ← 必須

# 查詢（不需要 commit）
users = db.query(User).all()  # ← 不需要 commit
```

### 3. 什麼時候使用 `refresh()`？

當你需要獲取資料庫自動生成的值（如 `id`、`created_at`）時：

```python
user = User(username="john")
db.add(user)
db.commit()
db.refresh(user)  # ← 獲取自動生成的 id 和 created_at
print(user.id)    # 現在可以訪問 id
```

### 4. 如何切換到 PostgreSQL？

只需要修改 `DATABASE_URL`：

```python
# database.py
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/dbname"
```

不需要修改其他代碼！這就是 SQLAlchemy 的優勢。

### 5. 如何查看執行的 SQL 語句？

設置 `echo=True`：

```python
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True  # ← 顯示所有 SQL 語句
)
```

## 總結

### 關鍵學習點

1. **SQLAlchemy 導入**：`create_engine`, `declarative_base`, `sessionmaker`
2. **ORM 模型**：繼承 `Base`，使用 `Column` 定義欄位
3. **Session 管理**：使用 `get_db()` 依賴注入函數
4. **查詢語法**：`db.query(Model).filter().all()`
5. **CRUD 操作**：`add()`, `commit()`, `refresh()`, `delete()`

### 架構優勢

✅ **資料庫無關**：可以輕鬆切換資料庫  
✅ **類型安全**：完整的類型提示支援  
✅ **自動管理**：Session 生命週期自動管理  
✅ **易於測試**：可以使用 mock Session  
✅ **生產就緒**：適合大型應用

## 參考資源

- [SQLAlchemy 官方文檔](https://docs.sqlalchemy.org/)
- [FastAPI - SQL Databases](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [SQLAlchemy ORM Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/orm_data_manipulation.html)
- [Alembic - 資料庫遷移工具](https://alembic.sqlalchemy.org/)
