from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
from ai_service import AIService
from dependencies import get_current_user # Correct dependency
from database import User

router = APIRouter()

class AnalysisRequest(BaseModel):
    data: Dict[str, Any]
    context: str
    api_key: Optional[str] = None # Optional: For BYOK mode
    model: Optional[str] = "gemini-2.5-flash"

class TestConnectionRequest(BaseModel):
    api_key: Optional[str] = None

@router.post("/test-connection")
async def test_connection(request: TestConnectionRequest, user: User = Depends(get_current_user)):
    """
    Test connectivity to the AI Service.
    """
    success = AIService.test_connection(api_key=request.api_key)
    if success:
        return {"status": "ok", "message": "AI Service Connected Successfully"}
    else:
        raise HTTPException(status_code=400, detail="Failed to connect to AI Service. Check Key or Zeabur Env.")

@router.post("/analyze")
async def analyze_data(request: AnalysisRequest, user: User = Depends(get_current_user)):
    """
    Stream analysis results.
    """
    # Simply stream the generator
    return StreamingResponse(
        AIService.analyze_data(
            data=request.data, 
            context=request.context, 
            api_key=request.api_key,
            model=request.model
        ),
        media_type="text/plain"
    )
