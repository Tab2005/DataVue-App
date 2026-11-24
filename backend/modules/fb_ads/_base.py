# backend/modules/fb_ads/_base.py
"""FB Ads 服務共用常數與 Token 取得工具"""

import sys
import logging
from modules.auth.service import TokenManager
from core.meta_api import GRAPH_API_BASE_URL

logger = logging.getLogger(__name__)

BASE_URL = GRAPH_API_BASE_URL
TIMEOUT = 30.0


def get_headers(user_id, team_id=None, allow_fallback=True):
    """取得 Facebook API Authorization headers（同步，使用既有 TokenManager）"""
    if team_id:
        token = TokenManager.get_team_token(team_id)
    else:
        token = TokenManager.get_user_token(user_id, allow_fallback=allow_fallback)

    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}
