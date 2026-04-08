# backend/services/line_service.py
"""
LINE Messaging API Service
處理與 LINE 伺服器的通訊，包括發送多媒體訊息與處理 Webhook 事件。
"""

import logging
import httpx
import json
from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from core.config import settings
from database.models.user import User
from database.models.line_binding import LineBinding

logger = logging.getLogger(__name__)

LINE_API_BASE = "https://api.line.me/v2/bot"

async def send_line_push_message(to_user_id: str, text: str, flex_content: Optional[Dict] = None):
    """
    發送 Push Message 給指定用戶。
    """
    if not settings.LINE_CHANNEL_ACCESS_TOKEN:
        logger.error("[LineService] LINE_CHANNEL_ACCESS_TOKEN is not configured.")
        return False

    url = f"{LINE_API_BASE}/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"
    }

    # 封裝訊息
    messages = []
    if flex_content:
        messages.append({"type": "flex", "altText": text[:40], "contents": flex_content})
    else:
        messages.append({"type": "text", "text": text})

    payload = {
        "to": to_user_id,
        "messages": messages
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            if response.status_code != 200:
                logger.error(f"[LineService] Failed to send push message: {response.text}")
                return False
            logger.info(f"[LineService] Successfully sent push message to {to_user_id}")
            return True
    except Exception as e:
        logger.error(f"[LineService] Error sending push message: {e}")
        return False

async def handle_line_webhook(db: Session, body: str, signature: str):
    """
    處理來自 LINE 的 Webhook 事件。
    主要功能：解析用戶傳送的 6 位數代碼，完成帳號綁定。
    """
    # TODO: 在正式開發中應驗證 signature (HMAC-SHA256)
    
    try:
        data = json.loads(body)
        events = data.get("events", [])
        
        for event in events:
            if event["type"] == "message" and event["message"]["type"] == "text":
                user_id = event["source"]["userId"]
                msg_text = event["message"]["text"].strip()
                
                # 檢查是否為 6 位數純數字
                if len(msg_text) == 6 and msg_text.isdigit():
                    await _process_binding(db, user_id, msg_text)
                else:
                    # 選項：如果不是代碼，可以回傳預設歡迎語
                    # await send_line_push_message(user_id, "您好！若要綁定帳號，請輸入系統產生的 6 位數驗證碼。")
                    pass
            
            elif event["type"] == "follow":
                # 用戶加入好友事件
                user_id = event["source"]["userId"]
                await send_line_push_message(user_id, "感謝您加入 DataVue 通知助手！請在系統介面取得 6 位數綁定碼並輸入於此，即可完成帳號連結。")

    except Exception as e:
        logger.error(f"[LineService] Error handling webhook: {e}")

async def _process_binding(db: Session, line_user_id: str, code: str):
    """
    執行綁定邏輯
    """
    # 查找代碼記錄
    binding = db.query(LineBinding).filter(LineBinding.code == code).first()
    
    if not binding:
        await send_line_push_message(line_user_id, "❌ 無效的綁定碼，請重新從系統取得。")
        return

    if binding.is_expired:
        await send_line_push_message(line_user_id, "❌ 綁定碼已過期，請重新從系統取得。")
        db.delete(binding)
        db.commit()
        return

    # 執行綁定
    user = db.query(User).filter(User.id == binding.user_id).first()
    if user:
        user.line_user_id = line_user_id
        # 綁定成功後刪除代碼
        db.delete(binding)
        db.commit()
        await send_line_push_message(line_user_id, f"✅ 帳號綁定成功！\n您的電子郵件：{user.email}\n從現在開始，自動產生的週報將會透過這裡通知您。")
        logger.info(f"[LineService] User {user.id} matched with LINE {line_user_id}")
    else:
        await send_line_push_message(line_user_id, "❌ 找不到對應的使用者帳號。")
