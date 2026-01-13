import os
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"Loading .env from: {dotenv_path}")
result = load_dotenv(dotenv_path)
print(f"load_dotenv result: {result}")

client_id = os.getenv('GOOGLE_CLIENT_ID', '').strip()
client_secret = os.getenv('GOOGLE_CLIENT_SECRET', '').strip()

print('GOOGLE_CLIENT_ID:', 'SET' if client_id else 'NOT SET', f'(length: {len(client_id)})')
print('GOOGLE_CLIENT_SECRET:', 'SET' if client_secret else 'NOT SET', f'(length: {len(client_secret)})')

if client_id:
    print('Client ID starts with:', client_id[:20] + '...')
if client_secret:
    print('Client Secret starts with:', client_secret[:10] + '...')