
import os
from dotenv import load_dotenv

load_dotenv()
client_id = os.getenv("GOOGLE_CLIENT_ID")
client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

print(f"CLIENT_ID Length: {len(client_id) if client_id else 0}")
print(f"CLIENT_SECRET Length: {len(client_secret) if client_secret else 0}")
print(f"CLIENT_ID Starts With: {client_id[:5] if client_id else 'None'}")
print(f"CLIENT_SECRET Starts With: {client_secret[:5] if client_secret else 'None'}")
print(f"Full Secret (Double Check): {client_secret}")
