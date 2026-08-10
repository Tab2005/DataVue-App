"""
GSC Module
Google Search Console 整合模組 - 提供 GSC 認證、網站列表、分析資料等功能

刻意不在此處 eager import `.router`/`.service`（比照 modules/ga4/__init__.py
的作法）：根目錄 `gsc_service.py`（相容轉發層）會 import
`modules.gsc.service`，若這裡的 `__init__.py` 又 eager import `.router`
（而 `.router` 需要 `from gsc_service import GSCService`），會形成
`gsc_service.py` → `modules.gsc`（觸發 `__init__.py`）→ `.router` →
`gsc_service.py` 的循環匯入。

使用方式：
    from modules.gsc.router import router as gsc_router
    from modules.gsc.service import GSCService
"""

__all__ = ["router", "service"]
