"""
AI Service (相容轉發層)

此檔案的實作已於 docs/07_audits_and_reviews/CODE_REVIEW_ACTION_PLAN_2026-07-01.md
P1-1 真遷移搬移至 `modules/ai_hub/service.py`（`AIService`）。

保留本檔案是為了不破壞既有呼叫端（`modules/ai_hub/router.py`、
`tests/test_analytics_ai.py`、`tests/test_ga4_insights_wave2.py`）的
`from ai_service import AIService` 匯入路徑與方法簽名。新代碼請直接
import `modules.ai_hub.service`，不要在本檔案新增邏輯。
"""
from typing import Optional, Dict, Any, Generator

from modules.ai_hub.service import AIService as _AIService


class AIService:
    """薄轉發層：所有方法皆呼叫 `modules/ai_hub` 的對應實作，本身不含邏輯。"""

    PROVIDERS = _AIService.PROVIDERS

    @staticmethod
    def get_available_providers() -> Dict[str, Dict]:
        return _AIService.get_available_providers()

    @staticmethod
    def get_available_models(provider: str = "zeabur", remote: bool = False, api_key: Optional[str] = None) -> Dict[str, Dict]:
        return _AIService.get_available_models(provider, remote=remote, api_key=api_key)

    @staticmethod
    def get_openrouter_client(api_key: Optional[str] = None):
        return _AIService.get_openrouter_client(api_key=api_key)

    @staticmethod
    def get_zeabur_client(api_key: Optional[str] = None):
        return _AIService.get_zeabur_client(api_key=api_key)

    @staticmethod
    def test_connection(
        api_key: Optional[str] = None,
        provider: str = "zeabur",
        model: str = "gemini-2.5-flash"
    ) -> bool:
        return _AIService.test_connection(api_key=api_key, provider=provider, model=model)

    @staticmethod
    def analyze_data(
        data: Dict[str, Any],
        context: str,
        api_key: Optional[str] = None,
        provider: str = "zeabur",
        model: str = "deepseek/deepseek-v4-flash",
        report_type: str = "ad_analysis",
        period: str = "weekly",
        module_type: str = "fb_ads"
    ) -> Generator[str, None, None]:
        return _AIService.analyze_data(
            data=data,
            context=context,
            api_key=api_key,
            provider=provider,
            model=model,
            report_type=report_type,
            period=period,
            module_type=module_type,
        )
