"""Database utilities for Supabase connection"""
import os
from supabase import create_client, Client
from typing import Optional, List, Dict, Any, cast
import logging

logger = logging.getLogger(__name__)

# Compatibility patch: Supabase 1.0.3 enforces legacy JWT regex on API keys.
# Modern Supabase projects use sb_secret_ / sb_publishable_ keys which are valid for PostgREST.
try:
    import re
    import supabase.client as _sc
    _orig_client_init = _sc.Client.__init__

    def _patched_client_init(self, supabase_url: str, supabase_key: str, options=None):
        if options is None:
            from supabase.lib.client_options import ClientOptions
            options = ClientOptions()
        try:
            _orig_client_init(self, supabase_url, supabase_key, options)
        except Exception as err:
            if "Invalid API key" in str(err) and supabase_key and (supabase_key.startswith("sb_") or "." not in supabase_key):
                self.supabase_url = supabase_url
                self.supabase_key = supabase_key
                options.headers.update(self._get_auth_headers())
                self.rest_url = f"{supabase_url}/rest/v1"
                self.realtime_url = f"{supabase_url}/realtime/v1".replace("http", "ws")
                self.auth_url = f"{supabase_url}/auth/v1"
                self.storage_url = f"{supabase_url}/storage/v1"
                if re.search(r"(supabase\.co)|(supabase\.in)", supabase_url):
                    url_parts = supabase_url.split(".")
                    self.functions_url = f"{url_parts[0]}.functions.{url_parts[1]}.{url_parts[2]}"
                else:
                    self.functions_url = f"{supabase_url}/functions/v1"
                self.schema = options.schema
                self.auth = self._init_supabase_auth_client(auth_url=self.auth_url, client_options=options)
                self.realtime = None
                self.postgrest = self._init_postgrest_client(
                    rest_url=self.rest_url,
                    supabase_key=self.supabase_key,
                    headers=options.headers,
                    schema=options.schema,
                    timeout=options.postgrest_client_timeout,
                )
                self.storage = self._init_storage_client(
                    self.storage_url, self._get_auth_headers(), options.storage_client_timeout
                )
            else:
                raise

    _sc.Client.__init__ = _patched_client_init
except Exception:
    pass


class SupabaseDB:
    """Supabase database wrapper"""
    
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client"""
        if cls._instance is None:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                from dotenv import load_dotenv
                _bdir = os.path.dirname(os.path.abspath(__file__))
                for _ef in [os.path.join(_bdir, '.env'), os.path.abspath(os.path.join(_bdir, '..', '.env'))]:
                    if os.path.exists(_ef):
                        load_dotenv(_ef)
                supabase_url = os.getenv('SUPABASE_URL')
                supabase_key = os.getenv('SUPABASE_KEY')

            if not supabase_url or not supabase_key:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
            
            schema = os.getenv('SUPABASE_SCHEMA', 'public').strip() or 'public'
            from supabase.lib.client_options import ClientOptions
            cls._instance = create_client(supabase_url, supabase_key, options=ClientOptions(schema=schema))
        
        assert cls._instance is not None
        return cls._instance

    @classmethod
    def get_table(cls, table: str):
        """Get table reference with optional custom schema (e.g. ess_portal or public)"""
        client = cls.get_client()
        schema = os.getenv('SUPABASE_SCHEMA', 'public').strip()
        if schema and schema != 'public':
            return client.postgrest.schema(schema).table(table)
        return client.table(table)
    
    @staticmethod
    def insert(table: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a record"""
        try:
            response = SupabaseDB.get_table(table).insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Insert error in {table}: {str(e)}")
            raise
    
    @staticmethod
    def insert_many(table: str, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Insert multiple records"""
        try:
            response = SupabaseDB.get_table(table).insert(data).execute()
            return response.data
        except Exception as e:
            logger.error(f"Batch insert error in {table}: {str(e)}")
            raise

    @staticmethod
    def upsert(table: str, data: Dict[str, Any], on_conflict: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Upsert a single record"""
        try:
            tbl = SupabaseDB.get_table(table)
            query = tbl.upsert(data, on_conflict=on_conflict) if on_conflict else tbl.upsert(data)
            response = query.execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Upsert error in {table}: {str(e)}")
            raise

    @staticmethod
    def upsert_many(table: str, data: List[Dict[str, Any]], on_conflict: Optional[str] = None) -> List[Dict[str, Any]]:
        """Upsert multiple records"""
        try:
            tbl = SupabaseDB.get_table(table)
            # postgrest-py type hints annotate json as dict instead of Union[dict, list],
            # but PostgREST supports batch upserting via a list of records at runtime.
            payload = cast(Any, data)
            query = tbl.upsert(payload, on_conflict=on_conflict) if on_conflict else tbl.upsert(payload)
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Batch upsert error in {table}: {str(e)}")
            raise
    
    @staticmethod
    def select(table: str, columns: str = "*", filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Select records with optional filters"""
        try:
            query = SupabaseDB.get_table(table).select(columns)
            
            if filters:
                for key, value in filters.items():
                    if isinstance(value, tuple):
                        op, val = value
                        method = getattr(query, op, None)
                        if method:
                            query = method(key, val)
                    else:
                        query = query.eq(key, value)
            
            response = query.execute()
            return cast(List[Dict[str, Any]], response.data)
        except Exception as e:
            logger.error(f"Select error from {table}: {str(e)}")
            raise
    
    @staticmethod
    def select_one(table: str, filters: Dict) -> Optional[Dict[str, Any]]:
        """Select a single record"""
        try:
            results = SupabaseDB.select(table, "*", filters)
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Select one error from {table}: {str(e)}")
            raise
    
    @staticmethod
    def update(table: str, filters: Dict, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update records"""
        try:
            query = SupabaseDB.get_table(table).update(data)
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            response = query.execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Update error in {table}: {str(e)}")
            raise
    
    @staticmethod
    def delete(table: str, filters: Dict) -> bool:
        """Delete records"""
        try:
            query = SupabaseDB.get_table(table).delete()
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            response = query.execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Delete error from {table}: {str(e)}")
            raise
    
    @staticmethod
    def count(table: str, filters: Optional[Dict] = None) -> int:
        """Count records"""
        try:
            query = SupabaseDB.get_table(table).select("id", count="exact")  # type: ignore[arg-type]
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            response = query.execute()
            return response.count if response.count is not None else 0
        except Exception as e:
            logger.error(f"Count error on {table}: {str(e)}")
            raise
