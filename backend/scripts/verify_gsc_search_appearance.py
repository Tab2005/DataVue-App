"""
Phase 0 可行性驗證腳本（docs/35_GSC_AI_Overview_生成式AI搜尋數據擴充實作規劃.md）

用途：
    呼叫 GSC Search Analytics API，dimensions=["searchAppearance"]，
    確認目前串接的帳號能否查到資料，以及回傳的 searchAppearance 列舉值中
    是否包含 AI Overview 對應項目（不硬編碼比對，僅以關鍵字提示）。

用法：
    python scripts/verify_gsc_search_appearance.py --email user@example.com --site-url sc-domain:example.com
    python scripts/verify_gsc_search_appearance.py --email user@example.com --site-url sc-domain:example.com --days 90

不帶 --site-url 時，會先列出該使用者已連接的所有站台供選擇。
本腳本只讀取資料，不寫入任何資料庫欄位。
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from database import SessionLocal, User  # noqa: E402
from gsc_service import GSCService  # noqa: E402

# 目前已知可能與 AI Overview 相關的關鍵字，僅用於「提示」，不用於篩選邏輯
AI_HINT_KEYWORDS = ["AI", "OVERVIEW", "GENERATIVE", "SGE"]


def find_user(db, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def print_sites(user: User, db) -> None:
    sites, error = GSCService.list_sites(user, db)
    if error:
        print(f"[錯誤] 無法列出站台: {error}")
        return
    print(f"使用者 {user.email} 已連接的站台（共 {len(sites or [])} 個）：")
    for s in sites or []:
        print(f"  - {s.get('siteUrl')}  (permissionLevel={s.get('permissionLevel')})")


def run(email: str, site_url: str | None, days: int) -> None:
    db = SessionLocal()
    try:
        user = find_user(db, email)
        if not user:
            print(f"[錯誤] 找不到 email={email} 的使用者")
            return

        if not user.gsc_refresh_token:
            print(f"[錯誤] 使用者 {email} 尚未連接 GSC（無 gsc_refresh_token）")
            return

        if not site_url:
            print_sites(user, db)
            print("\n請加上 --site-url 指定要驗證的站台後重新執行。")
            return

        end_date = date.today() - timedelta(days=2)  # GSC 資料通常有 1-2 天延遲
        start_date = end_date - timedelta(days=days)

        print(f"查詢站台: {site_url}")
        print(f"日期範圍: {start_date.isoformat()} ~ {end_date.isoformat()}")
        print("dimensions: ['searchAppearance']\n")

        rows, error = GSCService.get_analytics(
            user=user,
            site_url=site_url,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            dimensions=["searchAppearance"],
            db=db,
        )

        if error:
            print(f"[錯誤] API 呼叫失敗: {error}")
            return

        if not rows:
            print("[結果] 此站台在指定期間內，searchAppearance 維度沒有任何資料列。")
            print("可能原因：流量規模不足、GSC 尚未回傳此維度資料，或該站台沒有任何搜尋外觀類型曝光。")
            return

        rows_sorted = sorted(rows, key=lambda r: r.get("clicks", 0), reverse=True)

        print(f"[結果] 共取得 {len(rows_sorted)} 種 searchAppearance 類型：\n")
        header = f"{'searchAppearance':<40} {'clicks':>10} {'impressions':>12} {'ctr':>8} {'position':>10}"
        print(header)
        print("-" * len(header))

        ai_candidates = []
        for r in rows_sorted:
            key = r.get("keys", ["(unknown)"])[0]
            clicks = r.get("clicks", 0)
            impressions = r.get("impressions", 0)
            ctr = r.get("ctr", 0)
            position = r.get("position", 0)
            print(f"{key:<40} {clicks:>10} {impressions:>12} {ctr:>8.4f} {position:>10.2f}")

            if any(kw in key.upper() for kw in AI_HINT_KEYWORDS):
                ai_candidates.append(key)

        print()
        if ai_candidates:
            print(f"[提示] 以下 searchAppearance 值命中 AI 相關關鍵字，疑似對應 AI Overview：{ai_candidates}")
            print("請對照 Google 官方最新文件確認正式名稱，再決定是否寫入前端顯示邏輯。")
        else:
            print("[提示] 未發現任何命中 AI 相關關鍵字的 searchAppearance 值。")
            print("可能是此站台目前沒有 AI Overview 曝光，或 Google 尚未對此帳號/地區開放此類型資料。")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="驗證 GSC searchAppearance 維度是否可用，並提示 AI Overview 相關項目")
    parser.add_argument("--email", required=True, help="已連接 GSC 的使用者 email")
    parser.add_argument("--site-url", default=None, help="GSC 站台，例如 sc-domain:example.com 或 https://example.com/")
    parser.add_argument("--days", type=int, default=90, help="回溯查詢天數，預設 90 天")
    args = parser.parse_args()

    run(args.email, args.site_url, args.days)
