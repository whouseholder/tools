"""Query executor for running SQL queries against multiple database types."""

from typing import Any, Dict, List, Optional
import time
import sqlite3

# Optional imports for different database types
try:
    from pyhive import hive
    HIVE_AVAILABLE = True
except ImportError:
    HIVE_AVAILABLE = False
    hive = None

try:
    from impala.dbapi import connect as impala_connect
    IMPALA_AVAILABLE = True
except ImportError:
    IMPALA_AVAILABLE = False
    impala_connect = None

try:
    from databricks import sql as databricks_sql
    DATABRICKS_AVAILABLE = True
except ImportError:
    DATABRICKS_AVAILABLE = False
    databricks_sql = None

try:
    import snowflake.connector
    SNOWFLAKE_AVAILABLE = True
except ImportError:
    SNOWFLAKE_AVAILABLE = False
    snowflake = None

try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    psycopg2 = None

try:
    import pymysql
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    pymysql = None

from loguru import logger

from ..utils.config import MetadataConfig, QueryConfig


class QueryExecutor:
    """Executes SQL queries against various database types."""
    
    SUPPORTED_DATABASES = {
        'sqlite': {'requires': 'sqlite3 (built-in)', 'available': True},
        'hive': {'requires': 'pyhive', 'available': HIVE_AVAILABLE},
        'impala': {'requires': 'impyla', 'available': IMPALA_AVAILABLE},
        'databricks': {'requires': 'databricks-sql-connector', 'available': DATABRICKS_AVAILABLE},
        'snowflake': {'requires': 'snowflake-connector-python', 'available': SNOWFLAKE_AVAILABLE},
        'postgres': {'requires': 'psycopg2', 'available': POSTGRES_AVAILABLE},
        'mysql': {'requires': 'pymysql', 'available': MYSQL_AVAILABLE}
    }
    
    def __init__(self, metadata_config: MetadataConfig, query_config: QueryConfig):
        """Initialize query executor."""
        self.metadata_config = metadata_config
        self.query_config = query_config
        self._connection = None
        
        # Determine database type
        self.db_type = getattr(query_config, 'dialect', 'hive').lower()
        
        # Check if database type is supported
        if self.db_type not in self.SUPPORTED_DATABASES:
            logger.warning(f"Unknown database type: {self.db_type}, defaulting to sqlite")
            self.db_type = 'sqlite'
        
        db_info = self.SUPPORTED_DATABASES[self.db_type]
        if not db_info['available']:
            logger.warning(f"{self.db_type} support not available - requires {db_info['requires']}")
            if self.db_type != 'sqlite':
                logger.warning("Falling back to SQLite mode")
                self.db_type = 'sqlite'
        
        self.sqlite_path = getattr(query_config, 'sqlite_path', 'data/telco_sample.db')
        
        logger.info(f"Query executor initialized (type: {self.db_type.upper()})")
    
    def _get_connection(self):
        """Get or create database connection based on type."""
        if self.db_type == 'sqlite':
            return None  # SQLite uses per-query connections
        
        if self._connection is not None:
            return self._connection
        
        if self.db_type == 'hive':
            if not HIVE_AVAILABLE:
                raise RuntimeError("pyhive is not available - cannot connect to Hive")
            
            hive_config = self.metadata_config.hive
            self._connection = hive.Connection(
                host=hive_config.get('host', 'localhost'),
                port=hive_config.get('port', 10000),
                username=hive_config.get('username', ''),
                database=hive_config.get('database', 'default'),
                auth=hive_config.get('auth_mechanism', 'PLAIN')
            )
            logger.info("Hive connection established")
        
        elif self.db_type == 'impala':
            if not IMPALA_AVAILABLE:
                raise RuntimeError("impyla is not available - cannot connect to Impala")
            
            impala_config = self.metadata_config.hive
            self._connection = impala_connect(
                host=impala_config.get('host', 'localhost'),
                port=impala_config.get('port', 21050),
                database=impala_config.get('database', 'default'),
                auth_mechanism=impala_config.get('auth_mechanism', 'PLAIN')
            )
            logger.info("Impala connection established")
        
        elif self.db_type == 'databricks':
            if not DATABRICKS_AVAILABLE:
                raise RuntimeError("databricks-sql-connector is not available")
            
            databricks_config = self.metadata_config.hive
            self._connection = databricks_sql.connect(
                server_hostname=databricks_config.get('host'),
                http_path=databricks_config.get('http_path', '/sql/1.0/warehouses/'),
                access_token=databricks_config.get('token', ''),
                catalog=databricks_config.get('catalog', 'main'),
                schema=databricks_config.get('database', 'default')
            )
            logger.info("Databricks connection established")
        
        elif self.db_type == 'snowflake':
            if not SNOWFLAKE_AVAILABLE:
                raise RuntimeError("snowflake-connector-python is not available")
            
            snowflake_config = self.metadata_config.hive
            self._connection = snowflake.connector.connect(
                user=snowflake_config.get('username', ''),
                password=snowflake_config.get('password', ''),
                account=snowflake_config.get('account', ''),
                warehouse=snowflake_config.get('warehouse', ''),
                database=snowflake_config.get('database', ''),
                schema=snowflake_config.get('schema', 'public')
            )
            logger.info("Snowflake connection established")
        
        elif self.db_type == 'postgres':
            if not POSTGRES_AVAILABLE:
                raise RuntimeError("psycopg2 is not available")
            
            pg_config = self.metadata_config.hive
            self._connection = psycopg2.connect(
                host=pg_config.get('host', 'localhost'),
                port=pg_config.get('port', 5432),
                database=pg_config.get('database', 'postgres'),
                user=pg_config.get('username', ''),
                password=pg_config.get('password', '')
            )
            logger.info("PostgreSQL connection established")
        
        elif self.db_type == 'mysql':
            if not MYSQL_AVAILABLE:
                raise RuntimeError("pymysql is not available")
            
            mysql_config = self.metadata_config.hive
            self._connection = pymysql.connect(
                host=mysql_config.get('host', 'localhost'),
                port=mysql_config.get('port', 3306),
                database=mysql_config.get('database', ''),
                user=mysql_config.get('username', ''),
                password=mysql_config.get('password', '')
            )
            logger.info("MySQL connection established")
        
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
        
        logger.info(f"Executing query on {self.db_type.upper()}: {query[:100]}...")
        logger.debug(f"Full query to execute: {query}")
        logger.debug(f"Database type: {self.db_type}")
        logger.debug(f"SQLite path: {self.sqlite_path if self.db_type == 'sqlite' else 'N/A'}")
        
        start_time = time.time()
        
        try:
            if self.db_type == 'sqlite':
                # SQLite uses per-query connections
                logger.debug(f"Connecting to SQLite database: {self.sqlite_path}")
                conn = sqlite3.connect(self.sqlite_path)
                cursor = conn.cursor()
                
                logger.debug("Executing query on SQLite...")
                cursor.execute(query)
                
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                logger.debug(f"Query returned columns: {columns}")
                
                rows = cursor.fetchmany(self.query_config.max_result_rows)
                logger.debug(f"Fetched {len(rows)} rows")
                
                cursor.close()
                conn.close()
            else:
                # Other databases use persistent connections
                logger.debug(f"Getting connection for {self.db_type}...")
                conn = self._get_connection()
                cursor = conn.cursor()
                
                logger.debug("Executing query...")
                cursor.execute(query)
                
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                logger.debug(f"Query returned columns: {columns}")
                
                rows = cursor.fetchmany(self.query_config.max_result_rows)
                logger.debug(f"Fetched {len(rows)} rows")
                
                cursor.close()
            
            execution_time = time.time() - start_time
            
            result = {
                'columns': columns,
                'rows': rows,
                'row_count': len(rows),
                'execution_time': execution_time,
                'success': True
            }
            
            logger.info(f"Query executed successfully: {len(rows)} rows in {execution_time:.2f}s")
            if len(rows) == 0:
                logger.warning("Query returned 0 rows - data may not exist in database")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Query execution failed: {e}")
            logger.exception("Full exception traceback:")
            
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
            try:
                self._connection.close()
                logger.info(f"{self.db_type.upper()} connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
            finally:
                self._connection = None
                logger.info("Database connection closed")
