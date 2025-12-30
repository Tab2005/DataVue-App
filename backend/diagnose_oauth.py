"""
Diagnostic script to test Google OAuth configuration
"""
import os
from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("LOCAL GOOGLE OAUTH DIAGNOSTIC")
print("=" * 60)

client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()

print(f"\n1. CLIENT_ID:")
print(f"   Value: {client_id[:30]}...{client_id[-15:]}")
print(f"   Length: {len(client_id)}")
print(f"   Ends with .apps.googleusercontent.com: {client_id.endswith('.apps.googleusercontent.com')}")

print(f"\n2. CLIENT_SECRET:")
print(f"   Prefix: {client_secret[:6]}...")
print(f"   Length: {len(client_secret)}")
print(f"   Starts with GOCSPX-: {client_secret.startswith('GOCSPX-')}")

print("\n3. REQUIRED GOOGLE CLOUD CONSOLE SETTINGS:")
print("   Go to: https://console.cloud.google.com/apis/credentials")
print("   Select your OAuth 2.0 Client ID (Web Application)")
print("   Ensure these are in 'Authorized JavaScript origins':")
print("     - http://localhost:5173")
print("     - http://localhost:8000")
print("   Ensure these are in 'Authorized redirect URIs':")
print("     - http://localhost:5173")
print("     - http://localhost:8000/api/gsc/callback")

print("\n4. COMMON ISSUES:")
print("   - Missing 'http://localhost:5173' in JavaScript origins")
print("   - Using 'https' instead of 'http' for localhost")
print("   - Trailing slash mismatch (localhost:5173 vs localhost:5173/)")
print("=" * 60)
