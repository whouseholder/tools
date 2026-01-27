"""Metadata management and indexing for Hive metastore."""

from typing import Any, Dict, List, Optional
import time

from pyhive import hive
from loguru import logger

from ..vector_store.vector_store import VectorStore
from ..utils.config import MetadataConfig


class MetadataManager:
    """Manages metadata from Hive metastore and indexes it in vector store."""
    
    def __init__(
        self,
        vector_store: VectorStore,
        config: MetadataConfig
    ):
        """Initialize metadata manager."""
        self.vector_store = vector_store
        self.config = config
        self._connection = None
        self._last_refresh = 0
        self._metadata_cache: Dict[str, Dict[str, Any]] = {}
        logger.info("Metadata manager initialized")
    
    def _get_connection(self):
        """Get or create database connection."""
        if self._connection is None:
            hive_config = self.config.hive
            
            self._connection = hive.Connection(
                host=hive_config.get('host', 'localhost'),
                port=hive_config.get('port', 10000),
                username=hive_config.get('username', ''),
                database=hive_config.get('database', 'default'),
                auth=hive_config.get('auth_mechanism', 'PLAIN')
            )
            
            logger.info("Metadata connection established")
        
        return self._connection
    
    def fetch_table_metadata(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Fetch metadata for a specific table."""
        # Check cache first
        cache_key = table_name.lower()
        if cache_key in self._metadata_cache:
            cache_age = time.time() - self._metadata_cache[cache_key].get('cached_at', 0)
            if cache_age < self.config.cache_ttl:
                logger.debug(f"Using cached metadata for {table_name}")
                return self._metadata_cache[cache_key]
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Fetch column information
            cursor.execute(f"DESCRIBE {table_name}")
            columns_raw = cursor.fetchall()
            
            columns = []
            for row in columns_raw:
                col_name = row[0]
                col_type = row[1]
                col_comment = row[2] if len(row) > 2 else ""
                
                columns.append({
                    'name': col_name,
                    'type': col_type,
                    'description': col_comment
                })
            
            # Try to get table comment
            try:
                cursor.execute(f"SHOW CREATE TABLE {table_name}")
                create_stmt = cursor.fetchone()[0]
                
                # Extract comment from CREATE TABLE statement
                import re
                comment_match = re.search(r"COMMENT\s+'([^']+)'", create_stmt)
                table_description = comment_match.group(1) if comment_match else ""
            except:
                table_description = ""
            
            metadata = {
                'table_name': table_name,
                'description': table_description,
                'columns': columns,
                'cached_at': time.time()
            }
            
            # Update cache
            self._metadata_cache[cache_key] = metadata
            
            cursor.close()
            logger.info(f"Fetched metadata for {table_name}: {len(columns)} columns")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to fetch metadata for {table_name}: {e}")
            return None
    
    def fetch_all_tables(self) -> List[str]:
        """Fetch list of all tables in the database."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            logger.info(f"Found {len(tables)} tables in database")
            return tables
            
        except Exception as e:
            logger.error(f"Failed to fetch table list: {e}")
            return []
    
    def index_table(self, table_name: str) -> bool:
        """Index a table's metadata in the vector store."""
        metadata = self.fetch_table_metadata(table_name)
        
        if metadata:
            try:
                self.vector_store.add_metadata(
                    table_name=metadata['table_name'],
                    columns=metadata['columns'],
                    description=metadata['description']
                )
                logger.info(f"Indexed table: {table_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to index table {table_name}: {e}")
                return False
        
        return False
    
    def index_all_tables(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Index all tables in the database.
        
        Args:
            force_refresh: If True, ignore last refresh time
        
        Returns:
            Dict with indexing statistics
        """
        # Check if refresh is needed
        if not force_refresh:
            time_since_refresh = time.time() - self._last_refresh
            if time_since_refresh < self.config.index_refresh_interval:
                logger.info(f"Skipping index refresh (last refresh {time_since_refresh:.0f}s ago)")
                return {
                    'refreshed': False,
                    'reason': 'refresh_interval_not_reached'
                }
        
        logger.info("Starting full metadata indexing")
        start_time = time.time()
        
        tables = self.fetch_all_tables()
        
        stats = {
            'refreshed': True,
            'total_tables': len(tables),
            'indexed': 0,
            'failed': 0,
            'duration': 0
        }
        
        for table in tables:
            if self.index_table(table):
                stats['indexed'] += 1
            else:
                stats['failed'] += 1
        
        stats['duration'] = time.time() - start_time
        self._last_refresh = time.time()
        
        logger.info(
            f"Indexing complete: {stats['indexed']}/{stats['total_tables']} tables "
            f"in {stats['duration']:.2f}s"
        )
        
        return stats
    
    def get_relevant_tables(
        self,
        question: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Get relevant tables for a question using vector search."""
        return self.vector_store.search_relevant_metadata(question, top_k)
    
    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Metadata connection closed")
