"""
GSC Service (相容轉發層)

此檔案的實作已於 docs/07_audits_and_reviews/CODE_REVIEW_ACTION_PLAN_2026-07-01.md
P1-1 真遷移搬移至 `modules/gsc/service.py`（`GSCService`）。

保留本檔案是為了不破壞既有呼叫端（`modules/gsc/router.py`、
`scripts/verify_gsc_search_appearance.py`）的 `from gsc_service import
GSCService` 匯入路徑與方法簽名。新代碼請直接 import `modules.gsc.service`，
不要在本檔案新增邏輯。
"""
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from database import User
from modules.gsc.service import GSCService as _GSCService


class GSCService:
    """薄轉發層：所有方法皆呼叫 `modules/gsc` 的對應實作，本身不含邏輯。"""

    SCOPES = _GSCService.SCOPES

    @staticmethod
    def exchange_code(user: User, code: str, db: Session) -> Tuple[bool, str]:
        return _GSCService.exchange_code(user, code, db)

    @staticmethod
    def get_credentials(user: User, db: Session = None):
        return _GSCService.get_credentials(user, db)

    @staticmethod
    def list_sites(user: User, db: Session = None):
        return _GSCService.list_sites(user, db)

    @staticmethod
    def get_analytics(
        user: User,
        site_url: str,
        start_date: str,
        end_date: str,
        dimensions=['date'],
        limit: Optional[int] = None,
        offset: int = 0,
        db: Session = None,
        dimension_filters: Optional[list] = None,
    ):
        return _GSCService.get_analytics(
            user, site_url, start_date, end_date,
            dimensions=dimensions, limit=limit, offset=offset,
            db=db, dimension_filters=dimension_filters,
        )
