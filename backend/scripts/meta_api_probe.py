"""Meta Marketing API 相容性探測（唯讀）。

用途：升級 Graph API 版本前，用真實權杖確認專案使用的 insights 欄位
與訊息行為類型在目標版本是否仍被接受。只發 GET 請求，不會修改任何廣告。

設定（寫在 backend/.env，該檔已被 .gitignore 排除）：
    META_TEST_ACCESS_TOKEN=<Graph API Explorer 產生的權杖，需 ads_read>
    META_TEST_AD_ACCOUNT_ID=act_1234567890   # 選填；未填則列出帳戶並使用第一個

執行（在 backend 目錄）：
    venv\\Scripts\\python.exe scripts\\meta_api_probe.py
    venv\\Scripts\\python.exe scripts\\meta_api_probe.py --version v24.0   # 對照舊版
"""

import argparse
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_ROOT / ".env")
sys.path.insert(0, str(BACKEND_ROOT))

from core.meta_api import META_API_VERSION  # noqa: E402

TIMEOUT = 30

# 與 modules/fb_ads/analytics_service.py 預設欄位一致
DEFAULT_FIELDS = (
    "campaign_id,adset_id,ad_id,campaign_name,adset_name,ad_name,objective,"
    "spend,impressions,reach,frequency,cpm,cpc,ctr,inline_link_clicks,clicks,unique_clicks,"
    "unique_ctr,inline_link_click_ctr,outbound_clicks,outbound_clicks_ctr,"
    "instant_experience_clicks_to_open,instant_experience_clicks_to_start,"
    "actions,action_values,purchase_roas,catalog_segment_value,catalog_segment_actions,"
    "video_p25_watched_actions,video_p50_watched_actions,video_p75_watched_actions,"
    "video_p100_watched_actions,video_avg_time_watched_actions"
)
AD_LEVEL_EXTRA = "quality_ranking,engagement_rate_ranking,conversion_rate_ranking"

# 官方最新欄位清單中找不到、需實測的欄位：(欄位, 層級)
SUSPECT_FIELDS = [
    ("unique_clicks", "account"),
    ("unique_ctr", "account"),
    ("quality_ranking", "ad"),
    ("engagement_rate_ranking", "ad"),
    ("conversion_rate_ranking", "ad"),
]

# 與 modules/fb_ads/actions_parsing.MESSAGING_ACTION_FIELDS 保持一致
MESSAGING_ACTION_TYPES = [
    "onsite_conversion.messaging_first_reply",
    "onsite_conversion.messaging_conversation_started_7d",
    "onsite_conversion.messaging_welcome_message_view",
    "onsite_conversion.total_messaging_connection",
    "onsite_conversion.messaging_user_depth_2_message_send",
    "onsite_conversion.messaging_user_depth_3_message_send",
    "onsite_conversion.messaging_conversation_replied_7d",
    "onsite_conversion.messaging_block",
]


class Probe:
    def __init__(self, token: str, version: str):
        self.base = f"https://graph.facebook.com/{version}"
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {token}"

    def get(self, path: str, **params):
        resp = self.session.get(f"{self.base}/{path.lstrip('/')}", params=params, timeout=TIMEOUT)
        try:
            body = resp.json()
        except ValueError:
            body = {"error": {"message": resp.text[:200]}}
        return resp.status_code, body


