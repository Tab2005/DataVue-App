"""
Core Logging Configuration
統一的應用程式日誌設定模組

用法:
    from core.logging import setup_logging
    setup_logging()
    
    # 在每個模組頂部：
    import logging
    logger = logging.getLogger(__name__)
"""

import logging
import sys
from typing import Optional


def setup_logging(debug: Optional[bool] = None) -> logging.Logger:
    """
    設定應用程式日誌系統。
    
    Args:
        debug: 是否啟用 DEBUG 層級。若為 None，從環境變數 DEBUG/DEBUG_MODE 讀取。
    
    Returns:
        根 Logger 物件
    """
    if debug is None:
        import os
        debug = (
            os.getenv("DEBUG", "false").lower() == "true" or
            os.getenv("DEBUG_MODE", "false").lower() == "true"
        )

    log_level = logging.DEBUG if debug else logging.INFO

    # 格式：時間 | 模組名稱（對齊30字元）| 層級 | 訊息
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)-30s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 輸出至 stdout（供 Docker/容器平台收集）
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(log_level)

    # 設定根 Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(stream_handler)

    # 降低第三方庫的日誌噪音
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if debug else logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    root_logger.info(
        f"Logging initialized | level={'DEBUG' if debug else 'INFO'} | output=stdout"
    )
    return root_logger
