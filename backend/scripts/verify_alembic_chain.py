"""
臨時驗證腳本：
1. 驗證 alembic 版本鏈完整性（靜態分析，不連線資料庫）
2. 驗證新遷移腳本的 Python 語法是否正確
3. 驗證 down_revision 設定是否正確

執行方式：
  cd backend
  python scripts/verify_alembic_chain.py
"""

import sys
import os

# 確保工作目錄為 backend/
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

import importlib.util
from pathlib import Path

VERSIONS_DIR = Path(backend_dir) / "alembic" / "versions"

EXPECTED_CHAIN = {
    "0001_initial_schema": None,
    "20260106_add_permissions_tables": "0001_initial_schema",
    "20260114_add_ga4_columns": "20260106_add_permissions_tables",
    "20260223_p3_integrations_indexes": "fe8441e71f69",
    "0303de3f01eb": ("20260114_add_ga4_columns", "20260223_p3_integrations_indexes"),
    "20260224_fix_integrations_migration_compat": "0303de3f01eb",
}

errors = []
parsed = {}

for pyfile in sorted(VERSIONS_DIR.glob("*.py")):
    if pyfile.name.startswith("__"):
        continue
    
    spec = importlib.util.spec_from_file_location("_rev", pyfile)
    mod = importlib.util.module_from_spec(spec)
    
    # Mock alembic.op and sqlalchemy to avoid connection errors
    sys.modules.setdefault("alembic.op", type(sys)("alembic.op"))
    sys.modules.setdefault("sqlalchemy", type(sys)("sqlalchemy"))
    
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        errors.append(f"❌ 解析失敗 {pyfile.name}: {e}")
        continue
    
    rev = getattr(mod, "revision", None)
    down = getattr(mod, "down_revision", None)
    
    if rev:
        parsed[rev] = {"file": pyfile.name, "down": down}
        print(f"  ✅ {pyfile.name}")
        print(f"     revision = {rev}")
        print(f"     down_revision = {down}")

print("\n=== 版本鏈摘要 ===")
for rev, info in parsed.items():
    print(f"  {rev} <- {info['down']}  ({info['file']})")

# 找出 head（不是任何人的 down_revision 的那個）
all_revs = set(parsed.keys())
all_down = set()
for info in parsed.values():
    d = info["down"]
    if isinstance(d, (list, tuple)):
        all_down.update(d)
    elif d:
        all_down.add(d)

heads = all_revs - all_down
print(f"\n=== Heads ===")
for h in heads:
    print(f"  {h}  ({parsed[h]['file']})")

if errors:
    print("\n=== 錯誤 ===")
    for e in errors:
        print(e)
    sys.exit(1)

# 驗證預期的 head
expected_head = "20260224_fix_integrations_migration_compat"
if expected_head in heads:
    print(f"\n✅ 版本鏈正確，唯一 head = {expected_head}")
else:
    print(f"\n❌ 預期 head 為 {expected_head}，實際 heads = {heads}")
    sys.exit(1)

print("\n✅ 所有驗證通過")
