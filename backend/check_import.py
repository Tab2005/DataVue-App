import sys
import os

print(f"Python Executable: {sys.executable}")
try:
    import google.genai
    print("✅ google.genai imported successfully")
except ImportError as e:
    print(f"❌ Failed to import google.genai: {e}")

try:
    # Add current dir to path to mimic uvicorn
    sys.path.append(os.getcwd())
    from routers import ai
    print("✅ routers.ai imported successfully")
except Exception as e:
    print(f"❌ Failed to import routers.ai: {e}")
