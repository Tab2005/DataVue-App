import sys
print("🚀 DEBUG MAIN: Starting...", file=sys.stderr)

try:
    from fastapi import FastAPI
    import uvicorn
    print("✅ DEBUG MAIN: Imports successful", file=sys.stderr)
except Exception as e:
    print(f"❌ DEBUG MAIN Import Error: {e}", file=sys.stderr)
    sys.exit(1)

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "debug_ok", "message": "Minimal FastAPI is running!"}

if __name__ == "__main__":
    print("🚀 DEBUG MAIN: Starting Server on 0.0.0.0:8000...", file=sys.stderr)
    uvicorn.run(app, host="0.0.0.0", port=8000)
