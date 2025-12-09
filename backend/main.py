from fastapi import FastAPI
import uvicorn
import sys

print("🚀 MINIMAL MAIN: STARTING...", file=sys.stderr)

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "minimal_main_ok", "message": "If you see this, the pipeline is OK. The bug is in the full code."}

if __name__ == "__main__":
    print("🚀 MINIMAL MAIN: RUNNING UVICORN...", file=sys.stderr)
    uvicorn.run(app, host="0.0.0.0", port=8000)
