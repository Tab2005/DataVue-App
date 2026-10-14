"""
Ad Library - 素材圖片落地（docs/73「正式環境儲存現況」）

沿用 Meta Andromeda 的儲存管線，不另開 Volume／bucket：
  - SERVICE_ROLE=web：素材 Volume 只掛在 worker → 走
    `proxy_asset_upload_response` 經內網 HMAC 轉發給 worker 寫檔
  - 其他（all / worker）：本機持有儲存 → 直接 `MetaAndromedaService.upload_asset`
紀錄寫進 `meta_andromeda_assets`（asset_type="image"，沿用既有驗證與 >400KB 壓縮）。

讀取同理：`build_media_response` 依 storage_backend 與 SERVICE_ROLE 分流，
與 `meta_andromeda/router/scoring_assets.py::preview_asset` 相同。
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import HTTPException, status

from core.config import settings

logger = logging.getLogger(__name__)

_EXT_BY_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def ext_for_content_type(content_type: str | None) -> str | None:
    return _EXT_BY_MIME.get((content_type or "").split(";")[0].strip().lower())


async def store_image(
    *,
    file_bytes: bytes,
    content_type: str,
    filename_stem: str,
    uploaded_by: str | None,
) -> dict | None:
    """存一張圖片；回傳 {"asset_id", "asset_uri"}，不支援的格式或失敗回 None。"""
    ext = ext_for_content_type(content_type)
    if not ext:
        return None
    source_filename = f"{filename_stem}{ext}"

    try:
        if settings.SERVICE_ROLE == "web":
            from modules.meta_andromeda.internal_asset_gateway import proxy_asset_upload_response

            result = await proxy_asset_upload_response(
                asset_type="image",
                source_filename=source_filename,
                file_bytes=file_bytes,
                uploaded_by=uploaded_by,
                content_type=content_type,
            )
        else:
            result = await asyncio.to_thread(
                _store_locally, file_bytes, source_filename, uploaded_by, content_type
            )
    except Exception as exc:  # 單張失敗不阻斷整次刷新
        logger.warning("[AdLibrary] store image %s failed: %s", source_filename, exc)
        return None

    asset_id = result.get("asset_id") or result.get("id")
    asset_uri = result.get("asset_uri")
    if not asset_id or not asset_uri:
        return None
    return {"asset_id": asset_id, "asset_uri": asset_uri}


def _store_locally(file_bytes: bytes, source_filename: str, uploaded_by: str | None, content_type: str) -> dict:
    from database import SessionLocal
    from modules.meta_andromeda.service import MetaAndromedaService

    db = SessionLocal()
    try:
        return MetaAndromedaService.upload_asset(
            db,
            file_bytes=file_bytes,
            asset_type="image",
            source_filename=source_filename,
            uploaded_by=uploaded_by,
            content_type=content_type,
        )
    finally:
        db.close()


async def build_media_response(*, asset_uri: str, storage_backend: str, asset=None):
    """依儲存後端與 SERVICE_ROLE 回傳圖片內容。呼叫前須已完成授權檢查。"""
    from modules.meta_andromeda.asset_delivery import build_asset_response
    from modules.meta_andromeda.internal_asset_gateway import (
        MetaAndromedaInternalWorkerGatewayError,
        proxy_asset_preview_response,
    )

    if storage_backend == "filesystem":
        if settings.SERVICE_ROLE != "web":
            return build_asset_response(asset)
        try:
            return await proxy_asset_preview_response(asset_uri)
        except MetaAndromedaInternalWorkerGatewayError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    if storage_backend == "s3_compatible":
        return build_asset_response(asset)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="素材不存在")
