import sys
import os

# Capture status of imports
status_report = {}

def safe_import(name, import_func):
    try:
        import_func()
        status_report[name] = "OK"
    except Exception as e:
        status_report[name] = f"ERROR: {str(e)}"

print("🚀 DEBUG MAIN: Starting Progressive Imports...", file=sys.stderr)

# Test 1: Database (SQLAlchemy + psycopg2)
def import_db():
    from database import engine, SessionLocal
safe_import("database", import_db)

# Test 2: Auth (Cryptography + Fernet)
def import_auth():
    from auth import TokenManager
safe_import("auth", import_auth)

# Test 3: Services (Requests + Pandas logic)
def import_services():
    from services import FacebookService
safe_import("services", import_services)

# Test 4: Main App Logic (Routes)
def import_main_deps():
    # Only import non-app parts to avoid re-initializing fastapi app
    # NOW WE TRY TO IMPORT THE WHOLE APP to check for any runtime errors
    from main import app
safe_import("main_app_integrity", import_main_deps)

try:
    from fastapi import FastAPI
    import uvicorn
    status_report["fastapi"] = "OK"
except Exception as e:
    status_report["fastapi"] = f"ERROR: {e}"
    sys.exit(1)

app = FastAPI()

@app.get("/")
def read_root():
    return {
        "status": "diagnostic_mode",
        "env_vars": {
            "DATABASE_URL": "Set" if os.getenv("DATABASE_URL") else "Missing",
            "ENCRYPTION_KEY": "Set" if os.getenv("ENCRYPTION_KEY") else "Missing"
        },
        "import_results": status_report
    }

if __name__ == "__main__":
    print("🚀 DEBUG MAIN: Starting Server...", file=sys.stderr)
    uvicorn.run(app, host="0.0.0.0", port=8000)
