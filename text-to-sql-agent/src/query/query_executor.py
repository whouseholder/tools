"""Query executor for running SQL queries."""

from typing import Any, Dict, List, Optional
import time

from pyhive import hive
from loguru import logger

from ..utils.config import MetadataConfig, QueryConfig


class QueryExecutor:
    """Executes SQL queries against the database."""
    
    def __init__(self, metadata_config: MetadataConfig, query_config: QueryConfig):
        """Initialize query executor."""
        self.metadata_config = metadata_config
        self.query_config = query_config
        self._connection = None
        logger.info("Query executor initialized")
    
    def _get_connection(self):
        """Get or create database connection."""
        if self._connection is None:
            hive_config = self.metadata_config.hive
            
            self._connection = hive.Connection(
                host=hive_config.get('host', 'localhost'),
                port=hive_config.get('port', 10000),
                username=hive_config.get('username', ''),
                database=hive_config.get('database', 'default'),
                auth=hive_config.get('auth_mechanism', 'PLAIN')
            )
            
            logger.info("Database connection established")
        
        return self._connection
    
    def execute_query(
        self,
        query: str,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute SQL query and return results.
        
        Returns dict with 'columns', 'rows', 'row_count', 'execution_time'.
        """
        if timeout is None:
            timeout = self.query_config.max_execution_time
        
        logger.info(f"Executing query: {query[:100]}...")
        start_time = time.time()
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Execute query
            cursor.execute(query)
            
            # Fetch results
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchmany(self.query_config.max_result_rows)
            
            execution_time = time.time() - start_time
            
            result = {
                'columns': columns,
                'rows': rows,
                'row_count': len(rows),
                'execution_time': execution_time,
                'success': True
            }
            
            logger.info(f"Query executed successfully: {len(rows)} rows in {execution_time:.2f}s")
            
            cursor.close()
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Query execution failed: {e}")
            
            return {
                'columns': [],
                'rows': [],
                'row_count': 0,
                'execution_time': execution_time,
                'success': False,
                'error': str(e)
            }
    
    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")
