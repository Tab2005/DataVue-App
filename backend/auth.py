import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TOKEN_FILE = "tokens.json"

class TokenManager:
    @staticmethod
    def save_tokens(tokens):
        """Save tokens to a local JSON file."""
        with open(TOKEN_FILE, "w") as f:
            json.dump(tokens, f, indent=4)

    @staticmethod
    def load_tokens():
        """Load tokens from the local JSON file."""
        if not os.path.exists(TOKEN_FILE):
            return {}
        try:
            with open(TOKEN_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def exchange_for_long_lived_token(app_id, app_secret, short_lived_token):
        """
        Exchange a short-lived user access token for a long-lived one (60 days).
        https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived
        """
        url = "https://graph.facebook.com/v18.0/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": short_lived_token
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if "access_token" in data:
            # Save the new token securely
            existing_tokens = TokenManager.load_tokens()
            existing_tokens["long_lived_token"] = data["access_token"]
            # Save App ID/Secret locally for future usage if needed (optional but convenient)
            existing_tokens["app_id"] = app_id
            # CAUTION: Saving app_secret in plaintext locally is a risk, usually better in .env
            # But for this simple desktop-like app usage, we save it to tokens.json which is gitignored.
            existing_tokens["app_secret"] = app_secret 
            
            TokenManager.save_tokens(existing_tokens)
            return True, "Token exchanged and saved successfully."
        else:
            return False, data.get("error", {}).get("message", "Unknown error during token exchange.")

    @staticmethod
    def get_access_token():
        tokens = TokenManager.load_tokens()
        return tokens.get("long_lived_token")
