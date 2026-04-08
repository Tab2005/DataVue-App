# backend/routers/line.py
"""
LINE API Router
處理 LINE 帳號綁定代碼產生與 Webhook 回報。
"""

import random
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from database import User, LineBinding
from core.config import settings
from dependencies import get_db, get_current_active_user
from services.line_service import handle_line_webhook

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/line", tags=["line"])

@router.get("/binding-code")
async def get_binding_code(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    """
    為當前用戶產生一個 6 位數的自動綁定驗證碼。
    """
    # 檢查是否已有有效代碼，有的話就更新
    existing = db.query(LineBinding).filter(LineBinding.user_id == user.id).first()
    if existing:
        db.delete(existing)
        db.commit()

    # 產生不重複的 6 位數代碼
    code = str(random.randint(100000, 999999))
    
    # 衝突檢查 (極低機率但保險起見)
    while db.query(LineBinding).filter(LineBinding.code == code).first():
        code = str(random.randint(100000, 999999))

    new_binding = LineBinding(
        code=code,
        user_id=user.id
    )
    db.add(new_binding)
    db.commit()
    
    return {
        "code": code,
        "expires_in_seconds": 600, # 10 分鐘
        "status": "pending",
        "qr_code_url": settings.LINE_BOT_QR_URL
    }

@router.get("/status")
async def get_line_status(
    user: User = Depends(get_current_active_user)
):
    """
    回傳用戶是否已綁定 LINE。
    """
    return {
        "is_linked": user.line_user_id is not None,
        "line_user_id": user.line_user_id[:8] + "..." if user.line_user_id else None
    }

@router.post("/webhook")
async def line_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    LINE Messaging API Webhook 入口點。
    直接將處理邏輯交給 BackgroundTasks，快速回傳 200 給 LINE。
    """
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    body_str = body.decode("utf-8")
    
    # 交給背景處理
    background_tasks.add_task(handle_line_webhook, db, body_str, signature)
    
    return {"message": "ok"}
