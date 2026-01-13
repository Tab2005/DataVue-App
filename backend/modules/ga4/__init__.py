"""
GA4 Module
Google Analytics 4 整合模組 - 提供 GA4 認證、屬性列表、分析資料等功能

此模組整合了所有 GA4 相關功能，可複用於其他 FastAPI 專案。

使用方式:

```python
from fastapi import FastAPI
from modules.ga4 import router as ga4_router, GA4Service

app = FastAPI()
app.include_router(ga4_router)
```

導出:
    - router: FastAPI Router，包含 /api/ga4/* 端點
    - GA4Service: GA4 服務類別
"""

from routers.ga4 import router
from ga4_service import GA4Service

__all__ = [
    # Router
    "router",

    # Services
    "GA4Service",
]