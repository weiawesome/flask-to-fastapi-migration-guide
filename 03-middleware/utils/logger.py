"""
Logger Utility
日誌工具 - 統一的日誌配置
"""
import logging
import sys
from pathlib import Path


def setup_logger(
    name: str = "fastapi_app",
    level: int = logging.INFO,
    log_file: str | None = None
) -> logging.Logger:
    """
    設定日誌系統
    配置 root logger，讓所有子 logger 繼承配置並寫入檔案
    
    Args:
        name: Logger 名稱（用於標識，但實際配置 root logger）
        level: 日誌級別（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        log_file: 日誌檔案路徑（可選）
    
    Returns:
        logging.Logger: 配置好的 logger
    """
    # 獲取 root logger 並配置
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 避免重複新增 handler
    if root_logger.handlers:
        return logging.getLogger(name)
    
    # 日誌格式
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler（輸出到終端）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File Handler（輸出到檔案）
    if log_file:
        # 確保目錄存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # 返回指定名稱的 logger（會繼承 root logger 的配置）
    return logging.getLogger(name)


def get_logger(name: str) -> logging.Logger:
    """
    獲取 logger
    
    Args:
        name: Logger 名稱
    
    Returns:
        logging.Logger: Logger 實例
    """
    return logging.getLogger(name)

