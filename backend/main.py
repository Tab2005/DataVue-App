import sys
print("🚀 Starting Main Application...", file=sys.stderr)
from fastapi import FastAPI, HTTPException, Depends, status
print("✅ FastAPI imported", file=sys.stderr)
import os
print(f"📂 Current Debug Dir: {os.getcwd()}", file=sys.stderr)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from auth import TokenManager
from services import FacebookService
from database import init_db
import os
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# Initialize Database
# Load environment variables FIRST
load_dotenv()

# Initialize Database with Error Handling
try:
    init_db()
except Exception as e:
    print(f"❌ Database Initialization Failed: {str(e)}")


app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    """Health check endpoint to verify service status and DB connection."""
    db_type = "PostgreSQL" if "postgresql" in str(engine.url) else "SQLite"
    return {"status": "online", "database": db_type, "message": "Backend is running!"}

# --- Google Token Verification ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
security = HTTPBearer()

def verify_google_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        # P.S. Ideally cache the validation or use a library that handles caching certs
        id_info = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)
        userid = id_info['sub']
        return userid
    except ValueError as e:
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
        request.short_token,
        user_id # Pass user_id
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}

@app.get("/api/ad-accounts")
def get_ad_accounts(user_id: str = Depends(verify_google_token)):
    # Pass user_id
    accounts, error = FacebookService.get_all_ad_accounts(user_id)
    if error:
        return []
    return accounts

@app.get("/api/dashboard-data")
def get_dashboard_data(account_id: str = None, user_id: str = Depends(verify_google_token)):
    if account_id:
        # Pass user_id
        insights = FacebookService.get_account_insights(account_id, user_id)
        if insights:
            return {
                "source": "real",
                "account_id": account_id,
                "kpi": insights["kpi"],
                "chart_data": insights["charts"]
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to fetch insights for this account")

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


if __name__ == "__main__":
    import uvicorn
    # Important: host="0.0.0.0" is required for Docker/Zeabur to expose the port.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
