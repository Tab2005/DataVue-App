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

class ExchangeRequest(BaseModel):
    app_id: str
    app_secret: str
    short_token: str

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}

@app.post("/api/auth/exchange-token")
def exchange_token_endpoint(request: ExchangeRequest):
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
def get_ad_accounts():
    accounts, error = FacebookService.get_all_ad_accounts()
    if error:
         # If no token or error, return empty list so frontend can handle it gracefully
        return []
    return accounts

@app.get("/api/dashboard-data")
def get_dashboard_data(account_id: str = None):
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
