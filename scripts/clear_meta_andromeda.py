"""
清除 Meta Andromeda 所有評估紀錄

執行方式（在 backend/ 目錄下，並且環境變數 DATABASE_URL 已設定）：
    python ../scripts/clear_meta_andromeda.py
或從專案根目錄：
    python scripts/clear_meta_andromeda.py

DATABASE_URL 可寫在 backend/.env，腳本會自動載入。
"""

import os
import sys

# 讓 backend 目錄可以被 import
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(SCRIPT_DIR, "..", "backend")
sys.path.insert(0, os.path.abspath(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # fallback: SQLite
    SQLITE_PATH = os.path.join(BACKEND_DIR, "facebook_dashboard.db")
    DATABASE_URL = f"sqlite:///{SQLITE_PATH.replace(chr(92), '/')}"
    print(f"[INFO] DATABASE_URL 未設定，使用 SQLite: {SQLITE_PATH}")
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

# 刪除順序：先刪有 FK 依賴子表，再刪父表
TABLES_IN_ORDER = [
    "meta_andromeda_calibration_items",
    "meta_andromeda_calibration_datasets",
    "meta_andromeda_dead_letters",
    "meta_andromeda_worker_events",
    "meta_andromeda_feedback_events",
    "meta_andromeda_score_events",
    "meta_andromeda_observed_creatives",
    "meta_andromeda_drift_reports",
    "meta_andromeda_release_events",
    "meta_andromeda_release_records",
    "meta_andromeda_scoring_profiles",
    "meta_andromeda_assets",
]


def get_counts(conn):
    counts = {}
    for table in TABLES_IN_ORDER:
        try:
            row = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            counts[table] = row
        except Exception as e:
            counts[table] = f"ERROR: {e}"
    return counts


def main():
    print("=" * 60)
    print("Meta Andromeda 評估紀錄清除工具")
    print("=" * 60)
    print(f"資料庫: {str(engine.url).split('@')[-1] if '@' in str(engine.url) else engine.url}")
    print()

    with engine.connect() as conn:
        print("目前各資料表筆數：")
        counts = get_counts(conn)
        total = 0
        for table, count in counts.items():
            print(f"  {table:<50} {count}")
            if isinstance(count, int):
                total += count
        print(f"\n  合計約 {total} 筆資料")

    print()
    answer = input("確定要清除以上全部 Meta Andromeda 資料嗎？（輸入 YES 確認）: ").strip()
    if answer != "YES":
        print("已取消。")
        return

    print()
    with engine.begin() as conn:
        # PostgreSQL 需要暫時停用 FK 檢查（若資料庫支援）
        dialect = engine.dialect.name
        if dialect == "postgresql":
            conn.execute(text("SET session_replication_role = replica;"))

        for table in TABLES_IN_ORDER:
            try:
                result = conn.execute(text(f"DELETE FROM {table}"))
                print(f"  [OK] {table:<50} 刪除 {result.rowcount} 筆")
            except Exception as e:
                print(f"  [ERROR] {table}: {e}")

        if dialect == "postgresql":
            conn.execute(text("SET session_replication_role = DEFAULT;"))

    print()
    print("清除完成。下次服務啟動或呼叫 Release Overview API 時，")
    print("ensure_seed_data() 會自動補回基礎種子數據。")
    print("模型本身（model_registry）不受影響。")


if __name__ == "__main__":
    main()
