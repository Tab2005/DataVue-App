"""AssetServiceMixin for Meta Andromeda service."""

from ._shared import *  # noqa: F403


class AssetServiceMixin:

    @staticmethod
    def get_asset_by_uri(db, asset_uri: str):
        return repository.get_asset_by_uri(db, asset_uri)


    @staticmethod
    def upload_asset(
        db,
        file_bytes: bytes,
        asset_type: str,
        source_filename: str,
        uploaded_by: str | None = None,
        content_type: str | None = None,
    ) -> dict:
        # 自動壓縮圖片素材，避免過大導致 AI 服務超載或超時
        if asset_type == "image":
            file_bytes = MetaAndromedaService._compress_image(file_bytes, source_filename, content_type)

        MetaAndromedaService._validate_uploaded_asset(
            file_bytes=file_bytes,
            asset_type=asset_type,
            source_filename=source_filename,
            content_type=content_type,
        )
        asset_record = storage_adapter.store_asset(
            file_bytes=file_bytes,
            asset_type=asset_type,
            source_filename=source_filename,
            uploaded_by=uploaded_by,
            content_type=content_type,
        )
        return repository.create_uploaded_asset(db, asset_record=asset_record)


    @staticmethod
    def _compress_image(file_bytes: bytes, filename: str, content_type: str | None = None) -> bytes:
        import io
        from PIL import Image
        from pathlib import Path

        # 如果檔案本身就小於 400KB，直接保留原圖以保證最高精度與速度
        if len(file_bytes) < 400 * 1024:
            logger.info("[MetaAndromeda] Image size is %d bytes (<400KB), skipping compression.", len(file_bytes))
            return file_bytes

        try:
            img = Image.open(io.BytesIO(file_bytes))
            orig_format = img.format
            width, height = img.size
            
            fmt_lower = (orig_format or "").lower()
            if not fmt_lower:
                suffix = Path(filename).suffix.lower()
                if suffix in (".jpg", ".jpeg"):
                    fmt_lower = "jpeg"
                elif suffix == ".webp":
                    fmt_lower = "webp"
                else:
                    fmt_lower = "png"

            # 設定最長邊最大寬高為 1200 像素
            max_size = 1200
            if width > max_size or height > max_size:
                if width > height:
                    new_width = max_size
                    new_height = int(height * (max_size / width))
                else:
                    new_height = max_size
                    new_width = int(width * (max_size / height))
                
                logger.info(
                    "[MetaAndromeda] Resizing image from %dx%d to %dx%d (max_size=%d)",
                    width, height, new_width, new_height, max_size
                )
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            out_buf = io.BytesIO()
            save_kwargs = {}
            
            if fmt_lower in ("jpeg", "jpg"):
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")
                save_kwargs = {"quality": 85, "optimize": True}
                save_format = "JPEG"
            elif fmt_lower == "webp":
                save_kwargs = {"quality": 85, "method": 6}
                save_format = "WEBP"
            else:
                save_kwargs = {"optimize": True}
                save_format = "PNG"

            img.save(out_buf, format=save_format, **save_kwargs)
            compressed_bytes = out_buf.getvalue()
            
            logger.info(
                "[MetaAndromeda] Image compressed. Before: %d bytes, After: %d bytes (Ratio: %.1f%%)",
                len(file_bytes), len(compressed_bytes), (len(compressed_bytes) / len(file_bytes)) * 100
            )
            
            if len(compressed_bytes) >= len(file_bytes):
                logger.info("[MetaAndromeda] Compressed image is larger or equal, keeping original.")
                return file_bytes
                
            return compressed_bytes

        except Exception as e:
            logger.warning("[MetaAndromeda] Image compression failed: %s. Using original bytes.", e)
            return file_bytes


    @staticmethod
    def _validate_uploaded_asset(
        *,
        file_bytes: bytes,
        asset_type: str,
        source_filename: str,
        content_type: str | None,
    ) -> None:
        if not file_bytes:
            raise MetaAndromedaValidationError("upload_empty_file", status_code=400)
        if len(file_bytes) > settings.META_ANDROMEDA_UPLOAD_MAX_BYTES:
            raise MetaAndromedaValidationError("upload_file_too_large", status_code=413)

        allowed = {
            "image": {
                "mimes": {"image/png", "image/jpeg", "image/webp"},
                "exts": {".png", ".jpg", ".jpeg", ".webp"},
            },
            "video": {
                "mimes": {"video/mp4", "video/quicktime"},
                "exts": {".mp4", ".mov"},
            },
        }
        spec = allowed.get((asset_type or "").strip().lower())
        if spec is None:
            raise MetaAndromedaValidationError("unsupported_asset_type", status_code=415)

        content_type_normalized = (content_type or "").split(";")[0].strip().lower()
        ext = Path(source_filename or "").suffix.lower()
        if ext not in spec["exts"]:
            raise MetaAndromedaValidationError("upload_extension_not_allowed", status_code=415)
        if content_type_normalized not in spec["mimes"]:
            raise MetaAndromedaValidationError("upload_mime_not_allowed", status_code=415)


    @staticmethod
    def _is_allowed_media_host(hostname: str | None) -> bool:
        if not hostname:
            return False
        host = hostname.lower()
        for allowed in settings.META_ANDROMEDA_ALLOWED_MEDIA_HOSTS:
            normalized = allowed.lstrip(".")
            if host == normalized or host.endswith(f".{normalized}"):
                return True
        return False
