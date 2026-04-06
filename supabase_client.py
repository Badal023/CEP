from supabase import create_client, Client
from config import Config

supabase = None
try:
    if Config.SUPABASE_URL and Config.SUPABASE_KEY:
        supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        print("[INFO] Supabase client initialized successfully")
    else:
        print("[WARNING] Supabase credentials not configured in .env")
except Exception as e:
    print(f"[ERROR] Failed to initialize Supabase client: {e}")
