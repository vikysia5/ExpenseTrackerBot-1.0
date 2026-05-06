"""
Database connection - Supabase client
"""
from functools import lru_cache
from supabase import create_client, Client
from src.core.config import settings
from src.core.logger import logger


@lru_cache()
def get_supabase() -> Client:
    """Returns singleton Supabase client"""
    logger.info("Initializing Supabase client", url=settings.SUPABASE_URL[:30] + "...")
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return client


@lru_cache()
def get_supabase_admin() -> Client:
    """Returns Supabase admin client (bypasses RLS)"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
