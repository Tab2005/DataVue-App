"""
Internal-only Meta Andromeda worker asset routes.
"""

from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile, status

from database import get_db
from database.models.meta_andromeda import MetaAndromedaAsset
from .asset_delivery import build_asset_response
from .service import MetaAndromedaService

router = APIRouter(prefix="/internal/meta-andromeda", tags=["meta_andromeda_internal"])


@router.post("/assets")
async def create_internal_asset(
    asset_type: str = Form(...),
    source_filename: str = Form(...),
    uploaded_by: str | None = Form(default=None),
    content_type: str | None = Form(default=None),
    file: UploadFile = File(...),
    x_meta_andromeda_internal_signature: str | None = Header(default=None, alias="X-Meta-Andromeda-Internal-Signature"),
    x_meta_andromeda_internal_token: str | None = Header(default=None, alias="X-Meta-Andromeda-Internal-Token"),
    db=Depends(get_db),
):
    file_bytes = await file.read()
    auth_payload = MetaAndromedaService.build_internal_worker_upload_auth_payload(
        asset_type=asset_type,
        source_filename=source_filename,
        uploaded_by=uploaded_by,
        content_type=content_type or file.content_type,
        file_bytes=file_bytes,
    )
    try:
        MetaAndromedaService.verify_internal_worker_request(
            auth_payload,
            signature=x_meta_andromeda_internal_signature,
            worker_token=x_meta_andromeda_internal_token,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    try:
        return MetaAndromedaService.upload_asset(
            db,
            file_bytes=file_bytes,
            asset_type=asset_type,
            source_filename=source_filename,
            uploaded_by=uploaded_by,
            content_type=content_type or file.content_type,
        )
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise
        if getattr(exc, "status_code", None) is not None and getattr(exc, "detail", None) is not None:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
        raise


@router.get("/assets/raw")
async def get_internal_asset_raw(
    uri: str = Query(...),
    x_meta_andromeda_internal_signature: str | None = Header(default=None, alias="X-Meta-Andromeda-Internal-Signature"),
    x_meta_andromeda_internal_token: str | None = Header(default=None, alias="X-Meta-Andromeda-Internal-Token"),
    db=Depends(get_db),
):
    try:
        MetaAndromedaService.verify_internal_worker_request(
            uri.encode("utf-8"),
            signature=x_meta_andromeda_internal_signature,
            worker_token=x_meta_andromeda_internal_token,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    asset = MetaAndromedaService.get_asset_by_uri(db, uri)
    if not asset:
        asset = db.query(MetaAndromedaAsset).filter(
            (MetaAndromedaAsset.asset_uri == uri)
            | (MetaAndromedaAsset.source_filename == uri)
            | (MetaAndromedaAsset.storage_key.endswith(uri))
        ).first()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset not found for URI: {uri}",
        )

    response = build_asset_response(asset)
    # HTTP 標頭僅允許 latin-1，storage_key 可能含中文檔名，需 percent-encode 後才能塞進標頭
    response.headers["X-Meta-Andromeda-Storage-Key"] = quote(asset.storage_key)
    return response