def fmt_error(body: dict) -> str:
    err = body.get("error", {})
    return (
        f"code={err.get('code')} subcode={err.get('error_subcode')} "
        f"msg={err.get('message', '')[:160]}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", default=META_API_VERSION, help=f"Graph API 版本（預設 {META_API_VERSION}）")
    parser.add_argument("--date-preset", default="last_90d")
    args = parser.parse_args()

    token = (os.getenv("META_TEST_ACCESS_TOKEN") or "").strip()
    if not token:
        print("找不到 META_TEST_ACCESS_TOKEN，請先在 backend/.env 設定。")
        return 2

    probe = Probe(token, args.version)
    print(f"== Graph API {args.version}，期間 {args.date_preset} ==\n")
    problems = 0

    # 1. 權杖與權限
    status, body = probe.get("me", fields="id,name")
    if status != 200:
        print(f"[失敗] 權杖無效：{fmt_error(body)}")
        return 1
    print(f"[OK] 權杖有效（使用者：{body.get('name')}）")

    status, body = probe.get("me/permissions")
    granted = {p["permission"] for p in body.get("data", []) if p.get("status") == "granted"}
    if "ads_read" not in granted and "ads_management" not in granted:
        print("[失敗] 權杖缺少 ads_read 權限，請在 Graph API Explorer 勾選後重新產生。")
        return 1
    print(f"[OK] 權限：{', '.join(sorted(p for p in granted if p.startswith('ads') or p.startswith('business')))}")

    # 2. 廣告帳戶
    account_id = (os.getenv("META_TEST_AD_ACCOUNT_ID") or "").strip()
    status, body = probe.get("me/adaccounts", fields="account_id,name,account_status", limit=25)
    if status != 200:
        print(f"[失敗] 無法列出廣告帳戶：{fmt_error(body)}")
        return 1
    accounts = body.get("data", [])
    print(f"[OK] 可存取 {len(accounts)} 個廣告帳戶")
    for acc in accounts[:10]:
        print(f"      act_{acc['account_id']}  {acc.get('name')}  (status={acc.get('account_status')})")
    if not account_id:
        if not accounts:
            print("[失敗] 沒有可用的廣告帳戶。")
            return 1
        account_id = f"act_{accounts[0]['account_id']}"
    if not account_id.startswith("act_"):
        account_id = f"act_{account_id}"
    print(f"\n使用帳戶：{account_id}\n")

    # 3. 專案預設欄位組合（整組送出，與正式程式相同）
    for level, fields in (("account", DEFAULT_FIELDS), ("ad", f"{DEFAULT_FIELDS},{AD_LEVEL_EXTRA}")):
        status, body = probe.get(
            f"{account_id}/insights", fields=fields, level=level, date_preset=args.date_preset, limit=5
        )
        if status == 200:
            print(f"[OK] 預設欄位組合（level={level}）被接受，回傳 {len(body.get('data', []))} 筆")
        else:
            problems += 1
            print(f"[失敗] 預設欄位組合（level={level}）被拒絕：{fmt_error(body)}")

    # 4. 可疑欄位逐一測試
    print("\n-- 可疑欄位逐一測試 --")
    for field, level in SUSPECT_FIELDS:
        status, body = probe.get(
            f"{account_id}/insights", fields=f"spend,{field}", level=level,
            date_preset=args.date_preset, limit=5,
        )
        if status != 200:
            problems += 1
            print(f"[拒絕] {field:<26} {fmt_error(body)}")
            continue
        rows = body.get("data", [])
        has_value = any(field in row for row in rows)
        note = "有回傳值" if has_value else ("接受但無值（可能此期間無資料）" if rows else "接受，此期間無資料列")
        print(f"[接受] {field:<26} {note}")

    # 5. 訊息行為類型
    print("\n-- 訊息行為類型（actions）--")
    status, body = probe.get(
        f"{account_id}/insights", fields="actions", level="account", date_preset=args.date_preset
    )
    if status != 200:
        problems += 1
        print(f"[失敗] 無法取得 actions：{fmt_error(body)}")
    else:
        seen = {}
        for row in body.get("data", []):
            for act in row.get("actions", []) or []:
                seen[act.get("action_type")] = act.get("value")
        for action_type in MESSAGING_ACTION_TYPES:
            if action_type in seen:
                print(f"[有值] {action_type} = {seen[action_type]}")
            else:
                print(f"[無值] {action_type}（若此帳戶期間內沒有訊息廣告，屬正常）")
        messaging_like = sorted(k for k in seen if k and "messag" in k)
        if messaging_like:
            print("\n此帳戶回傳的所有訊息相關 action_type：")
            for k in messaging_like:
                print(f"      {k} = {seen[k]}")

    print(f"\n== 完成：{'沒有發現問題' if problems == 0 else f'{problems} 項需要處理'} ==")
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
