"""
GA4 Module - Service
Google Analytics 4 服務

此檔案重新導出 ga4_service 以保持模組結構一致性。

使用方式:
    from modules.ga4.service import GA4Service

    # 交換授權碼
    success, message = GA4Service.exchange_code(user, code, db)

    # 列出屬性
    properties, error = GA4Service.list_properties(user)

    # 取得分析資料
    data, error = GA4Service.get_analytics(user, property_id, start_date, end_date)
"""

# 重新導出現有的 GA4 服務
from ga4_service import GA4Service

__all__ = ["GA4Service"]