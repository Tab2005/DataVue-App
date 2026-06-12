"""
Meta Andromeda Module - Storage adapter
"""

from datetime import datetime, timezone
import hashlib
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from core.config import settings


class MetaAndromedaStorageAdapter:
    """Storage adapter supporting filesystem and S3-compatible object storage."""

    @staticmethod
    def _build_storage_key(asset_id: str, source_filename: str) -> str:
        date_prefix = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        safe_name = Path(source_filename).name
        key_prefix = settings.META_ANDROMEDA_STORAGE_KEY_PREFIX.strip("/")
        key_suffix = f"uploads/{date_prefix}/{asset_id}/{safe_name}"
        if not key_prefix:
            return key_suffix
        return f"{key_prefix}/{key_suffix}"

    @staticmethod
    def _build_public_url(storage_key: str) -> str | None:
        base = settings.META_ANDROMEDA_STORAGE_PUBLIC_BASE_URL
        if not base:
            return None
        return f"{base.rstrip('/')}/{storage_key}"

    @staticmethod
    def _build_asset_record(
        *,
        asset_id: str,
        asset_uri: str,
        storage_key: str,
        asset_type: str,
        source_filename: str,
        checksum: str,
        file_size_bytes: int,
        uploaded_by: str | None,
    ) -> dict:
        return {
            "id": asset_id,
            "asset_uri": asset_uri,
            "storage_backend": settings.META_ANDROMEDA_STORAGE_BACKEND,
            "storage_key": storage_key,
            "asset_type": asset_type,
            "source_filename": Path(source_filename).name,
            "checksum_sha256": checksum,
            "upload_status": "stored",
            "file_size_bytes": file_size_bytes,
            "public_url": MetaAndromedaStorageAdapter._build_public_url(storage_key),
            "uploaded_by": uploaded_by,
            "uploaded_at": datetime.now(timezone.utc),
        }

    @staticmethod
    def _store_filesystem(file_bytes: bytes, storage_key: str) -> None:
        storage_root = Path(settings.META_ANDROMEDA_STORAGE_ROOT)
        absolute_path = storage_root / Path(storage_key)
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_bytes(file_bytes)

    @staticmethod
    def _build_s3_client():
        try:
            import boto3
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "META_ANDROMEDA_STORAGE_BACKEND=s3_compatible requires boto3 to be installed."
            ) from exc

        session = boto3.session.Session()
        client_kwargs = {
            "service_name": "s3",
            "region_name": settings.META_ANDROMEDA_STORAGE_S3_REGION,
            "aws_access_key_id": settings.META_ANDROMEDA_STORAGE_S3_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.META_ANDROMEDA_STORAGE_S3_SECRET_ACCESS_KEY,
        }
        if settings.META_ANDROMEDA_STORAGE_S3_ENDPOINT_URL:
            client_kwargs["endpoint_url"] = settings.META_ANDROMEDA_STORAGE_S3_ENDPOINT_URL
        return session.client(**client_kwargs)

    @staticmethod
    def _store_s3_compatible(file_bytes: bytes, storage_key: str, content_type: str | None = None) -> None:
        if not settings.META_ANDROMEDA_STORAGE_S3_BUCKET:
            raise RuntimeError(
                "META_ANDROMEDA_STORAGE_S3_BUCKET is required when using s3_compatible storage."
            )
        client = MetaAndromedaStorageAdapter._build_s3_client()
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        client.upload_fileobj(
            Fileobj=BytesIO(file_bytes),
            Bucket=settings.META_ANDROMEDA_STORAGE_S3_BUCKET,
            Key=storage_key,
            ExtraArgs=extra_args or None,
        )

    @staticmethod
    def store_asset(
        file_bytes: bytes,
        asset_type: str,
        source_filename: str,
        uploaded_by: str | None = None,
        content_type: str | None = None,
    ) -> dict:
        asset_id = f"asset_{uuid4().hex[:10]}"
        storage_key = MetaAndromedaStorageAdapter._build_storage_key(asset_id, source_filename)
        asset_uri = f"storage://meta-andromeda/{storage_key}"
        checksum = hashlib.sha256(file_bytes).hexdigest()
        if settings.META_ANDROMEDA_STORAGE_BACKEND == "filesystem":
            MetaAndromedaStorageAdapter._store_filesystem(file_bytes, storage_key)
        elif settings.META_ANDROMEDA_STORAGE_BACKEND == "s3_compatible":
            MetaAndromedaStorageAdapter._store_s3_compatible(file_bytes, storage_key, content_type=content_type)
        else:
            raise RuntimeError(
                f"Unsupported META_ANDROMEDA_STORAGE_BACKEND: {settings.META_ANDROMEDA_STORAGE_BACKEND}"
            )

        return MetaAndromedaStorageAdapter._build_asset_record(
            asset_id=asset_id,
            asset_uri=asset_uri,
            storage_key=storage_key,
            asset_type=asset_type,
            source_filename=source_filename,
            checksum=checksum,
            file_size_bytes=len(file_bytes),
            uploaded_by=uploaded_by,
        )


storage_adapter = MetaAndromedaStorageAdapter()
