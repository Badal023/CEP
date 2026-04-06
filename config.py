import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "default-secret-key")
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "site-assets")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    SUPABASE_STORAGE_PRIVATE_BUCKET = os.getenv("SUPABASE_STORAGE_PRIVATE_BUCKET", "false").lower() in ("true", "1", "yes")
    SUPABASE_SIGNED_URL_EXPIRES_SECONDS = int(os.getenv("SUPABASE_SIGNED_URL_EXPIRES_SECONDS", "3600"))
    MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(5 * 1024 * 1024)))
    ADMIN_DEFAULT_EMAIL = os.getenv("ADMIN_DEFAULT_EMAIL", "admin@graminsanta.org")
    ADMIN_DEFAULT_PASSWORD = os.getenv("ADMIN_DEFAULT_PASSWORD", "admin123")
