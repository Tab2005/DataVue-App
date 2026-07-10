"""
Meta Andromeda asset delivery helpers.
"""

from pathlib import Path

from fastapi import HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse

from core.config import settings
from .storage import storage_adapter


def infer_asset_media_type(asset_type: str, source_filename: str) -> str:
    lowered = (source_filename or "").lower()
    if asset_type == "video":
        return "video/mp4"
    if lowered.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lowered.endswith(".gif"):
        return "image/gif"
    if lowered.endswith(".webp"):
        return "image/webp"
    return "image/png"


def resolve_filesystem_asset_path(storage_key: str) -> Path:
    storage_root = Path(settings.META_ANDROMEDA_STORAGE_ROOT).resolve()
    safe_path = (storage_root / storage_key).resolve()
    try:
        safe_path.relative_to(storage_root)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Path traversal detected.",
        ) from exc
    return safe_path


def build_filesystem_asset_response(asset) -> FileResponse:
    safe_path = resolve_filesystem_asset_path(asset.storage_key)
    if not safe_path.exists() or not safe_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset file does not exist on filesystem.",
        )
    return FileResponse(
        path=safe_path,
        media_type=infer_asset_media_type(asset.asset_type, asset.source_filename),
        filename=asset.source_filename,
    )


def build_s3_asset_response(asset) -> StreamingResponse:
    try:
        client = storage_adapter._build_s3_client()
        bucket = settings.META_ANDROMEDA_STORAGE_S3_BUCKET
        response = client.get_object(Bucket=bucket, Key=asset.storage_key)
        body = response["Body"]
        media_type = response.get("ContentType", "application/octet-stream")

        def iterfile():
            yield from body

        return StreamingResponse(iterfile(), media_type=media_type)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"S3 storage retrieval failed: {str(exc)}",
        ) from exc


def build_asset_response(asset):
    if asset.storage_backend == "filesystem":
        return build_filesystem_asset_response(asset)
    if asset.storage_backend == "s3_compatible":
        return build_s3_asset_response(asset)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported storage backend: {asset.storage_backend}",
    )
