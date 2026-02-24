"""
寫入結果到檔案的測試腳本
"""
import sys
import os
import subprocess

# 結果寫入到這個檔案
RESULT_FILE = r"d:\users\Qoo\Documents\python\DataVue-App\backend\test_result.txt"

results = []

def log(msg):
    results.append(str(msg))
    print(msg)

os.chdir(r"d:\users\Qoo\Documents\python\DataVue-App\backend")
sys.path.insert(0, r"d:\users\Qoo\Documents\python\DataVue-App\backend")

log("=== Step 1: 驗證 Python 語法 ===")

# 驗證 new migration file syntax
import ast
for fname in [
    r"d:\users\Qoo\Documents\python\DataVue-App\backend\alembic\versions\20260223_p3_integrations_indexes.py",
    r"d:\users\Qoo\Documents\python\DataVue-App\backend\alembic\versions\20260224_fix_integrations_migration_compat.py",
]:
    try:
        with open(fname, encoding="utf-8") as f:
            src = f.read()
        ast.parse(src)
        log(f"✅ 語法正確: {os.path.basename(fname)}")
    except SyntaxError as e:
        log(f"❌ 語法錯誤: {os.path.basename(fname)}: {e}")

log("\n=== Step 2: 驗證版本鏈 down_revision ===")

# Read the relevant revision values
import importlib.util
VERSIONS_DIR = r"d:\users\Qoo\Documents\python\DataVue-App\backend\alembic\versions"

# We need to mock required modules
import types

# Create a minimal mock for alembic.op and sqlalchemy
alembic_mock = types.ModuleType("alembic")
alembic_op_mock = types.ModuleType("alembic.op")
alembic_op_mock.create_table = lambda *a, **k: None
alembic_op_mock.create_index = lambda *a, **k: None 
alembic_op_mock.drop_index = lambda *a, **k: None
alembic_op_mock.drop_table = lambda *a, **k: None
alembic_op_mock.get_bind = lambda: None
alembic_op_mock.execute = lambda *a, **k: None

sa_mock = types.ModuleType("sqlalchemy")
sa_mock.Column = lambda *a, **k: None
sa_mock.String = lambda *a, **k: None
sa_mock.Text = lambda *a, **k: None
sa_mock.Integer = lambda *a, **k: None
sa_mock.Boolean = lambda *a, **k: None
sa_mock.DateTime = lambda *a, **k: None
sa_mock.JSON = lambda *a, **k: None
sa_mock.ForeignKey = lambda *a, **k: None
sa_mock.UniqueConstraint = lambda *a, **k: None
sa_mock.text = lambda s: s

sys.modules["alembic.op"] = alembic_op_mock
sys.modules["sqlalchemy"] = sa_mock

revisions = {}
for pyfile in sorted(os.listdir(VERSIONS_DIR)):
    if not pyfile.endswith(".py") or pyfile.startswith("__"):
        continue
    fpath = os.path.join(VERSIONS_DIR, pyfile)
    spec = importlib.util.spec_from_file_location(f"_rev_{pyfile}", fpath)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        rev = getattr(mod, "revision", None)
        down = getattr(mod, "down_revision", None)
        if rev:
            revisions[rev] = {"file": pyfile, "down": down}
            log(f"  {rev} <- {down}  [{pyfile}]")
    except Exception as e:
        log(f"  ⚠️ 無法解析 {pyfile}: {type(e).__name__}: {e}")

log("\n=== Step 3: 找出 HEAD ===")
all_revs = set(revisions.keys())
all_down = set()
for info in revisions.values():
    d = info["down"]
    if isinstance(d, (list, tuple)):
        all_down.update(d)
    elif d:
        all_down.add(d)
heads = all_revs - all_down
log(f"  Heads: {heads}")

expected_head = "20260224_fix_integrations_migration_compat"
if {expected_head} == heads:
    log(f"✅ 版本鏈驗證通過！Head = {expected_head}")
else:
    log(f"❌ 版本鏈異常。期望 head = {expected_head}，實際 = {heads}")

log("\n=== Step 4: alembic upgrade head (SQLite) ===")
test_db = r"d:\users\Qoo\Documents\python\DataVue-App\backend\test_migration_temp.db"
env = {**os.environ, "DATABASE_URL": f"sqlite:///{test_db.replace(chr(92), '/')}"}

r = subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"],
    cwd=r"d:\users\Qoo\Documents\python\DataVue-App\backend",
    capture_output=True,
    text=True,
    env=env,
    timeout=60,
)
log(f"  EXIT: {r.returncode}")
log(f"  STDOUT: {r.stdout[:3000] or '(empty)'}")
log(f"  STDERR: {r.stderr[:3000] or '(empty)'}")

if r.returncode == 0:
    log("✅ SQLite upgrade head 成功！")
else:
    log("❌ SQLite upgrade head 失敗")

# Cleanup
try:
    os.unlink(test_db)
except Exception:
    pass

# Write results to file
with open(RESULT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(results))
log(f"\n結果已寫入: {RESULT_FILE}")
