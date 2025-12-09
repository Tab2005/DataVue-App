from auth import TokenManager
from database import SessionLocal, User
import os
from dotenv import load_dotenv

load_dotenv()

def test_encryption_flow():
    print("--- Testing Security Hardening ---")
    
    # 1. Setup a test user
    test_google_id = "test_user_encryption"
    test_token_plain = "EAAB_PLAINTEXT_TOKEN"
    
    session = SessionLocal()
    # Cleanup previous test
    session.query(User).filter(User.google_id == test_google_id).delete()
    session.commit()
    
    # 2. Insert PLAINTEXT data manually (simulating old data)
    user = User(google_id=test_google_id, fb_access_token=test_token_plain)
    session.add(user)
    session.commit()
    session.close()
    print("[1] Inserted plaintext token directly into DB.")
    
    # 3. Test Lazy Migration (Read)
    retrieved = TokenManager.get_user_token(test_google_id)
    print(f"[2] Retrieved token via TokenManager: {retrieved}")
    if retrieved == test_token_plain:
        print("    PASS: Lazy migration worked (read plaintext successfully).")
    else:
        print("    FAIL: Could not read plaintext token.")
        
    # 4. Test Encryption (Write)
    test_token_new = "EAAB_NEW_TOKEN_TO_ENCRYPT"
    TokenManager.save_user_token(test_google_id, test_token_new)
    print("[3] Saved new token via TokenManager (should be encrypted).")
    
    # 5. Verify DB content (Raw)
    session = SessionLocal()
    raw_user = session.query(User).filter(User.google_id == test_google_id).first()
    raw_token = raw_user.fb_access_token
    session.close()
    
    print(f"[4] Raw DB Content: {raw_token}")
    if raw_token != test_token_new and raw_token.startswith("gAAAA"):
        print("    PASS: Token is encrypted in Database.")
    else:
        print("    FAIL: Token is NOT encrypted (or format unexpected).")
        
    # 6. Verify Decryption (Read)
    retrieved_new = TokenManager.get_user_token(test_google_id)
    print(f"[5] Retrieved new token: {retrieved_new}")
    if retrieved_new == test_token_new:
        print("    PASS: Decryption worked.")
    else:
        print("    FAIL: Decryption failed.")

    # Cleanup
    session = SessionLocal()
    session.query(User).filter(User.google_id == test_google_id).delete()
    session.commit()
    session.close()

if __name__ == "__main__":
    test_encryption_flow()
