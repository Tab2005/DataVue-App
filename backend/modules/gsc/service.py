"""
GSC Module - Service
Google Search Console 服務

此檔案重新導出 gsc_service 以保持模組結構一致性。

使用方式:
    from modules.gsc.service import GSCService
    
    # 交換授權碼
    success, message = GSCService.exchange_code(user, code, db)
    
    # 列出網站
    sites, error = GSCService.list_sites(user)
    
    # 取得分析資料
    data, error = GSCService.get_analytics(user, site_url, start_date, end_date)
"""

# 重新導出現有的 GSC 服務
from gsc_service import GSCService

__all__ = ["GSCService"]


def get_analytics_data(user, site_url, start_date, end_date):
    data, error = GSCService.get_analytics(user, site_url, start_date, end_date, limit=None, offset=0)
    return data, error
