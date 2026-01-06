from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from ai_service import AIService
from dependencies import get_current_user
from database import User

router = APIRouter()


class AnalysisRequest(BaseModel):
    data: Dict[str, Any]
    context: str
    api_key: Optional[str] = None  # Optional: For BYOK mode
    provider: Optional[str] = "zeabur"  # 'zeabur' or 'google_gemini'
    model: Optional[str] = "gemini-2.5-flash"
    report_type: Optional[str] = "ad_analysis"  # 'ad_analysis' or 'weekly_summary'


class TestConnectionRequest(BaseModel):
    api_key: Optional[str] = None
    provider: Optional[str] = "zeabur"
    model: Optional[str] = "gemini-2.5-flash"


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
    user: User = Depends(get_current_user)
):
    """
    Get available models for a provider.
    """
    models = AIService.get_available_models(provider)
    if not models:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    
    return {
        "provider": provider,
        "models": models
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
    from auth import TokenManager
    
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
    from auth import TokenManager
    
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
        return {
            "success": True,
            "message": "AI settings saved successfully",
            "settings": settings
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/settings/{provider}")
async def clear_ai_key(
    provider: str,
    user: User = Depends(get_current_user)
):
    """
    Clear a specific AI provider's API key.
    """
    from auth import TokenManager
    
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
