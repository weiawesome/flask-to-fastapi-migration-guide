# 環境變數管理

## 概述

正確管理環境變數和配置是生產環境部署的關鍵。本章將學習如何在 FastAPI 應用中管理配置，從 Flask 的配置方式遷移到現代化的配置管理策略。

## 目錄

- [Flask vs FastAPI 配置對比](#flask-vs-fastapi-配置對比)
- [Pydantic Settings](#pydantic-settings)
- [12-Factor App 原則](#12-factor-app-原則)
- [環境變數管理策略](#環境變數管理策略)
- [機密資訊管理](#機密資訊管理)
- [配置驗證](#配置驗證)
- [最佳實踐](#最佳實踐)

## Flask vs FastAPI 配置對比

### Flask 傳統配置方式

```python
# Flask config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

# app.py
from flask import Flask
app = Flask(__name__)
app.config.from_object('config.ProductionConfig')
```

**問題：**
- ❌ 缺乏型別驗證
- ❌ 默認值管理混亂
- ❌ 配置散亂在不同文件
- ❌ 難以追蹤配置來源

### FastAPI 現代配置方式

```python
# config.py
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # 應用配置
    app_name: str = "FastAPI App"
    debug: bool = Field(default=False, env="DEBUG")
    secret_key: str = Field(..., env="SECRET_KEY")  # 必需
    
    # 資料庫配置
    database_url: str = Field(..., env="DATABASE_URL")
    
    # Redis 配置
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()
```

**優勢：**
- ✅ 自動型別驗證和轉換
- ✅ 清晰的默認值
- ✅ 統一的配置管理
- ✅ 自動讀取 .env 文件
- ✅ 配置文檔自動生成

## Pydantic Settings

Pydantic Settings 是 FastAPI 推薦的配置管理方式，基於 Pydantic 模型提供強大的配置驗證和管理功能。

### 基礎配置類

```python
# config/settings.py
from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn, RedisDsn
from typing import Optional

class Settings(BaseSettings):
    # 應用基本配置
    app_name: str = Field(default="FastAPI App", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # 服務器配置
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # 安全配置
    secret_key: str = Field(..., env="SECRET_KEY")  # 必需，無默認值
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, 
        env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    # 資料庫配置
    database_url: PostgresDsn = Field(..., env="DATABASE_URL")
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(
        default=20, 
        env="DATABASE_MAX_OVERFLOW"
    )
    
    # Redis 配置
    redis_url: RedisDsn = Field(
        default="redis://localhost:6379", 
        env="REDIS_URL"
    )
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # CORS 配置
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
        env="CORS_ORIGINS"
    )
    
    # 日誌配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # 支持從多個環境變數前綴讀取
        env_prefix = ""  # 可設置為 "APP_"
        # 允許嵌套配置
        extra = "ignore"  # 忽略未定義的環境變數

# 創建全局設置實例
settings = Settings()
```

### 使用配置

```python
# main.py
from fastapi import FastAPI
from config.settings import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

@app.get("/")
async def root():
    return {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "version": settings.app_version
    }
```

### 多環境配置

```python
# config/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class BaseConfig(BaseSettings):
    """基礎配置"""
    app_name: str = "FastAPI App"
    secret_key: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

class DevelopmentConfig(BaseConfig):
    """開發環境配置"""
    environment: str = "development"
    debug: bool = True
    database_url: str = "postgresql://user:pass@localhost:5432/dev_db"
    
    model_config = SettingsConfigDict(env_file=".env.development")

class ProductionConfig(BaseConfig):
    """生產環境配置"""
    environment: str = "production"
    debug: bool = False
    database_url: str  # 必須從環境變數讀取
    
    model_config = SettingsConfigDict(env_file=".env.production")

class TestingConfig(BaseConfig):
    """測試環境配置"""
    environment: str = "testing"
    debug: bool = True
    database_url: str = "sqlite:///test.db"
    
    model_config = SettingsConfigDict(env_file=".env.testing")

def get_settings() -> BaseConfig:
    """根據環境變數返回對應的配置"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()

# 使用緩存確保單例
@lru_cache()
def get_settings_cached() -> BaseConfig:
    return get_settings()

settings = get_settings_cached()
```

### 嵌套配置

```python
# config/settings.py
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

class DatabaseConfig(BaseModel):
    url: str = Field(..., env="DATABASE_URL")
    pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    echo: bool = Field(default=False, env="DATABASE_ECHO")

class RedisConfig(BaseModel):
    url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    db: int = Field(default=0, env="REDIS_DB")

class Settings(BaseSettings):
    app_name: str = "FastAPI App"
    debug: bool = False
    
    # 嵌套配置
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"  # 支持 DATABASE__URL 格式

settings = Settings()
```

使用嵌套配置：

```bash
# .env
DATABASE__URL=postgresql://user:pass@localhost:5432/mydb
DATABASE__POOL_SIZE=20
REDIS__URL=redis://localhost:6379
REDIS__PASSWORD=mypassword
```

## 12-Factor App 原則

12-Factor App 是構建現代化應用的最佳實踐，其中配置管理是重要一環。

### 原則 3: 配置（Config）

**核心思想：** 將配置存儲在環境變數中，而不是代碼中。

**Flask 傳統方式（違反原則）：**
```python
# ❌ 配置硬編碼在代碼中
class Config:
    DATABASE_URL = "postgresql://localhost/mydb"
    SECRET_KEY = "hardcoded-secret-key"
```

**FastAPI 現代方式（符合原則）：**
```python
# ✅ 配置從環境變數讀取
class Settings(BaseSettings):
    database_url: str = Field(..., env="DATABASE_URL")
    secret_key: str = Field(..., env="SECRET_KEY")
```

### 配置分離實踐

**1. 應用配置（環境變數）**
```bash
# .env.development
ENVIRONMENT=development
DEBUG=True
DATABASE_URL=postgresql://localhost/dev_db
REDIS_URL=redis://localhost:6379
```

**2. 機密資訊（Secret 管理）**
```bash
# 不要提交到 Git
SECRET_KEY=your-secret-key-here
DATABASE_PASSWORD=your-database-password
API_KEY=your-api-key
```

**3. 環境特定配置（不同文件）**
```
.env.development
.env.staging
.env.production
```

## 環境變數管理策略

### 1. .env 文件管理

**開發環境 `.env.development`：**
```bash
# 應用配置
APP_NAME=FastAPI App
ENVIRONMENT=development
DEBUG=True

# 服務器配置
HOST=0.0.0.0
PORT=8000

# 資料庫配置
DATABASE_URL=postgresql://user:password@localhost:5432/dev_db

# Redis 配置
REDIS_URL=redis://localhost:6379

# 安全配置
SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS 配置
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# 日誌配置
LOG_LEVEL=DEBUG
```

**生產環境 `.env.production`：**
```bash
# 應用配置
APP_NAME=FastAPI Production
ENVIRONMENT=production
DEBUG=False

# 服務器配置
HOST=0.0.0.0
PORT=8000

# 資料庫配置（從 Secret 管理系統讀取）
DATABASE_URL=postgresql://user:${DB_PASSWORD}@db.example.com:5432/prod_db

# Redis 配置
REDIS_URL=redis://redis.example.com:6379
REDIS_PASSWORD=${REDIS_PASSWORD}

# 安全配置（從 Secret 管理系統讀取）
SECRET_KEY=${SECRET_KEY}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15

# CORS 配置
CORS_ORIGINS=https://app.example.com,https://admin.example.com

# 日誌配置
LOG_LEVEL=INFO
LOG_FILE=/var/log/fastapi/app.log
```

**注意：** `.env.production` 不應該包含實際的密碼，應該使用變數占位符或從 Secret 管理系統讀取。

### 2. .env.example 模板

`.env.example`（提交到 Git）：

```bash
# 應用配置
APP_NAME=FastAPI App
ENVIRONMENT=development
DEBUG=False

# 服務器配置
HOST=0.0.0.0
PORT=8000

# 資料庫配置
DATABASE_URL=postgresql://user:password@localhost:5432/mydb

# Redis 配置
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=

# 安全配置
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS 配置
CORS_ORIGINS=http://localhost:3000

# 日誌配置
LOG_LEVEL=INFO
LOG_FILE=
```

### 3. 環境變數優先級

Pydantic Settings 按以下優先級讀取配置：

1. **環境變數**（最高優先級）
2. `.env` 文件
3. **默認值**（最低優先級）

```python
class Settings(BaseSettings):
    # 環境變數 > .env 文件 > 默認值
    database_url: str = Field(
        default="sqlite:///app.db",  # 3. 默認值
        env="DATABASE_URL"            # 1. 環境變數
    )
    # .env 文件中的 DATABASE_URL 是 2. 中間優先級
```

### 4. python-dotenv 使用

```python
# config/settings.py
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

# 手動加載 .env 文件
env_file = os.getenv("ENV_FILE", ".env")
load_dotenv(env_file)

class Settings(BaseSettings):
    # ...
    
    class Config:
        env_file = env_file
```

## 機密資訊管理

### 1. 本地開發（.env + .gitignore）

```bash
# .gitignore
.env
.env.local
.env.*.local
*.env
secrets/
```

**注意：** `.env.example` 應該提交到 Git，但實際的 `.env` 文件不應該。

### 2. Docker 環境變數

**docker-compose.yml：**
```yaml
services:
  api:
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
      - SECRET_KEY=${SECRET_KEY}
    env_file:
      - .env.production
```

### 3. Kubernetes Secrets

**創建 Secret：**
```bash
# 從命令行創建
kubectl create secret generic fastapi-secrets \
  --from-literal=secret-key='your-secret-key' \
  --from-literal=database-url='postgresql://user:pass@db:5432/mydb'

# 從文件創建
kubectl create secret generic fastapi-secrets \
  --from-file=.env=./.env.production
```

**在 Deployment 中使用：**
```yaml
spec:
  containers:
  - name: fastapi
    env:
    - name: SECRET_KEY
      valueFrom:
        secretKeyRef:
          name: fastapi-secrets
          key: secret-key
    - name: DATABASE_URL
      valueFrom:
        secretKeyRef:
          name: fastapi-secrets
          key: database-url
```

### 4. HashiCorp Vault 整合

```python
# config/vault.py
import hvac

def get_secret_from_vault(path: str, key: str) -> str:
    """從 Vault 讀取機密"""
    client = hvac.Client(url=os.getenv("VAULT_ADDR"))
    client.token = os.getenv("VAULT_TOKEN")
    
    secret = client.secrets.kv.v2.read_secret_version(path=path)
    return secret["data"]["data"][key]

# config/settings.py
class Settings(BaseSettings):
    secret_key: str = Field(default_factory=lambda: get_secret_from_vault(
        "secret/fastapi", 
        "secret_key"
    ))
```

### 5. AWS Secrets Manager

```python
# config/aws_secrets.py
import boto3
import json

def get_secret(secret_name: str) -> dict:
    """從 AWS Secrets Manager 讀取機密"""
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# 使用
secrets = get_secret("fastapi/production")
DATABASE_URL = secrets["database_url"]
```

## 配置驗證

Pydantic Settings 提供強大的配置驗證功能。

### 1. 型別驗證

```python
from pydantic import Field, validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    port: int = Field(default=8000, ge=1, le=65535)  # 1-65535
    pool_size: int = Field(default=10, gt=0)  # 必須 > 0
    log_level: str = Field(default="INFO")
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level must be one of {valid_levels}')
        return v.upper()
    
    @validator('port')
    def validate_port(cls, v):
        if v < 1024 and os.geteuid() != 0:
            raise ValueError('Ports < 1024 require root privileges')
        return v
```

### 2. 自定義驗證器

```python
from pydantic import PostgresDsn, RedisDsn, validator
from typing import Optional

class Settings(BaseSettings):
    database_url: PostgresDsn  # 自動驗證 PostgreSQL DSN 格式
    redis_url: RedisDsn  # 自動驗證 Redis DSN 格式
    
    @validator('database_url', pre=True)
    def validate_database_url(cls, v):
        if not v:
            raise ValueError('DATABASE_URL is required')
        # 可以添加額外的驗證邏輯
        return v
```

### 3. 必需字段驗證

```python
class Settings(BaseSettings):
    # 沒有默認值 = 必需字段
    secret_key: str = Field(..., env="SECRET_KEY")
    database_url: str = Field(..., env="DATABASE_URL")
    
    # 有默認值 = 可選字段
    redis_url: str = Field(default="redis://localhost:6379")
```

如果必需字段缺失，Pydantic 會自動拋出驗證錯誤。

### 4. 啟動時驗證

```python
# main.py
from fastapi import FastAPI
from config.settings import Settings

def validate_settings():
    """啟動時驗證所有配置"""
    try:
        settings = Settings()
        # 可以添加自定義驗證邏輯
        return settings
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        raise

settings = validate_settings()
app = FastAPI(title=settings.app_name)
```

## 最佳實踐

### 1. 配置組織結構

```
config/
├── __init__.py
├── settings.py          # 主配置類
├── database.py          # 資料庫配置
├── redis.py            # Redis 配置
├── logging.py          # 日誌配置
└── security.py         # 安全配置
```

### 2. 配置文檔化

```python
class Settings(BaseSettings):
    """應用配置
    
    Attributes:
        database_url: 資料庫連接 URL
        pool_size: 連接池大小，建議為 CPU 核心數 × 2
        max_overflow: 最大溢出連接數
    """
    database_url: str = Field(
        ...,
        env="DATABASE_URL",
        description="PostgreSQL 資料庫連接 URL"
    )
    pool_size: int = Field(
        default=10,
        env="DATABASE_POOL_SIZE",
        description="資料庫連接池大小",
        gt=0
    )
```

### 3. 敏感資訊處理

```python
from pydantic import Field, SecretStr

class Settings(BaseSettings):
    # 使用 SecretStr 隱藏敏感資訊
    secret_key: SecretStr = Field(..., env="SECRET_KEY")
    database_password: SecretStr = Field(..., env="DATABASE_PASSWORD")
    
    def get_secret_key(self) -> str:
        """獲取解密後的密鑰"""
        return self.secret_key.get_secret_value()
```

### 4. 配置快取

```python
from functools import lru_cache

@lru_cache()
def get_settings() -> Settings:
    """獲取配置實例（緩存）"""
    return Settings()

settings = get_settings()
```

### 5. 環境特定配置

```python
import os
from pathlib import Path

def get_env_file() -> str:
    """根據環境變數選擇 .env 文件"""
    env = os.getenv("ENVIRONMENT", "development")
    env_file = f".env.{env}"
    
    if Path(env_file).exists():
        return env_file
    return ".env"

class Settings(BaseSettings):
    # ...
    
    class Config:
        env_file = get_env_file()
```

## 常見問題

### Q: 如何處理複雜的配置結構？
**A:** 使用嵌套的 Pydantic 模型，或使用 `env_nested_delimiter` 支持嵌套環境變數。

### Q: 配置變更需要重啟應用嗎？
**A:** 是的，Pydantic Settings 在應用啟動時讀取配置。如需動態配置，考慮使用配置中心（如 Consul、etcd）。

### Q: 如何在不同環境使用不同配置？
**A:** 使用不同的 `.env` 文件（`.env.development`, `.env.production`）或通過 `ENVIRONMENT` 環境變數選擇。

### Q: 機密資訊應該存儲在哪裡？
**A:** 
- 開發環境：`.env` 文件（不提交到 Git）
- 生產環境：Secret 管理系統（Kubernetes Secrets、HashiCorp Vault、AWS Secrets Manager）

## 總結

### Flask → FastAPI 配置遷移總結

| 項目 | Flask | FastAPI | 優勢 |
|------|-------|---------|------|
| **配置管理** | 手動處理 | Pydantic Settings | 自動驗證和型別轉換 |
| **型別驗證** | 無 | 強型別驗證 | 編譯期發現錯誤 |
| **環境變數** | 手動讀取 | 自動讀取 | 更簡單 |
| **配置文檔** | 手動維護 | 自動生成 | 減少維護成本 |

### 關鍵要點

1. ✅ **使用 Pydantic Settings 管理配置**
2. ✅ **遵循 12-Factor App 原則**
3. ✅ **將機密資訊存儲在 Secret 管理系統**
4. ✅ **使用 `.env.example` 作為配置模板**
5. ✅ **配置驗證確保應用正確啟動**

## 參考資源

- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [12-Factor App](https://12factor.net/config)
- [FastAPI Settings](https://fastapi.tiangolo.com/advanced/settings/)
- [python-dotenv Documentation](https://github.com/theskumar/python-dotenv)

