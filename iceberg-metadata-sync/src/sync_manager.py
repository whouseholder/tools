"""
Main sync manager orchestrating the incremental metadata sync.
"""
import argparse
import logging
import sys
import time
from typing import Optional

from pyspark.sql import SparkSession

from .file_scanner import FileScanner
from .metadata_tracker import MetadataTracker
from .state_manager import StateManager
from .utils import calculate_delta, setup_logging, print_summary

logger = logging.getLogger(__name__)


class IcebergSyncManager:
    """
    Main orchestrator for Iceberg metadata synchronization.
    """
    
    def __init__(
        self,
        replicated_base_path: str,
        catalog_name: str,
        db: str,
        table_name: str,
        warehouse_path: str,
        state_dir: str = "/tmp/iceberg_sync_state",
        spark_session: Optional[SparkSession] = None
    ):
        """
        Initialize sync manager.
        
        Args:
            replicated_base_path: Base path where tables are replicated
            catalog_name: Iceberg catalog name
            db: Database name
            table_name: Table name
            warehouse_path: Iceberg warehouse path
            state_dir: Directory for state files
            spark_session: Optional existing SparkSession
        """
        self.replicated_base_path = replicated_base_path
        self.catalog_name = catalog_name
        self.db = db
        self.table_name = table_name
        self.warehouse_path = warehouse_path
        
        self.table_path = f"{replicated_base_path}/{db}.db/{table_name}"
        self.data_path = f"{self.table_path}/data"
        
        # Initialize Spark if not provided
        self.spark = spark_session or self._create_spark_session()
        
        # Initialize components
        self.scanner = FileScanner(self.spark)
        self.metadata = MetadataTracker(self.spark, catalog_name, warehouse_path)
        self.state = StateManager(state_dir)
    
    def _create_spark_session(self) -> SparkSession:
        """Create and configure SparkSession for Iceberg."""
        logger.info("Creating SparkSession...")
        
        return SparkSession.builder \
            .appName(f"Iceberg-Sync-{self.db}.{self.table_name}") \
            .config("spark.jars.packages",
                    "org.apache.iceberg:iceberg-spark-runtime-3.3_2.12:1.2.0") \
            .config("spark.sql.extensions",
                    "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
            .config(f"spark.sql.catalog.{self.catalog_name}",
                    "org.apache.iceberg.spark.SparkCatalog") \
            .config(f"spark.sql.catalog.{self.catalog_name}.type", "hadoop") \
            .config(f"spark.sql.catalog.{self.catalog_name}.warehouse",
                    self.warehouse_path) \
            .config("spark.sql.adaptive.enabled", "true") \
            .getOrCreate()
    
    def sync(self) -> bool:
        """
        Perform incremental sync operation.
        
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        
        logger.info("="*80)
        logger.info("Starting Iceberg Metadata Sync")
        logger.info("="*80)
        logger.info(f"Table: {self.catalog_name}.{self.db}.{self.table_name}")
        logger.info(f"Data path: {self.data_path}")
        logger.info("="*80)
        
        try:
            # Step 1: Scan filesystem for data files
            logger.info("\n[1/5] Scanning filesystem for data files...")
            current_files = self.scanner.scan_data_files(self.data_path)
            
            if not current_files:
                logger.warning("No data files found in filesystem!")
                return False
            
            # Step 2: Get files tracked by Iceberg
            logger.info("\n[2/5] Querying Iceberg metadata...")
            tracked_files = self.metadata.get_tracked_files(self.db, self.table_name)
            
            # Step 3: Calculate delta
            logger.info("\n[3/5] Calculating delta...")
            delta = calculate_delta(current_files, tracked_files)
            
            print_summary(delta)
            
            if delta['new_count'] == 0:
                logger.info("✅ No new files to process - metadata is up to date")
                self.state.save_state(
                    self.db, self.table_name,
                    new_files_count=0,
                    new_rows_count=0,
                    new_files=[],
                    success=True
                )
                return True
            
            # Step 4: Process new files
            logger.info(f"\n[4/5] Processing {delta['new_count']} new files...")
            success, rows_processed = self._process_new_files(delta['new_files'])
            
            if not success:
                logger.error("❌ Failed to process new files")
                return False
            
            # Step 5: Save state
            logger.info("\n[5/5] Saving state...")
            self.state.save_state(
                self.db,
                self.table_name,
                new_files_count=delta['new_count'],
                new_rows_count=rows_processed,
                new_files=sorted(list(delta['new_files'])),
                success=True
            )
            
            # Final summary
            elapsed = time.time() - start_time
            logger.info("="*80)
            logger.info("✅ Sync Completed Successfully!")
            logger.info("="*80)
            logger.info(f"Files processed: {delta['new_count']:,}")
            logger.info(f"Rows processed:  {rows_processed:,}")
            logger.info(f"Runtime:         {elapsed:.2f} seconds")
            logger.info("="*80)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Sync failed: {e}", exc_info=True)
            self.state.save_state(
                self.db, self.table_name,
                new_files_count=0,
                new_rows_count=0,
                new_files=[],
                success=False
            )
            return False
    
    def _process_new_files(self, new_files) -> tuple:
        """
        Process new files and update Iceberg metadata.
        
        Args:
            new_files: Set of new file paths
        
        Returns:
            Tuple of (success: bool, rows_processed: int)
        """
        if not new_files:
            return True, 0
        
        # Convert set to sorted list
        new_files_list = sorted(list(new_files))
        
        # Show sample
        logger.info(f"Sample files to process:")
        for f in new_files_list[:3]:
            logger.info(f"  - {f}")
        if len(new_files_list) > 3:
            logger.info(f"  ... and {len(new_files_list) - 3} more")
        
        try:
            # Read only new files
            df = self.spark.read.parquet(*new_files_list)
            row_count = df.count()
            
            logger.info(f"✅ Read {row_count:,} rows from {len(new_files_list)} files")
            
            # Check if table exists
            table_exists = self.metadata.table_exists(self.db, self.table_name)
            
            if not table_exists:
                logger.info("Creating new Iceberg table...")
                self.metadata.create_table(self.db, self.table_name, df)
            else:
                logger.info("Appending to existing Iceberg table...")
                self.metadata.append_to_table(self.db, self.table_name, df)
            
            # Verify
            stats = self.metadata.get_table_stats(self.db, self.table_name)
            if stats:
                logger.info(f"✅ Table now contains {stats['row_count']:,} total rows")
            
            return True, row_count
            
        except Exception as e:
            logger.error(f"Error processing files: {e}", exc_info=True)
            return False, 0
    
    def get_stats(self):
        """Print statistics about table and sync history."""
        print("\n" + "="*80)
        print(f"Statistics: {self.catalog_name}.{self.db}.{self.table_name}")
        print("="*80)
        
        # Iceberg table stats
        iceberg_stats = self.metadata.get_table_stats(self.db, self.table_name)
        if iceberg_stats:
            print("\nIceberg Table:")
            print(f"  Rows:      {iceberg_stats['row_count']:,}")
            print(f"  Files:     {iceberg_stats['file_count']:,}")
            print(f"  Size:      {iceberg_stats['total_size_gb']:.2f} GB")
            print(f"  Snapshots: {iceberg_stats['snapshot_count']:,}")
        else:
            print("\nIceberg Table: Not found")
        
        # State stats
        state_stats = self.state.get_stats(self.db, self.table_name)
        print("\nSync History:")
        print(f"  Total files processed: {state_stats['total_files_processed']:,}")
        print(f"  Total rows processed:  {state_stats['total_rows_processed']:,}")
        print(f"  Total runs:            {state_stats['total_runs']}")
        print(f"  Successful runs:       {state_stats['successful_runs']}")
        print(f"  Failed runs:           {state_stats['failed_runs']}")
        print(f"  Last run:              {state_stats['last_run_time'] or 'Never'}")
        
        print("="*80 + "\n")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Incremental Iceberg metadata sync for replicated tables'
    )
    parser.add_argument('--replicated-path', required=True,
                       help='Base path of replicated tables')
    parser.add_argument('--catalog', required=True,
                       help='Iceberg catalog name')
    parser.add_argument('--database', required=True,
                       help='Database name')
    parser.add_argument('--table', required=True,
                       help='Table name')
    parser.add_argument('--warehouse', required=True,
                       help='Iceberg warehouse path')
    parser.add_argument('--state-dir', default='/tmp/iceberg_sync_state',
                       help='Directory for state files')
    parser.add_argument('--stats', action='store_true',
                       help='Show statistics only (no sync)')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Create manager
    manager = IcebergSyncManager(
        replicated_base_path=args.replicated_path,
        catalog_name=args.catalog,
        db=args.database,
        table_name=args.table,
        warehouse_path=args.warehouse,
        state_dir=args.state_dir
    )
    
    if args.stats:
        manager.get_stats()
        sys.exit(0)
    else:
        success = manager.sync()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

