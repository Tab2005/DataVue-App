"""Meta Graph / Marketing API 版本設定（全專案唯一來源）。

升級版本時只改 DEFAULT_META_API_VERSION；緊急回退可在 .env 設定
META_GRAPH_API_VERSION（例如 v25.0），不需改程式。
版本時程見 https://developers.facebook.com/docs/marketing-api/marketing-api-changelog
"""

import os
import re

from dotenv import load_dotenv

# 與 core/config.py 相同：確保任何進入點都讀得到 .env（不覆蓋既有環境變數）
load_dotenv()

DEFAULT_META_API_VERSION = "v27.0"

_VERSION_PATTERN = re.compile(r"^v\d+\.\d+$")


def _resolve_version() -> str:
    value = (os.getenv("META_GRAPH_API_VERSION") or "").strip()
    if not value:
        return DEFAULT_META_API_VERSION
    if not _VERSION_PATTERN.match(value):
        raise ValueError(
            f"META_GRAPH_API_VERSION 格式錯誤：{value!r}，應為像 'v27.0' 的格式"
        )
    return value


META_API_VERSION = _resolve_version()
GRAPH_API_BASE_URL = f"https://graph.facebook.com/{META_API_VERSION}"
