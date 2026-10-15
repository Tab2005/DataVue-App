"""
Ad Library - 內容元件指紋（docs/74 第二節）

把一則已 normalize 的廣告拆成內容元件（主要文字、標題、說明、圖片、影片），
算出每個元件的指紋，以及整則廣告的 `copy_key`（文案組合）與 `media_key`
（素材組合）。純函數、不碰 DB，方便單元測試。

判定規則（docs/74 拍板決策）：
- 文字「正規化後完全相同」才算同一段；emoji、大小寫保留。
- 圖片以 Meta `image_hash` 識別，影片以 `video_id` 識別（重複上傳的同一支
  影片會被判為不同素材，已接受的限制）。
- 任何一個素材取不到識別（沒有 image_hash / video_id）→ 該廣告 `media_key`
  為 None，不參與素材比對，避免以會過期的 CDN URL 誤判。
- 輪播保留卡片順序；動態素材的順序由系統決定，排序後再組合。
- 只有商品目錄變數（例如 `{{product.name}}`）的文字不算文案：目錄廣告的實際
  文字由商品決定，若納入會讓所有目錄廣告被判為「同文案」。
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any

TEXT_KINDS = ("primary_text", "headline", "description")
MEDIA_KINDS = ("image", "video")
_TEXT_SOURCES = {"primary_text": "primary_texts", "headline": "headlines", "description": "descriptions"}
_BLANK_LINES = re.compile(r"\n{3,}")
_TEMPLATE_ONLY = re.compile(r"^(\{\{[^{}]+\}\}\s*)+$")


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = _BLANK_LINES.sub("\n\n", text)
    return text.strip()


def is_template_only(text: str) -> bool:
    return bool(_TEMPLATE_ONLY.match(text))


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def text_fingerprint(value: str) -> str:
    return "txt:" + _sha(value)


def _media_component(entry: dict) -> dict | None:
    """單一 media entry → 素材元件；取不到識別時回 None。"""
    kind = entry.get("kind")
    if kind == "video_thumbnail":
        # 影片縮圖的 image_hash 只代表縮圖，不能當影片識別
        video_id = entry.get("video_id")
        if not video_id:
            return None
        # asset_id 為影片縮圖的落地素材，供元件成效面板顯示
        return {
            "kind": "video",
            "fingerprint": f"vid:{video_id}",
            "video_id": str(video_id),
            "asset_id": entry.get("asset_id"),
        }
    image_hash = entry.get("image_hash")
    if not image_hash:
        return None
    return {
        "kind": "image",
        "fingerprint": f"img:{image_hash}",
        "image_hash": image_hash,
        "asset_id": entry.get("asset_id"),
    }


def extract_components(item: dict[str, Any]) -> dict[str, Any]:
    """拆出廣告的內容元件並算出 copy_key / media_key。

    Args:
        item: normalize_ad 的輸出（或 ad_library_items 列轉成的 dict），需含
              primary_texts / headlines / descriptions / media / media_type。

    Returns:
        {"components": [{kind, fingerprint, position, text_value|image_hash|video_id|asset_id}],
         "copy_key": str | None, "media_key": str | None}
    """
    components: list[dict] = []
    copy_parts: list[str] = []

    for kind in TEXT_KINDS:
        seen: set[str] = set()
        fps: list[str] = []
        for value in item.get(_TEXT_SOURCES[kind]) or []:
            text = normalize_text(value)
            if not text or is_template_only(text):
                continue
            fp = text_fingerprint(text)
            if fp in seen:
                continue
            seen.add(fp)
            fps.append(fp)
            components.append({"kind": kind, "fingerprint": fp, "position": len(fps) - 1, "text_value": text})
        if fps:
            copy_parts.append(f"{kind}=" + ",".join(sorted(fps)))

    media_fps: list[str] = []
    media_complete = True
    seen_media: dict[str, int] = {}
    for entry in item.get("media") or []:
        component = _media_component(entry)
        if component is None:
            media_complete = False
            continue
        media_fps.append(component["fingerprint"])
        # 同一素材在輪播中出現多次只記一個元件，但 media_key 仍保留完整順序
        if component["fingerprint"] in seen_media:
            continue
        seen_media[component["fingerprint"]] = len(seen_media)
        components.append({**component, "position": seen_media[component["fingerprint"]]})

    if item.get("media_type") != "carousel":
        media_fps = sorted(media_fps)

    return {
        "components": components,
        "copy_key": _sha("|".join(copy_parts)) if copy_parts else None,
        "media_key": _sha("|".join(media_fps)) if (media_fps and media_complete) else None,
    }
