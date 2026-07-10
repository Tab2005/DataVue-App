"""
Internal worker gateway for Meta Andromeda asset reads.
"""

import httpx
from fastapi import HTTPException, Response, status

from core.config import settings
from .service import MetaAndromedaService


class MetaAndromedaInternalWorkerGatewayError(RuntimeError):
    def __init__(self, *, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _build_internal_auth_headers(raw_payload: bytes) -> dict[str, str]:
    headers: dict[str, str] = {}
    signature = MetaAndromedaService._build_internal_worker_signature(raw_payload)
    token = settings.META_ANDROMEDA_INTERNAL_WORKER_TOKEN
    if signature:
        headers["X-Meta-Andromeda-Internal-Signature"] = signature
    if token:
        headers["X-Meta-Andromeda-Internal-Token"] = token
    return headers


async def proxy_asset_preview_response(uri: str) -> Response:
    base_url = settings.META_ANDROMEDA_INTERNAL_WORKER_BASE_URL
    if not base_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Meta Andromeda internal worker base URL is not configured.",
        )

    url = f"{base_url.rstrip('/')}/internal/meta-andromeda/assets/raw"
    try:
        async with httpx.AsyncClient(timeout=settings.META_ANDROMEDA_INTERNAL_WORKER_TIMEOUT_SECONDS) as client:
            response = await client.get(
                url,
                params={"uri": uri},
                headers=_build_internal_auth_headers(uri.encode("utf-8")),
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Meta Andromeda worker asset proxy request failed: {exc}",
        ) from exc

    if response.status_code >= 400:
        detail = response.text or "Meta Andromeda worker asset proxy failed."
        if response.headers.get("content-type", "").startswith("application/json"):
            try:
                payload = response.json()
                detail = payload.get("detail") or payload.get("error") or detail
            except ValueError:
                pass
        raise MetaAndromedaInternalWorkerGatewayError(status_code=response.status_code, detail=detail)

    passthrough_headers = {}
    content_length = response.headers.get("content-length")
    if content_length:
        passthrough_headers["Content-Length"] = content_length
    storage_key = response.headers.get("x-meta-andromeda-storage-key")
    if storage_key:
        passthrough_headers["X-Meta-Andromeda-Storage-Key"] = storage_key

    return Response(
        content=response.content,
        media_type=response.headers.get("content-type", "application/octet-stream"),
        headers=passthrough_headers,
        status_code=response.status_code,
    )


async def proxy_asset_upload_response(
    *,
    asset_type: str,
    source_filename: str,
    file_bytes: bytes,
    uploaded_by: str | None,
    content_type: str | None,
) -> dict:
    base_url = settings.META_ANDROMEDA_INTERNAL_WORKER_BASE_URL
    if not base_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Meta Andromeda internal worker base URL is not configured.",
        )

    auth_payload = MetaAndromedaService.build_internal_worker_upload_auth_payload(
        asset_type=asset_type,
        source_filename=source_filename,
        uploaded_by=uploaded_by,
        content_type=content_type,
        file_bytes=file_bytes,
    )
    url = f"{base_url.rstrip('/')}/internal/meta-andromeda/assets"
    files = {
        "file": (source_filename, file_bytes, content_type or "application/octet-stream"),
    }
    data = {
        "asset_type": asset_type,
        "source_filename": source_filename,
        "uploaded_by": uploaded_by or "",
        "content_type": content_type or "",
    }

    try:
        async with httpx.AsyncClient(timeout=settings.META_ANDROMEDA_INTERNAL_WORKER_TIMEOUT_SECONDS) as client:
            response = await client.post(
                url,
                data=data,
                files=files,
                headers=_build_internal_auth_headers(auth_payload),
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Meta Andromeda worker asset upload request failed: {exc}",
        ) from exc

    if response.status_code >= 400:
        detail = response.text or "Meta Andromeda worker asset upload failed."
        if response.headers.get("content-type", "").startswith("application/json"):
            try:
                payload = response.json()
                detail = payload.get("detail") or payload.get("error") or detail
            except ValueError:
                pass
        raise HTTPException(status_code=response.status_code, detail=detail)

    return response.json()
