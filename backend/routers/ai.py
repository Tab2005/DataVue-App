from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import sys
import logging
from ai_service import AIService
from dependencies import get_current_user
from database import User
from modules.auth.service import TokenManager

logger = logging.getLogger(__name__)
router = APIRouter()


class AnalysisRequest(BaseModel):
    data: Dict[str, Any]
    context: str
    api_key: Optional[str] = None  # Optional: For BYOK mode
    provider: Optional[str] = "zeabur"  # 'zeabur' or 'google_gemini'
    model: Optional[str] = "gemini-1.5-flash"
    report_type: Optional[str] = "ad_analysis"  # 'ad_analysis' or 'weekly_summary'


class TestConnectionRequest(BaseModel):
    api_key: Optional[str] = None
    provider: Optional[str] = "zeabur"
    model: Optional[str] = "gemini-1.5-flash"


@router.get("/providers")
async def get_providers(user: User = Depends(get_current_user)):
    """
    Get available AI providers.
    """
    return {
        "providers": AIService.get_available_providers()
    }


@router.get("/models")
async def get_models(
    provider: str = "zeabur",
    sync: bool = False,
    user: User = Depends(get_current_user)
):
    """
    Get available models for a provider.
    Supports 'sync=true' to fetch latest from remote.
    """
    # Get user's API key for this provider (if any)
    api_key = TokenManager.get_ai_api_key(user.google_id, provider=provider)
    
    models = AIService.get_available_models(provider, remote=sync, api_key=api_key)
    if not models:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    
    return {
        "provider": provider,
        "models": models,
        "synced": sync
    }


@router.post("/test-connection")
async def test_connection(
    request: TestConnectionRequest, 
    user: User = Depends(get_current_user)
):
    """
    Test connectivity to the AI Service.
    """
    success = AIService.test_connection(
        api_key=request.api_key,
        provider=request.provider,
        model=request.model
    )
    if success:
        return {
            "status": "ok", 
            "message": "AI Service Connected Successfully",
            "provider": request.provider,
            "model": request.model
        }
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to connect to AI Service (provider: {request.provider}). Check Key or configuration."
        )


@router.post("/analyze")
async def analyze_data(
    request: AnalysisRequest, 
    user: User = Depends(get_current_user)
):
    """
    Stream analysis results.
    """
    return StreamingResponse(
        AIService.analyze_data(
            data=request.data, 
            context=request.context, 
            api_key=request.api_key,
            provider=request.provider,
            model=request.model,
            report_type=request.report_type
        ),
        media_type="text/plain"
    )


# ============================================================
# AI Settings (Encrypted Storage)
# ============================================================

class AISettingsRequest(BaseModel):
    """Request model for saving AI settings"""
    zeabur_api_key: Optional[str] = None  # If empty string, will clear the key
    gemini_api_key: Optional[str] = None  # If empty string, will clear the key
    ai_provider: Optional[str] = None     # 'zeabur' or 'gemini'
    ai_model: Optional[str] = None


@router.get("/settings")
async def get_ai_settings(user: User = Depends(get_current_user)):
    """
    Get current user's AI settings.
    Returns provider, model, and whether keys are configured (not the keys themselves).
    """
    
    settings = TokenManager.get_ai_settings(user.google_id)
    if not settings:
        # Return defaults if no settings found
        return {
            "ai_provider": "zeabur",
            "ai_model": "gemini-2.5-flash",
            "has_zeabur_key": False,
            "has_gemini_key": False
        }
    
    return settings


@router.post("/settings")
async def save_ai_settings(
    request: AISettingsRequest,
    user: User = Depends(get_current_user)
):
    """
    Save user's AI settings (API keys are encrypted before storage).
    """
    logger.info(f"[AI API] save_ai_settings called for user: {user.email}")
    logger.debug(
        f"[AI API] Request data: gemini_key_len={len(request.gemini_api_key) if request.gemini_api_key else 0}, "
        f"zeabur_key_len={len(request.zeabur_api_key) if request.zeabur_api_key else 0}, "
        f"provider={request.ai_provider}, model={request.ai_model}"
    )
    
    try:
        TokenManager.save_ai_settings(
            google_id=user.google_id,
            zeabur_api_key=request.zeabur_api_key,
            gemini_api_key=request.gemini_api_key,
            ai_provider=request.ai_provider,
            ai_model=request.ai_model
        )
        
        # Return updated settings
        settings = TokenManager.get_ai_settings(user.google_id)
        logger.info(f"[AI API] Settings saved.")
        return {
            "success": True,
            "message": "AI settings saved successfully",
            "settings": settings
        }
    except Exception as e:
        logger.error(f"[AI API] Save error: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/settings/{provider}")
async def clear_ai_key(
    provider: str,
    user: User = Depends(get_current_user)
):
    """
    Clear a specific AI provider's API key.
    """
    
    if provider not in ["zeabur", "gemini"]:
        raise HTTPException(status_code=400, detail="Invalid provider. Use 'zeabur' or 'gemini'.")
    
    try:
        if provider == "zeabur":
            TokenManager.save_ai_settings(user.google_id, zeabur_api_key="")
        else:
            TokenManager.save_ai_settings(user.google_id, gemini_api_key="")
        
        return {"success": True, "message": f"{provider} API key cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-gemini")
async def test_gemini_connection(user: User = Depends(get_current_user)):
    """
    Test Google Gemini API connection using the user's saved API key.
    """
    logger.info(f"[AI API] Testing Gemini connection for user: {user.email}")
    
    # Get the user's Gemini API key from encrypted storage
    api_key = TokenManager.get_ai_api_key(user.google_id, provider="gemini")
    
    if not api_key:
        logger.warning(f"[AI API] No Gemini API key found for user: {user.email}")
        return {
            "success": False,
            "message": "No Google Gemini API key configured. Please save your API key first.",
            "provider": "gemini"
        }
    
    logger.debug(f"[AI API] Found Gemini API key (length={len(api_key)})")
    
    try:
        from services.ai.gemini_client import GoogleGeminiClient
        client = GoogleGeminiClient(api_key=api_key)
        result = client.test_connection()
        
        logger.info(f"[AI API] Gemini test result: success={result.get('success')}")
        
        return {
            "success": result.get("success", False),
            "message": result.get("message", "Unknown result"),
            "response": result.get("response", "")[:100] if result.get("response") else None,
            "model": result.get("model"),
            "provider": "gemini"
        }
    except Exception as e:
        logger.error(f"[AI API] Gemini test error: {type(e).__name__}: {str(e)}")
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}",
            "provider": "gemini"
        }

