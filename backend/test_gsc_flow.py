"""
Test script to diagnose GSC token exchange failure.
This simulates the exact flow happening in the /authorize endpoint.
"""
import os
import sys
import traceback
from dotenv import load_dotenv

load_dotenv()

# Print environment check
print("=" * 60)
print("Environment Check")
print("=" * 60)
client_id = os.getenv("GOOGLE_CLIENT_ID")
client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
print(f"CLIENT_ID present: {bool(client_id)}")
print(f"CLIENT_ID length: {len(client_id) if client_id else 0}")
print(f"CLIENT_SECRET present: {bool(client_secret)}")
print(f"CLIENT_SECRET length: {len(client_secret) if client_secret else 0}")

if not client_id or not client_secret:
    print("\n[ERROR] Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET!")
    sys.exit(1)

# Now test the actual flow
print("\n" + "=" * 60)
print("Testing GSC Service Flow")
print("=" * 60)

from google_auth_oauthlib.flow import Flow

SCOPES = [
    'https://www.googleapis.com/auth/webmasters.readonly',
    'openid',
    'email',
    'profile'
]

client_config = {
    "web": {
        "client_id": client_id,
        "client_secret": client_secret,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

print(f"\nScopes configured: {SCOPES}")
print(f"Client config keys: {list(client_config['web'].keys())}")

# Test Flow initialization
try:
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri="postmessage"
    )
    print("\n[OK] Flow object created successfully")
    print(f"Flow redirect_uri: {flow.redirect_uri}")
    print(f"Flow scopes: {flow.oauth2session.scope}")
except Exception as e:
    print(f"\n[ERROR] Failed to create Flow:")
    traceback.print_exc()
    sys.exit(1)

# Test with a dummy code (will fail, but we want to see the exact error)
print("\n" + "=" * 60)
print("Testing Token Exchange (with dummy code - expected to fail)")
print("=" * 60)

try:
    flow.fetch_token(code="dummy_test_code_12345")
    print("[UNEXPECTED] Token exchange succeeded with dummy code!")
except Exception as e:
    print(f"\n[EXPECTED ERROR] Token exchange failed:")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    
    # Check if it's the specific scope error
    error_str = str(e).lower()
    if "scope" in error_str:
        print("\n[DIAGNOSIS] This is a SCOPE MISMATCH error!")
        print("The scopes requested during token exchange don't match")
        print("what was authorized by the user in the OAuth popup.")
    elif "redirect" in error_str:
        print("\n[DIAGNOSIS] This is a REDIRECT_URI_MISMATCH error!")
        print("Check Google Cloud Console for correct redirect URIs.")
    elif "invalid_grant" in error_str:
        print("\n[DIAGNOSIS] This is an INVALID_GRANT error!")
        print("The authorization code may have expired or been used already.")
    elif "invalid_client" in error_str:
        print("\n[DIAGNOSIS] This is an INVALID_CLIENT error!")
        print("Check CLIENT_ID and CLIENT_SECRET in .env file.")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
