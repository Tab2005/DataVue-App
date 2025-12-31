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
