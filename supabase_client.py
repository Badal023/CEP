from supabase import create_client, Client
from config import Config

supabase = None
try:
    supabase_key = Config.SUPABASE_SERVICE_ROLE_KEY or Config.SUPABASE_KEY
    key_type = "service_role" if Config.SUPABASE_SERVICE_ROLE_KEY else "anon"

    if Config.SUPABASE_URL and supabase_key:
        supabase = create_client(Config.SUPABASE_URL, supabase_key)
        print(f"[INFO] Supabase client initialized successfully (key={key_type})")
    else:
        print("[WARNING] Supabase credentials not configured in .env")
except Exception as e:
    print(f"[ERROR] Failed to initialize Supabase client: {e}")
