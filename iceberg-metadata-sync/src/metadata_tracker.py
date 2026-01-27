"""
Metadata tracker for Iceberg table operations.
"""
import logging
from typing import Set, Optional

logger = logging.getLogger(__name__)


class MetadataTracker:
    """
    Tracks and manages Iceberg table metadata.
    Queries Iceberg's metadata tables to find what files are already tracked.
    """
    
    def __init__(self, spark_session, catalog_name: str, warehouse_path: str):
        """
        Initialize metadata tracker.
        
        Args:
            spark_session: SparkSession with Iceberg configured
            catalog_name: Name of Iceberg catalog
            warehouse_path: Path to Iceberg warehouse
        """
        self.spark = spark_session
        self.catalog_name = catalog_name
        self.warehouse_path = warehouse_path
    
    def get_tracked_files(self, db: str, table: str) -> Set[str]:
        """
        Get list of data files currently tracked by Iceberg.
        
        Args:
            db: Database name
            table: Table name
        
        Returns:
            Set of absolute file paths tracked by Iceberg
        """
        table_identifier = f"{self.catalog_name}.{db}.{table}"
        
        try:
            # Verify table exists
            self.spark.sql(f"DESCRIBE TABLE {table_identifier}")
            
            logger.info(f"Reading Iceberg metadata: {table_identifier}")
            
            # Query metadata table for tracked files
            files_df = self.spark.sql(f"""
                SELECT file_path
                FROM {table_identifier}.files
            """)
            
            tracked_files = set(row.file_path for row in files_df.collect())
            
            logger.info(f"Iceberg tracks {len(tracked_files)} files")
            return tracked_files
            
        except Exception as e:
            logger.warning(f"Table doesn't exist or can't read metadata: {e}")
            logger.info("Will create new table")
            return set()
    
    def table_exists(self, db: str, table: str) -> bool:
        """
        Check if Iceberg table exists.
        
        Args:
            db: Database name
            table: Table name
        
        Returns:
            True if table exists, False otherwise
        """
        table_identifier = f"{self.catalog_name}.{db}.{table}"
        
        try:
            self.spark.sql(f"DESCRIBE TABLE {table_identifier}")
            return True
        except:
            return False
    
    def get_table_stats(self, db: str, table: str) -> Optional[dict]:
        """
        Get statistics about Iceberg table.
        
        Args:
            db: Database name
            table: Table name
        
        Returns:
            Dictionary with stats or None if table doesn't exist
        """
        if not self.table_exists(db, table):
            return None
        
        table_identifier = f"{self.catalog_name}.{db}.{table}"
        
        # Get row count
        row_count = self.spark.table(table_identifier).count()
        
        # Get file stats
        files_df = self.spark.sql(f"""
            SELECT 
                COUNT(*) as file_count,
                SUM(file_size_in_bytes) as total_size_bytes
            FROM {table_identifier}.files
        """)
        
        stats_row = files_df.collect()[0]
        
        # Get snapshot count
        snapshots_df = self.spark.sql(f"""
            SELECT COUNT(*) as snapshot_count
            FROM {table_identifier}.snapshots
        """)
        
        snapshot_count = snapshots_df.collect()[0].snapshot_count
        
        return {
            'row_count': row_count,
            'file_count': stats_row.file_count,
            'total_size_bytes': stats_row.total_size_bytes,
            'total_size_gb': stats_row.total_size_bytes / (1024**3) if stats_row.total_size_bytes else 0,
            'snapshot_count': snapshot_count
        }
    
    def create_table(self, db: str, table: str, dataframe, table_properties: dict = None):
        """
        Create new Iceberg table.
        
        Args:
            db: Database name
            table: Table name
            dataframe: Spark DataFrame with data
            table_properties: Optional table properties
        """
        table_identifier = f"{self.catalog_name}.{db}.{table}"
        
        logger.info(f"Creating Iceberg table: {table_identifier}")
        
        writer = dataframe.writeTo(table_identifier).using("iceberg")
        
        # Apply default properties
        default_props = {
            "format-version": "2",
            "write.format.default": "parquet",
            "write.parquet.compression-codec": "snappy"
        }
        
        if table_properties:
            default_props.update(table_properties)
        
        for key, value in default_props.items():
            writer = writer.tableProperty(key, str(value))
        
        writer.create()
        
        logger.info(f"Created table: {table_identifier}")
    
    def append_to_table(self, db: str, table: str, dataframe):
        """
        Append data to existing Iceberg table.
        
        Args:
            db: Database name
            table: Table name
            dataframe: Spark DataFrame with new data
        """
        table_identifier = f"{self.catalog_name}.{db}.{table}"
        
        logger.info(f"Appending to table: {table_identifier}")
        
        dataframe.writeTo(table_identifier).using("iceberg").append()
        
        logger.info(f"Appended data to: {table_identifier}")

