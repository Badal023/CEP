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


def resolve_asset_url(value):
    if not value:
        return ""
    if not Config.SUPABASE_STORAGE_PRIVATE_BUCKET:
        return value
    if value.startswith("http://") or value.startswith("https://"):
        return value
    try:
        return create_signed_asset_url(value) or ""
    except Exception:
        return ""


def _safe_text(value):
    if value is None:
        return ""
    return str(value).strip()


def get_legacy_content_map():
    """Backward compatibility for old key-value endpoint."""
    _ensure_supabase()
    result = supabase.table("site_content").select("key, value, type").execute()
    content = {}
    for row in (result.data or []):
        value = row.get("value", "")
        if (row.get("type") or "").strip().lower() == "image":
            value = resolve_asset_url(value)
        content[row["key"]] = value
    return content


def ensure_homepage_row():
    _ensure_supabase()
    result = supabase.table("homepage").select("*").limit(1).execute()
    if result.data:
        return result.data[0]

    inserted = supabase.table("homepage").insert({
        "title": "Shiksha Sabke Liye",
        "description": "Supporting quality education across rural communities.",
        "hero_image": "",
        "notice_text": "Applications open for Tribal Scholarship Scheme 2026",
    }).execute()

    if not inserted.data:
        raise ContentServiceError("Failed to initialize homepage data")
    return inserted.data[0]


def get_homepage_content():
    row = ensure_homepage_row()
    return {
        "id": row.get("id"),
        "title": row.get("title", ""),
        "description": row.get("description", ""),
        "notice_text": row.get("notice_text", ""),
        "hero_image": resolve_asset_url(row.get("hero_image", "")),
        "hero_image_value": row.get("hero_image", ""),
    }


def update_homepage_content(payload):
    current = ensure_homepage_row()
    home_id = current.get("id")
    if not home_id:
        raise ContentServiceError("Homepage row is missing")

    update_payload = {
        "title": _safe_text(payload.get("title")),
        "description": _safe_text(payload.get("description")),
        "notice_text": _safe_text(payload.get("notice_text")),
        "hero_image": _safe_text(payload.get("hero_image")),
        "updated_at": datetime.utcnow().isoformat(),
    }

    result = supabase.table("homepage").update(update_payload).eq("id", home_id).execute()
    if not result.data:
        raise ContentServiceError("Failed to update homepage")
    return get_homepage_content()


def get_about_items():
    _ensure_supabase()
    result = supabase.table("about_items").select("id, title, description, image_url, order_index, created_at, updated_at").order("order_index").order("id").execute()
    rows = result.data or []

    image_result = supabase.table("about_item_images").select("id, about_item_id, image_url, caption, order_index").order("order_index").order("id").execute()
    image_rows = image_result.data or []
    images_by_item = {}
    for image_row in image_rows:
        about_item_id = image_row.get("about_item_id")
        if not about_item_id:
            continue
        images_by_item.setdefault(about_item_id, []).append({
            "id": image_row.get("id"),
            "about_item_id": about_item_id,
            "image_url": resolve_asset_url(image_row.get("image_url", "")),
            "image_value": image_row.get("image_url", ""),
            "caption": image_row.get("caption", ""),
            "order_index": image_row.get("order_index", 0),
        })

    normalized = []
    for row in rows:
        item_id = row.get("id")
        item_images = images_by_item.get(item_id, [])
        cover_value = row.get("image_url", "")
        if not cover_value and item_images:
            cover_value = item_images[0].get("image_value", "")
        normalized.append({
            "id": item_id,
            "title": row.get("title", ""),
            "description": row.get("description", ""),
            "image_url": resolve_asset_url(cover_value),
            "image_value": cover_value,
            "images": item_images,
            "order_index": row.get("order_index", 0),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
        })
    return normalized


def _next_about_order_index():
    result = supabase.table("about_items").select("order_index").order("order_index", desc=True).limit(1).execute()
    rows = result.data or []
    if not rows:
        return 1
    return int(rows[0].get("order_index") or 0) + 1


def add_about_item(payload):
    _ensure_supabase()
    title = _safe_text(payload.get("title"))
    description = _safe_text(payload.get("description"))
    image_url = _safe_text(payload.get("image_url"))

    if not title:
        raise ContentServiceError("About item title is required")
    if not description:
        raise ContentServiceError("About item description is required")

    insert_payload = {
        "title": title,
        "description": description,
        "image_url": image_url,
        "order_index": _next_about_order_index(),
    }

    result = supabase.table("about_items").insert(insert_payload).execute()
    if not result.data:
        raise ContentServiceError("Failed to add about item")
    new_id = result.data[0].get("id")
    items = get_about_items()
    for item in items:
        if item.get("id") == new_id:
            return item
    return items[-1] if items else None


def update_about_item(item_id, payload):
    _ensure_supabase()
    title = _safe_text(payload.get("title"))
    description = _safe_text(payload.get("description"))
    image_url = _safe_text(payload.get("image_url"))

    if not title:
        raise ContentServiceError("About item title is required")
    if not description:
        raise ContentServiceError("About item description is required")

    update_payload = {
        "title": title,
        "description": description,
        "image_url": image_url,
        "updated_at": datetime.utcnow().isoformat(),
    }
    result = supabase.table("about_items").update(update_payload).eq("id", item_id).execute()
    if not result.data:
        raise ContentServiceError("Failed to update about item")

    items = get_about_items()
    for item in items:
        if str(item.get("id")) == str(item_id):
            return item
    return None


