"""Metadata management for multiple database types.

Supports:
- Hive
- Impala
- Iceberg REST Catalog
- Databricks
- Snowflake
- SQLite (local testing)
- PostgreSQL
- MySQL
"""

from typing import Any, Dict, List, Optional
import time

# Optional imports for different database types
try:
    from pyhive import hive
    HIVE_AVAILABLE = True
except ImportError:
    HIVE_AVAILABLE = False
    hive = None

try:
    from pyhive import presto
    PRESTO_AVAILABLE = True
except ImportError:
    PRESTO_AVAILABLE = False
    presto = None

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

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

from loguru import logger

from ..vector_store.vector_store import VectorStore
from ..utils.config import MetadataConfig


class MetadataManager:
    """Manages metadata from various database types and indexes in vector store."""
    
    SUPPORTED_DATABASES = {
        'sqlite': {'requires': 'sqlite3 (built-in)', 'available': True},
        'hive': {'requires': 'pyhive', 'available': HIVE_AVAILABLE},
        'impala': {'requires': 'impyla', 'available': IMPALA_AVAILABLE},
        'databricks': {'requires': 'databricks-sql-connector', 'available': DATABRICKS_AVAILABLE},
        'snowflake': {'requires': 'snowflake-connector-python', 'available': SNOWFLAKE_AVAILABLE},
        'postgres': {'requires': 'psycopg2', 'available': POSTGRES_AVAILABLE},
        'mysql': {'requires': 'pymysql', 'available': MYSQL_AVAILABLE},
        'iceberg': {'requires': 'requests', 'available': REQUESTS_AVAILABLE}
    }
    
    def __init__(
        self,
        vector_store: VectorStore,
        metadata_config: MetadataConfig,
        query_config
    ):
        """Initialize metadata manager."""
        self.vector_store = vector_store
        self.config = metadata_config
        self.query_config = query_config
        self._connection = None
        self._last_refresh = 0
        self._metadata_cache: Dict[str, Dict[str, Any]] = {}

        # Determine database type from config
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

        # SQLite-specific config
        self.sqlite_path = getattr(query_config, 'sqlite_path', 'data/telco_sample.db')

        logger.info(f"Metadata manager initialized (type: {self.db_type.upper()})")
    
    def get_database_info(self) -> Dict[str, str]:
        """Get database type and version information for SQL generation."""
        info = {
            'type': self.db_type.upper(),
            'dialect': self.db_type,
            'version': 'unknown'
        }
        
        try:
            conn = self._get_connection()
            
            if self.db_type == 'sqlite':
                import sqlite3
                info['version'] = sqlite3.sqlite_version
                info['description'] = 'SQLite embedded database'
            
            elif self.db_type in ['hive', 'impala']:
                cursor = conn.cursor()
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()
                info['version'] = version[0] if version else 'unknown'
                info['description'] = f'{self.db_type.title()} data warehouse'
            
            elif self.db_type == 'databricks':
                cursor = conn.cursor()
                cursor.execute("SELECT version()")
                version = cursor.fetchone()
                info['version'] = version[0] if version else 'unknown'
                info['description'] = 'Databricks SQL warehouse'
            
            elif self.db_type == 'snowflake':
                cursor = conn.cursor()
                cursor.execute("SELECT CURRENT_VERSION()")
                version = cursor.fetchone()
                info['version'] = version[0] if version else 'unknown'
                info['description'] = 'Snowflake data warehouse'
            
            elif self.db_type == 'postgres':
                cursor = conn.cursor()
                cursor.execute("SELECT version()")
                version = cursor.fetchone()
                if version:
                    # Extract version number from PostgreSQL version string
                    import re
                    match = re.search(r'PostgreSQL (\d+\.\d+)', version[0])
                    info['version'] = match.group(1) if match else version[0]
                info['description'] = 'PostgreSQL relational database'
            
            elif self.db_type == 'mysql':
                cursor = conn.cursor()
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()
                info['version'] = version[0] if version else 'unknown'
                info['description'] = 'MySQL relational database'
            
            elif self.db_type == 'iceberg':
                info['version'] = 'REST API'
                info['description'] = 'Apache Iceberg REST catalog'
        
        except Exception as e:
            logger.warning(f"Could not retrieve database version: {e}")
        
        return info
    
    def _get_connection(self):
        """Get or create database connection based on type."""
        if self._connection is not None:
            return self._connection
        
        if self.db_type == 'sqlite':
            return None  # SQLite uses per-query connections
        
        elif self.db_type == 'hive':
            if not HIVE_AVAILABLE:
                raise RuntimeError("pyhive is not available - cannot connect to Hive")
            
            hive_config = self.config.hive
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
            
            impala_config = self.config.hive
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
            
            databricks_config = self.config.hive
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
            
            snowflake_config = self.config.hive
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
            
            pg_config = self.config.hive
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
            
            mysql_config = self.config.hive
            self._connection = pymysql.connect(
                host=mysql_config.get('host', 'localhost'),
                port=mysql_config.get('port', 3306),
                database=mysql_config.get('database', ''),
                user=mysql_config.get('username', ''),
                password=mysql_config.get('password', '')
            )
            logger.info("MySQL connection established")
        
        return self._connection
    
    def _get_sqlite_metadata(self) -> List[Dict[str, Any]]:
        """Get metadata from SQLite database."""
        import sqlite3
        
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            metadata_list = []
            for table in tables:
                # Get column info
                cursor.execute(f"PRAGMA table_info({table})")
                columns_raw = cursor.fetchall()
                
                columns = []
                for col in columns_raw:
                    columns.append({
                        'name': col[1],
                        'type': col[2],
                        'description': '',
                        'is_primary_key': bool(col[5])
                    })
                
                # Get foreign key info
                cursor.execute(f"PRAGMA foreign_key_list({table})")
                fk_raw = cursor.fetchall()
                
                foreign_keys = []
                for fk in fk_raw:
                    # fk format: (id, seq, table, from, to, on_update, on_delete, match)
                    foreign_keys.append({
                        'column': fk[3],          # from column
                        'references_table': fk[2],  # referenced table
                        'references_column': fk[4]  # referenced column
                    })
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                # Default descriptions for telco tables
                descriptions = {
                    'customers': 'Customer account information including demographics, status, and value metrics',
                    'plans': 'Service plans with pricing and limits',
                    'devices': 'Customer devices with manufacturer and model info',
                    'network_activity': 'Network usage including calls, SMS, data, roaming',
                    'transactions': 'Financial transactions including charges, payments, and overages'
                }
                
                metadata_list.append({
                    'table_name': table,
                    'description': descriptions.get(table, f'{table.title()} table'),
                    'columns': columns,
                    'foreign_keys': foreign_keys,
                    'row_count': row_count
                })
            
            conn.close()
            logger.debug(f"Retrieved metadata for {len(metadata_list)} SQLite tables")
            return metadata_list
            
        except Exception as e:
            logger.error(f"Failed to get SQLite metadata: {e}")
            return []
    
    def _get_hive_metadata(self, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get metadata from Hive metastore."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if table_name:
                tables_to_fetch = [table_name]
            else:
                # Get all tables in database
                cursor.execute("SHOW TABLES")
                tables_to_fetch = [row[0] for row in cursor.fetchall()]
            
            metadata_list = []
            for table in tables_to_fetch:
                # Describe table
                cursor.execute(f"DESCRIBE FORMATTED {table}")
                desc_rows = cursor.fetchall()
                
                columns = []
                table_description = ""
                in_columns_section = True
                
                for row in desc_rows:
                    col_name = row[0].strip() if row[0] else ""
                    
                    if col_name.startswith('#'):
                        in_columns_section = False
                        continue
                    
                    if in_columns_section and col_name:
                        columns.append({
                            'name': col_name,
                            'type': row[1].strip() if row[1] else '',
                            'description': row[2].strip() if len(row) > 2 and row[2] else ''
                        })
                    
                    if col_name.lower() == 'comment':
                        table_description = row[1].strip() if row[1] else ""
                
                metadata_list.append({
                    'table_name': table,
                    'description': table_description,
                    'columns': columns
                })
            
            logger.debug(f"Retrieved metadata for {len(metadata_list)} Hive tables")
            return metadata_list
            
        except Exception as e:
            logger.error(f"Failed to get Hive metadata: {e}")
            return []
    
    def _get_impala_metadata(self, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get metadata from Impala."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if table_name:
                tables_to_fetch = [table_name]
            else:
                cursor.execute("SHOW TABLES")
                tables_to_fetch = [row[0] for row in cursor.fetchall()]
            
            metadata_list = []
            for table in tables_to_fetch:
                cursor.execute(f"DESCRIBE {table}")
                columns_raw = cursor.fetchall()
                
                columns = []
                for row in columns_raw:
                    if row[0] and not row[0].startswith('#'):
                        columns.append({
                            'name': row[0].strip(),
                            'type': row[1].strip() if row[1] else '',
                            'description': row[2].strip() if len(row) > 2 and row[2] else ''
                        })
                
                metadata_list.append({
                    'table_name': table,
                    'description': '',
                    'columns': columns
                })
            
            logger.debug(f"Retrieved metadata for {len(metadata_list)} Impala tables")
            return metadata_list
            
        except Exception as e:
            logger.error(f"Failed to get Impala metadata: {e}")
            return []
    
    def _get_databricks_metadata(self, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get metadata from Databricks."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if table_name:
                tables_to_fetch = [table_name]
            else:
                cursor.execute("SHOW TABLES")
                tables_to_fetch = [row[1] for row in cursor.fetchall()]
            
            metadata_list = []
            for table in tables_to_fetch:
                cursor.execute(f"DESCRIBE TABLE {table}")
                columns_raw = cursor.fetchall()
                
                columns = []
                for row in columns_raw:
                    if row[0] and not row[0].startswith('#'):
                        columns.append({
                            'name': row[0].strip(),
                            'type': row[1].strip() if row[1] else '',
                            'description': row[2].strip() if len(row) > 2 and row[2] else ''
                        })
                
                metadata_list.append({
                    'table_name': table,
                    'description': '',
                    'columns': columns
                })
            
            logger.debug(f"Retrieved metadata for {len(metadata_list)} Databricks tables")
            return metadata_list
            
        except Exception as e:
            logger.error(f"Failed to get Databricks metadata: {e}")
            return []
    
    def _get_snowflake_metadata(self, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get metadata from Snowflake."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if table_name:
                tables_to_fetch = [table_name]
            else:
                cursor.execute("SHOW TABLES")
                tables_to_fetch = [row[1] for row in cursor.fetchall()]
            
            metadata_list = []
            for table in tables_to_fetch:
                cursor.execute(f"DESCRIBE TABLE {table}")
                columns_raw = cursor.fetchall()
                
                columns = []
                for row in columns_raw:
                    columns.append({
                        'name': row[0],
                        'type': row[1],
                        'description': row[8] if len(row) > 8 and row[8] else ''
                    })
                
                # Get table comment
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                table_info = cursor.fetchone()
                table_description = table_info[5] if len(table_info) > 5 else ""
                
                metadata_list.append({
                    'table_name': table,
                    'description': table_description,
                    'columns': columns
                })
            
            logger.debug(f"Retrieved metadata for {len(metadata_list)} Snowflake tables")
            return metadata_list
            
        except Exception as e:
            logger.error(f"Failed to get Snowflake metadata: {e}")
            return []
    
    def _get_postgres_metadata(self, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get metadata from PostgreSQL."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get tables from information_schema
            if table_name:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = %s
                """, (table_name,))
            else:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """)
            
            tables_to_fetch = [row[0] for row in cursor.fetchall()]
            
            metadata_list = []
            for table in tables_to_fetch:
                # Get column info
                cursor.execute("""
                    SELECT column_name, data_type, column_default, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table,))
                
                columns_raw = cursor.fetchall()
                columns = []
                for row in columns_raw:
                    columns.append({
                        'name': row[0],
                        'type': row[1],
                        'description': '',
                        'nullable': row[3] == 'YES'
                    })
                
                metadata_list.append({
                    'table_name': table,
                    'description': '',
                    'columns': columns
                })
            
            logger.debug(f"Retrieved metadata for {len(metadata_list)} PostgreSQL tables")
            return metadata_list
            
        except Exception as e:
            logger.error(f"Failed to get PostgreSQL metadata: {e}")
            return []
    
    def _get_mysql_metadata(self, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get metadata from MySQL."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if table_name:
                cursor.execute("SHOW TABLES LIKE %s", (table_name,))
            else:
                cursor.execute("SHOW TABLES")
            
            tables_to_fetch = [row[0] for row in cursor.fetchall()]
            
            metadata_list = []
            for table in tables_to_fetch:
                cursor.execute(f"DESCRIBE {table}")
                columns_raw = cursor.fetchall()
                
                columns = []
                for row in columns_raw:
                    columns.append({
                        'name': row[0],
                        'type': row[1],
                        'description': '',
                        'nullable': row[2] == 'YES'
                    })
                
                metadata_list.append({
                    'table_name': table,
                    'description': '',
                    'columns': columns
                })
            
            logger.debug(f"Retrieved metadata for {len(metadata_list)} MySQL tables")
            return metadata_list
            
        except Exception as e:
            logger.error(f"Failed to get MySQL metadata: {e}")
            return []
    
    def _get_iceberg_metadata(self, namespace: str = "default") -> List[Dict[str, Any]]:
        """Get metadata from Iceberg REST catalog."""
        if not REQUESTS_AVAILABLE:
            logger.error("requests library not available for Iceberg REST API")
            return []
        
        try:
            iceberg_config = self.config.hive  # Use same config section
            base_url = iceberg_config.get('rest_url', 'http://localhost:8181')
            
            # List tables
            response = requests.get(f"{base_url}/v1/namespaces/{namespace}/tables")
            response.raise_for_status()
            
            tables_data = response.json()
            metadata_list = []
            
            for table_info in tables_data.get('identifiers', []):
                table_name = table_info['name']
                
                # Get table metadata
                table_response = requests.get(
                    f"{base_url}/v1/namespaces/{namespace}/tables/{table_name}"
                )
                table_response.raise_for_status()
                table_data = table_response.json()
                
                # Extract schema
                schema = table_data.get('metadata', {}).get('current-schema', {})
                columns = []
                
                for field in schema.get('fields', []):
                    columns.append({
                        'name': field.get('name', ''),
                        'type': field.get('type', ''),
                        'description': field.get('doc', ''),
                        'required': field.get('required', False)
                    })
                
                metadata_list.append({
                    'table_name': table_name,
                    'description': table_data.get('metadata', {}).get('properties', {}).get('comment', ''),
                    'columns': columns
                })
            
            logger.debug(f"Retrieved metadata for {len(metadata_list)} Iceberg tables")
            return metadata_list
            
        except Exception as e:
            logger.error(f"Failed to get Iceberg metadata: {e}")
            return []
    
    def _fetch_metadata(self, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch metadata based on database type."""
        if self.db_type == 'sqlite':
            return self._get_sqlite_metadata()
        elif self.db_type == 'hive':
            return self._get_hive_metadata(table_name)
        elif self.db_type == 'impala':
            return self._get_impala_metadata(table_name)
        elif self.db_type == 'databricks':
            return self._get_databricks_metadata(table_name)
        elif self.db_type == 'snowflake':
            return self._get_snowflake_metadata(table_name)
        elif self.db_type == 'postgres':
            return self._get_postgres_metadata(table_name)
        elif self.db_type == 'mysql':
            return self._get_mysql_metadata(table_name)
        elif self.db_type == 'iceberg':
            return self._get_iceberg_metadata()
        else:
            logger.error(f"Unsupported database type: {self.db_type}")
            return []
    
    def get_relevant_tables(self, question: str) -> List[Dict[str, Any]]:
        """Get relevant tables for a question."""
        logger.debug(f"[MetadataManager] Getting relevant tables for: {question[:100]}...")
        logger.debug(f"[MetadataManager] Database type: {self.db_type}")
        
        # For SQLite and small databases, return all tables
        if self.db_type in ['sqlite', 'iceberg']:
            logger.debug(f"[MetadataManager] Fetching all tables for {self.db_type}")
            result = self._fetch_metadata()
            logger.info(f"[MetadataManager] Retrieved {len(result)} tables")
            return result
        
        # For larger databases, use vector store to find relevant tables
        try:
            # Try to find relevant tables from vector store
            logger.debug("[MetadataManager] Searching vector store for relevant tables")
            similar = self.vector_store.search(question, top_k=10)
            logger.debug(f"[MetadataManager] Vector store returned {len(similar)} results")
            
            # Extract unique table names
            table_names = set()
            for result in similar:
                metadata = result.get('metadata', {})
                if 'table_name' in metadata:
                    table_names.add(metadata['table_name'])
            
            logger.debug(f"[MetadataManager] Found table names in vector store: {table_names}")
            
            if table_names:
                # Fetch metadata for relevant tables only
                all_metadata = []
                for table_name in table_names:
                    table_meta = self._fetch_metadata(table_name)
                    all_metadata.extend(table_meta)
                logger.info(f"[MetadataManager] Retrieved {len(all_metadata)} relevant tables")
                return all_metadata
            else:
                # Fallback to all tables if no matches
                logger.warning("[MetadataManager] No relevant tables found in vector store, returning all")
                result = self._fetch_metadata()
                logger.info(f"[MetadataManager] Retrieved {len(result)} tables as fallback")
                return result
                
        except Exception as e:
            logger.error(f"[MetadataManager] Failed to get relevant tables from vector store: {e}")
            logger.exception("[MetadataManager] Full exception:")
            # Fallback to fetching all metadata
            result = self._fetch_metadata()
            logger.info(f"[MetadataManager] Retrieved {len(result)} tables after error")
            return result
    
    def get_table_metadata(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific table."""
        # Get from cache if available
        cache_key = table_name.lower()
        if cache_key in self._metadata_cache:
            cache_age = time.time() - self._metadata_cache[cache_key].get('cached_at', 0)
            if cache_age < self.config.cache_ttl:
                logger.debug(f"Using cached metadata for {table_name}")
                return self._metadata_cache[cache_key]
        
        # Fetch fresh metadata
        metadata_list = self._fetch_metadata(table_name)
        
        for metadata in metadata_list:
            if metadata['table_name'].lower() == table_name.lower():
                # Cache it
                metadata['cached_at'] = time.time()
                self._metadata_cache[cache_key] = metadata
                return metadata
        
        return None
    
