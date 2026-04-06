from datetime import datetime
from uuid import uuid4
import os

from werkzeug.utils import secure_filename

from config import Config
from supabase_client import supabase


ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}


class ContentServiceError(Exception):
    """Expected service-level error for CMS operations."""


def _ensure_supabase():
    if not supabase:
        raise ContentServiceError("Database not configured")


def _normalize_public_url(raw_url):
    if isinstance(raw_url, str):
        return raw_url
    if isinstance(raw_url, dict):
        return raw_url.get("publicUrl") or raw_url.get("public_url") or raw_url.get("data", {}).get("publicUrl")
    return None


def _normalize_signed_url(raw_url):
    if isinstance(raw_url, str):
        return raw_url
    if isinstance(raw_url, dict):
        return (
            raw_url.get("signedURL")
            or raw_url.get("signedUrl")
            or raw_url.get("data", {}).get("signedURL")
            or raw_url.get("data", {}).get("signedUrl")
        )
    return None


def _to_absolute_storage_url(url):
    if not url:
        return None
    if url.startswith("http://") or url.startswith("https://"):
        return url
    base = (Config.SUPABASE_URL or "").rstrip("/")
    if not base:
        return url
    if url.startswith("/storage/v1"):
        return f"{base}{url}"
    if url.startswith("/"):
        return f"{base}/storage/v1{url}"
    return f"{base}/{url.lstrip('/')}"


def create_signed_asset_url(storage_path):
    if not storage_path:
        return None
    signed = supabase.storage.from_(Config.SUPABASE_STORAGE_BUCKET).create_signed_url(
        storage_path,
        Config.SUPABASE_SIGNED_URL_EXPIRES_SECONDS,
    )
    return _to_absolute_storage_url(_normalize_signed_url(signed))


def get_content_map():
    """Return site content as a key-value dictionary for frontend consumption."""
    _ensure_supabase()
    result = supabase.table("site_content").select("key, value, type").execute()

    content = {}
    for row in (result.data or []):
        key = row["key"]
        value = row.get("value", "")
        content_type = (row.get("type") or "text").strip().lower()

        if content_type == "image" and value and Config.SUPABASE_STORAGE_PRIVATE_BUCKET:
            if value.startswith("http://") or value.startswith("https://"):
                content[key] = value
            else:
                try:
                    content[key] = create_signed_asset_url(value) or ""
                except Exception:
                    content[key] = ""
            continue

        content[key] = value

    return content


def list_content_rows():
    """Return full rows for admin listing."""
    _ensure_supabase()
    result = supabase.table("site_content").select("id, key, value, type, created_at, updated_at").order("key").execute()
    return result.data or []


def upsert_content(key, value, content_type=None):
    """Insert or update a content key using Supabase upsert."""
    _ensure_supabase()

    if not key or not key.strip():
        raise ContentServiceError("'key' is required")

    payload = {
        "key": key.strip(),
        "value": "" if value is None else str(value).strip(),
        "updated_at": datetime.utcnow().isoformat()
    }
    if content_type:
        payload["type"] = content_type.strip()

    result = supabase.table("site_content").upsert(payload, on_conflict="key").execute()
    if not result.data:
        raise ContentServiceError("Failed to update content")

    return result.data[0]


def _is_allowed_image(filename):
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS


def upload_image(file_storage):
    """Upload image to Supabase storage and return response metadata."""
    _ensure_supabase()

    if not file_storage or not file_storage.filename:
        raise ContentServiceError("No image file provided")

    if not _is_allowed_image(file_storage.filename):
        raise ContentServiceError("Unsupported image type. Allowed: png, jpg, jpeg, webp, gif")

    safe_name = secure_filename(file_storage.filename)
    ext = os.path.splitext(safe_name)[1].lower()
    unique_name = f"cms/{datetime.utcnow().strftime('%Y/%m/%d')}/{uuid4().hex}{ext}"

    file_bytes = file_storage.read()
    if not file_bytes:
        raise ContentServiceError("Uploaded file is empty")

    if len(file_bytes) > Config.MAX_UPLOAD_SIZE_BYTES:
        max_mb = Config.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise ContentServiceError(f"Image is too large. Max size is {max_mb}MB")

    try:
        supabase.storage.from_(Config.SUPABASE_STORAGE_BUCKET).upload(
            unique_name,
            file_bytes,
            {
                "content-type": file_storage.mimetype or "application/octet-stream",
                "cache-control": "3600",
                "upsert": "true"
            }
        )
    except Exception as exc:
        raise ContentServiceError(
            "Image upload failed. Ensure storage bucket exists and backend uses SUPABASE_SERVICE_ROLE_KEY. "
            f"Details: {exc}"
        ) from exc

    if Config.SUPABASE_STORAGE_PRIVATE_BUCKET:
        signed_url = create_signed_asset_url(unique_name)
        if not signed_url:
            raise ContentServiceError("Upload succeeded but failed to generate a signed URL")
        return {
            "url": signed_url,
            "stored_value": unique_name,
            "storage_path": unique_name,
            "private_bucket": True,
        }

    public_url = _normalize_public_url(
        supabase.storage.from_(Config.SUPABASE_STORAGE_BUCKET).get_public_url(unique_name)
    )

    if not public_url:
        raise ContentServiceError("Upload succeeded but failed to generate a public URL")

    return {
        "url": public_url,
        "stored_value": public_url,
        "storage_path": unique_name,
        "private_bucket": False,
    }
