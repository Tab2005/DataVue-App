import sys
import traceback

print("Attempting to import main...")
try:
    import main
    print("Main imported successfully")
except Exception:
    traceback.print_exc()
except SystemExit as e:
    print(f"SystemExit: {e}")
