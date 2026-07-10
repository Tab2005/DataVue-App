"""
GA4 Service (相容轉發層)

此檔案的實作已於 docs/22 第 0 波重構搬移至 `modules/ga4/{client,service}.py`：
- OAuth 授權碼交換、token 刷新、Admin API 屬性列表 → `modules/ga4/client.py`（`GA4Client`）
- RunReport 報表組裝、快取、週報資料 → `modules/ga4/service.py`（`GA4AnalyticsService`）

保留本檔案是為了不破壞既有呼叫端（`routers/ga4.py`、`services/report_service.py`）
的 `from ga4_service import GA4Service` 匯入路徑與方法簽名。新代碼請直接
import `modules.ga4`，不要在本檔案新增邏輯。
"""
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from database import User
from modules.ga4.client import GA4Client
from modules.ga4.service import GA4AnalyticsService


class GA4Service:
    """薄轉發層：所有方法皆呼叫 `modules/ga4` 的對應實作，本身不含邏輯。"""

    SCOPES = GA4Client.SCOPES
    VIRTUAL_METRICS = GA4Client.VIRTUAL_METRICS

    @staticmethod
    def exchange_code(user: User, code: str, db: Session) -> Tuple[bool, str]:
        return GA4Client.exchange_code(user, code, db)

    @staticmethod
    def get_credentials(user: User, db: Session = None):
        return GA4Client.get_credentials(user, db)

    @staticmethod
    def list_properties(user: User, db: Session = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        return GA4Client.list_properties(user, db)

    @staticmethod
    def get_analytics(
        user: User,
        property_id: str,
        start_date: str,
        end_date: str,
        metrics: Optional[List[str]] = None,
        dimensions: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        db: Session = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        return GA4AnalyticsService.get_analytics(
            user=user,
            property_id=property_id,
            start_date=start_date,
            end_date=end_date,
            metrics=metrics,
            dimensions=dimensions,
            limit=limit,
            offset=offset,
            db=db
        )

    @staticmethod
    async def get_weekly_report_data(
        user: User,
        property_id: str,
        since: str,
        until: str,
        selected_metrics: List[str],
        db: Session = None
    ) -> Dict[str, Any]:
        return await GA4AnalyticsService.get_weekly_report_data(
            user=user,
            property_id=property_id,
            since=since,
            until=until,
            selected_metrics=selected_metrics,
            db=db
        )