def delete_about_item(item_id):
    _ensure_supabase()
    supabase.table("about_item_images").delete().eq("about_item_id", item_id).execute()
    result = supabase.table("about_items").delete().eq("id", item_id).execute()
    return bool(result.data)


def get_about_item_images(item_id):
    _ensure_supabase()
    result = supabase.table("about_item_images").select("id, about_item_id, image_url, caption, order_index, created_at, updated_at").eq("about_item_id", item_id).order("order_index").order("id").execute()
    rows = result.data or []
    normalized = []
    for row in rows:
        normalized.append({
            "id": row.get("id"),
            "about_item_id": row.get("about_item_id"),
            "image_url": resolve_asset_url(row.get("image_url", "")),
            "image_value": row.get("image_url", ""),
            "caption": row.get("caption", ""),
            "order_index": row.get("order_index", 0),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
        })
    return normalized


def add_about_item_image(item_id, payload):
    _ensure_supabase()
    image_url = _safe_text(payload.get("image_url"))
    caption = _safe_text(payload.get("caption"))

    if not image_url:
        raise ContentServiceError("image_url is required")

    about_item_result = supabase.table("about_items").select("id").eq("id", item_id).limit(1).execute()
    if not about_item_result.data:
        raise ContentServiceError("About item not found")

    index_result = supabase.table("about_item_images").select("order_index").eq("about_item_id", item_id).order("order_index", desc=True).limit(1).execute()
    index_rows = index_result.data or []
    next_index = int(index_rows[0].get("order_index") or 0) + 1 if index_rows else 1
    result = supabase.table("about_item_images").insert({
        "about_item_id": item_id,
        "image_url": image_url,
        "caption": caption,
        "order_index": next_index,
    }).execute()
    if not result.data:
        raise ContentServiceError("Failed to add about image")
    new_id = result.data[0].get("id")
    for image in get_about_item_images(item_id):
        if image.get("id") == new_id:
            return image
    return None


def delete_about_item_image(image_id):
    _ensure_supabase()
    result = supabase.table("about_item_images").delete().eq("id", image_id).execute()
    return bool(result.data)


def reorder_about_items(ordered_ids):
    _ensure_supabase()
    if not isinstance(ordered_ids, list) or not ordered_ids:
        raise ContentServiceError("ids array is required")

    try:
        normalized_ids = [int(item_id) for item_id in ordered_ids]
    except (TypeError, ValueError):
        raise ContentServiceError("ids must contain numeric item IDs")

    for index, item_id in enumerate(normalized_ids, start=1):
        supabase.table("about_items").update({
            "order_index": index,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", item_id).execute()
    return get_about_items()


def _next_order_index(table_name):
    result = supabase.table(table_name).select("order_index").order("order_index", desc=True).limit(1).execute()
    rows = result.data or []
    if not rows:
        return 1
    return int(rows[0].get("order_index") or 0) + 1


def get_nav_links():
    _ensure_supabase()
    result = supabase.table("nav_links").select("id, name, url, order_index").order("order_index").order("id").execute()
    return result.data or []


def add_nav_link(payload):
    _ensure_supabase()
    name = _safe_text(payload.get("name"))
    url = _safe_text(payload.get("url"))
    if not name or not url:
        raise ContentServiceError("name and url are required")
    result = supabase.table("nav_links").insert({
        "name": name,
        "url": url,
        "order_index": _next_order_index("nav_links"),
    }).execute()
    if not result.data:
        raise ContentServiceError("Failed to add nav link")
    return result.data[0]


def delete_nav_link(link_id):
    _ensure_supabase()
    result = supabase.table("nav_links").delete().eq("id", link_id).execute()
    return bool(result.data)


def get_hero_slides():
    _ensure_supabase()
    result = supabase.table("hero_slides").select("id, title, description, image_url, order_index").order("order_index").order("id").execute()
    rows = result.data or []
    for row in rows:
        row["image_url"] = resolve_asset_url(row.get("image_url", ""))
    return rows


def add_hero_slide(payload):
    _ensure_supabase()
    title = _safe_text(payload.get("title"))
    description = _safe_text(payload.get("description"))
    image_url = _safe_text(payload.get("image_url"))
    if not title or not image_url:
        raise ContentServiceError("title and image_url are required")
    result = supabase.table("hero_slides").insert({
        "title": title,
        "description": description,
        "image_url": image_url,
        "order_index": _next_order_index("hero_slides"),
    }).execute()
    if not result.data:
        raise ContentServiceError("Failed to add hero slide")
    row = result.data[0]
    return {
        "id": row.get("id"),
        "title": row.get("title", ""),
        "description": row.get("description", ""),
        "image_url": resolve_asset_url(row.get("image_url", "")),
        "order_index": row.get("order_index", 0),
    }


def delete_hero_slide(slide_id):
    _ensure_supabase()
    result = supabase.table("hero_slides").delete().eq("id", slide_id).execute()
    return bool(result.data)


def get_notices():
    _ensure_supabase()
    result = supabase.table("notices").select("id, text, link_url, order_index").order("order_index").order("id").execute()
    return result.data or []


def add_notice(payload):
    _ensure_supabase()
    text = _safe_text(payload.get("text"))
    link_url = _safe_text(payload.get("link_url"))
    if not text:
        raise ContentServiceError("text is required")
    result = supabase.table("notices").insert({
        "text": text,
        "link_url": link_url,
        "order_index": _next_order_index("notices"),
    }).execute()
    if not result.data:
        raise ContentServiceError("Failed to add notice")
    return result.data[0]


def delete_notice(notice_id):
    _ensure_supabase()
    result = supabase.table("notices").delete().eq("id", notice_id).execute()
    return bool(result.data)


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
