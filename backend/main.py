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
# Robust Imports with Error Handling
try:
    from database import init_db, engine, SessionLocal
    DB_STATUS = "OK"
except Exception as e:
    print(f"❌ DATABASE IMPORT ERROR: {e}", file=sys.stderr)
    DB_STATUS = f"ERROR: {e}"
    # Mock objects to prevent NameError later
    engine = None
    SessionLocal = None
    def init_db(): pass

try:
    from services import FacebookService
except Exception as e:
    print(f"❌ SERVICES IMPORT ERROR: {e}", file=sys.stderr)

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
    db_info = "Unknown"
    if engine:
        db_info = "PostgreSQL" if "postgresql" in str(engine.url) else "SQLite"
    
    return {
        "status": "online", 
        "database_status": DB_STATUS,
        "database_type": db_info,
        "message": "Backend is running (Safe Mode)"
    }

# --- Google Token Verification ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
security = HTTPBearer()

def verify_google_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        # P.S. Ideally cache the validation or use a library that handles caching certs
        # DEBUG LOGGING
        print(f"🔐 Verifying Token: {token[:10]}... ClientID: {GOOGLE_CLIENT_ID}", file=sys.stderr)
        
        id_info = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)
        userid = id_info['sub']
        return userid
    except ValueError as e:
        print(f"❌ Token Verification Failed: {e}", file=sys.stderr)
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
def get_dashboard_data(account_id: str = None, days: int = 7, user_id: str = Depends(verify_google_token)):
    if account_id:
        # Pass user_id and days
        insights = FacebookService.get_account_insights(account_id, user_id, days)
        if insights:
            return {
                "source": "real",
                "account_id": account_id,
                "kpi": insights["kpi"],
                "chart_data": insights["charts"],
                "date_range": insights.get("date_range")
            }
        else:
            print(f"❌ Dashboard Data Fetch Failed for {account_id}", file=sys.stderr)
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

@app.get("/api/analytics-data")
def get_analytics_data(
    account_id: str, 
    since: str, 
    until: str, 
    level: str = "account", 
    user_id: str = Depends(verify_google_token)
):
    """
    Endpoint for the Advanced Analytics page.
    Requires account_id, custom date range (since/until), and aggregation level.
    """
    report_data = FacebookService.get_custom_report(account_id, user_id, since, until, level)
    
    if report_data is None:
         raise HTTPException(status_code=400, detail="Failed to fetch analytics data")
         
    return {
        "data": report_data,
        "meta": {
            "level": level,
            "period": f"{since} ~ {until}"
        }
    }

@app.get("/api/analytics-trend")
def get_analytics_trend_data(
    account_id: str,
    since: str,
    until: str,
    prev_since: str = None,
    prev_until: str = None,
    user_id: str = Depends(verify_google_token)
):
    """
    Endpoint for daily trend chart data.
    """
    trend_data = FacebookService.get_analytics_trend(account_id, user_id, since, until, prev_since, prev_until)
    if trend_data is None:
         # Return empty list instead of 400 to avoid breaking UI if just no data
         return []
    return trend_data


if __name__ == "__main__":
    import uvicorn
    print("🚀 STARTING UVICORN SERVER...", file=sys.stderr)
    # Use 'app' object directly instead of string to avoid re-import issues
    # Disable reload for production stability
    uvicorn.run(app, host="0.0.0.0", port=8000)
