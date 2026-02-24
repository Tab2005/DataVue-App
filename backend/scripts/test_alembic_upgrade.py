"""
臨時測試腳本：在臨時 SQLite DB 上執行 alembic upgrade head，
驗證所有遷移腳本（包含修復後的版本）可在 SQLite 環境正常執行。

執行方式：
  cd backend
  python scripts/test_alembic_upgrade.py
"""

import sys
import os
import subprocess

# 確保工作目錄為 backend/
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

import tempfile
from pathlib import Path

# 建立臨時 SQLite 資料庫
with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
    db_path = tmp.name

db_url = f"sqlite:///{db_path}"
print(f"[TEST] 使用臨時 SQLite DB：{db_path}")

env = os.environ.copy()
env["DATABASE_URL"] = db_url

print("[TEST] 執行 alembic upgrade head...")

result = subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"],
    cwd=backend_dir,
    env=env,
    capture_output=True,
    text=True,
    timeout=60,
)

print("[STDOUT]", result.stdout or "(empty)")
print("[STDERR]", result.stderr or "(empty)")
print(f"[EXIT CODE] {result.returncode}")

if result.returncode == 0:
    print("\n✅ alembic upgrade head 在 SQLite 環境執行成功！")
else:
    print("\n❌ alembic upgrade head 失敗")

# 清理臨時 DB
try:
    os.unlink(db_path)
except Exception:
    pass

sys.exit(result.returncode)
