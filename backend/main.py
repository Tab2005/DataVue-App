from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from auth import TokenManager

app = FastAPI()

# Configure CORS to allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev flexibility (fixes port mismatch)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Google Token Verification ---
import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

load_dotenv()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
security = HTTPBearer()

def verify_google_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        # Specify the CLIENT_ID of the app that accesses the backend:
        id_info = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)

        # ID token is valid. Get the user's Google Account ID from the decoded token.
        userid = id_info['sub']
        return userid
    except ValueError as e:
        # Invalid token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
# ---------------------------------

class ExchangeRequest(BaseModel):
    app_id: str
    app_secret: str
    short_token: str

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}

@app.post("/api/auth/exchange-token")
def exchange_token_endpoint(request: ExchangeRequest, user_id: str = Depends(verify_google_token)):
    success, message = TokenManager.exchange_for_long_lived_token(
        request.app_id, 
        request.app_secret, 
        request.short_token
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}

from services import FacebookService

# ... imports ...

@app.get("/api/ad-accounts")
def get_ad_accounts(user_id: str = Depends(verify_google_token)):
    accounts, error = FacebookService.get_all_ad_accounts()
    if error:
         # If no token or error, return empty list so frontend can handle it gracefully
        return []
    return accounts

@app.get("/api/dashboard-data")
def get_dashboard_data(account_id: str = None, user_id: str = Depends(verify_google_token)):
    # If explicit account_id is provided, use it
    if account_id:
        insights = FacebookService.get_account_insights(account_id)
        if insights:
            return {
                "source": "real",
                "account_id": account_id,
                "kpi": insights["kpi"],
                "chart_data": insights["charts"]
            }
        else:
            # If fetch failed for specific account
            raise HTTPException(status_code=400, detail="Failed to fetch insights for this account")

    # If no account_id provided (or initial load state without selection), return mock
    return {
        "source": "mock_fallback",
        "kpi": [
            {"label": "Total Followers", "value": "---", "change": "---"},
            {"label": "Engagement Rate", "value": "---", "change": "---"},
            {"label": "Impressions", "value": "---", "change": "---"},
            {"label": "Reach", "value": "---", "change": "---"},
        ],
        "chart_data": []
    }
