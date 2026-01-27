"""
Integration test simulating OneFS block replication with file copy.
Tests the full sync workflow without requiring actual Isilon hardware.
"""
import unittest
from pathlib import Path
import tempfile
import shutil
import time

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType

from src.file_scanner import FileScanner
from src.metadata_tracker import MetadataTracker
from src.state_manager import StateManager
from src.sync_manager import IcebergSyncManager
from src.utils import calculate_delta


class TestEndToEndReplication(unittest.TestCase):
    """
    End-to-end integration test simulating storage replication.
    Uses regular file copy to simulate OneFS block replication.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up Spark session once for all tests."""
        cls.spark = SparkSession.builder \
            .appName("Iceberg-Sync-Integration-Test") \
            .master("local[2]") \
            .config("spark.sql.extensions",
                    "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
            .config("spark.sql.catalog.test_catalog",
                    "org.apache.iceberg.spark.SparkCatalog") \
            .config("spark.sql.catalog.test_catalog.type", "hadoop") \
            .config("spark.ui.enabled", "false") \
            .getOrCreate()
        
        cls.spark.sparkContext.setLogLevel("WARN")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up Spark session."""
        cls.spark.stop()
    
    def setUp(self):
        """Set up test environment for each test."""
        # Create temporary directories
        self.test_root = tempfile.mkdtemp()
        self.test_path = Path(self.test_root)
        
        # Simulate source and DR locations
        self.source_warehouse = self.test_path / "source" / "warehouse"
        self.dr_warehouse = self.test_path / "dr" / "warehouse"
        
        self.source_warehouse.mkdir(parents=True)
        self.dr_warehouse.mkdir(parents=True)
        
        # Create table structure
        self.db = "testdb"
        self.table = "users"
        
        self.source_table_path = self.source_warehouse / f"{self.db}.db" / self.table
        self.dr_table_path = self.dr_warehouse / f"{self.db}.db" / self.table
        
        # State directory
        self.state_dir = str(self.test_path / "state")
        
        print(f"\n{'='*60}")
        print(f"Test Setup:")
        print(f"  Source:  {self.source_table_path}")
        print(f"  DR:      {self.dr_table_path}")
        print(f"{'='*60}\n")
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_root)
    
    def _create_sample_parquet_data(self, output_path: Path, num_files: int = 3, rows_per_file: int = 100):
        """
        Create sample parquet files simulating data.
        
        Args:
            output_path: Where to write parquet files
            num_files: Number of parquet files to create
            rows_per_file: Rows per file
        
        Returns:
            List of created file paths
        """
        output_path.mkdir(parents=True, exist_ok=True)
        
        created_files = []
        
        for i in range(num_files):
            # Create sample data
            data = []
            for j in range(rows_per_file):
                row_id = i * rows_per_file + j
                data.append({
                    'id': row_id,
                    'name': f'user_{row_id}',
                    'email': f'user{row_id}@example.com',
                    'age': 20 + (row_id % 50),
                    'created_at': f'2024-01-{(row_id % 28) + 1:02d}'
                })
            
            df = self.spark.createDataFrame(data)
            
            # Write as parquet
            file_path = output_path / f"data_{i:04d}.parquet"
            df.coalesce(1).write.mode("overwrite").parquet(str(file_path))
            
            # Find the actual parquet file (Spark creates a directory)
            parquet_files = list(file_path.glob("*.parquet"))
            if parquet_files:
                actual_file = parquet_files[0]
                # Move it to our desired name
                final_file = output_path / f"data_{i:04d}.parquet"
                shutil.rmtree(file_path)
                actual_file.parent.rename(final_file.parent / f"_temp_{i}")
                (final_file.parent / f"_temp_{i}" / actual_file.name).rename(final_file)
                shutil.rmtree(final_file.parent / f"_temp_{i}")
                created_files.append(final_file)
        
        print(f"Created {len(created_files)} parquet files in {output_path}")
        return created_files
    
    def _simulate_block_replication(self, source_path: Path, dest_path: Path):
        """
        Simulate OneFS block-level replication using file copy.
        Copies entire directory structure.
        
        Args:
            source_path: Source directory
            dest_path: Destination directory
        """
        print(f"\n📦 Simulating block replication:")
        print(f"   {source_path} -> {dest_path}")
        
        if dest_path.exists():
            shutil.rmtree(dest_path)
        
        shutil.copytree(source_path, dest_path)
        
        # Verify replication
        source_files = list(source_path.rglob("*.parquet"))
        dest_files = list(dest_path.rglob("*.parquet"))
        
        print(f"   ✅ Replicated {len(dest_files)} files")
        
        assert len(source_files) == len(dest_files), "Replication file count mismatch"
    
    def test_01_initial_sync(self):
        """Test initial sync with all new files."""
        print("\n" + "="*60)
        print("TEST 1: Initial Sync (All New Files)")
        print("="*60)
        
        # Step 1: Create data at source
        source_data_path = self.source_table_path / "data"
        files = self._create_sample_parquet_data(source_data_path, num_files=3)
        
        # Step 2: Simulate block replication to DR
        self._simulate_block_replication(self.source_table_path, self.dr_table_path)
        
        # Step 3: Configure DR warehouse for Iceberg
        self.spark.conf.set("spark.sql.catalog.test_catalog.warehouse",
                           str(self.dr_warehouse))
        
        # Step 4: Run sync manager
        manager = IcebergSyncManager(
            replicated_base_path=str(self.dr_warehouse),
            catalog_name="test_catalog",
            db=self.db,
            table_name=self.table,
            warehouse_path=str(self.dr_warehouse),
            state_dir=self.state_dir,
            spark_session=self.spark
        )
        
        # Run sync
        success = manager.sync()
        
        # Verify
        self.assertTrue(success, "Initial sync should succeed")
        
        # Check Iceberg table was created
        table_identifier = f"test_catalog.{self.db}.{self.table}"
        df = self.spark.table(table_identifier)
        row_count = df.count()
        
        print(f"\n✅ Initial sync complete: {row_count} rows in Iceberg table")
        self.assertEqual(row_count, 300, "Should have 300 rows (3 files * 100 rows)")
        
        # Check state was saved
        state = manager.state.load_state(self.db, self.table)
        self.assertEqual(state['total_files_processed'], 3)
    
    def test_02_incremental_sync(self):
        """Test incremental sync with new files added."""
        print("\n" + "="*60)
        print("TEST 2: Incremental Sync (New Files)")
        print("="*60)
        
        # Step 1: Initial setup with 3 files
        source_data_path = self.source_table_path / "data"
        self._create_sample_parquet_data(source_data_path, num_files=3)
        self._simulate_block_replication(self.source_table_path, self.dr_table_path)
        
        self.spark.conf.set("spark.sql.catalog.test_catalog.warehouse",
                           str(self.dr_warehouse))
        
        manager = IcebergSyncManager(
            replicated_base_path=str(self.dr_warehouse),
            catalog_name="test_catalog",
            db=self.db,
            table_name=self.table,
            warehouse_path=str(self.dr_warehouse),
            state_dir=self.state_dir,
            spark_session=self.spark
        )
        
        # Initial sync
        print("\n[Phase 1] Initial sync with 3 files...")
        success1 = manager.sync()
        self.assertTrue(success1)
        
        initial_count = self.spark.table(f"test_catalog.{self.db}.{self.table}").count()
        print(f"Initial count: {initial_count}")
        
        # Step 2: Add more files at source
        print("\n[Phase 2] Adding 2 new files at source...")
        time.sleep(0.1)  # Small delay to ensure different timestamps
        
        # Create new files (starting from index 3)
        for i in range(3, 5):
            data = []
            for j in range(100):
                row_id = i * 100 + j
                data.append({
                    'id': row_id,
                    'name': f'user_{row_id}',
                    'email': f'user{row_id}@example.com',
                    'age': 20 + (row_id % 50),
                    'created_at': f'2024-01-{(row_id % 28) + 1:02d}'
                })
            
            df = self.spark.createDataFrame(data)
            file_path = source_data_path / f"data_{i:04d}.parquet"
            df.coalesce(1).write.mode("overwrite").parquet(str(file_path))
        
        # Step 3: Replicate new files to DR (simulating incremental replication)
        print("\n[Phase 3] Replicating to DR...")
        self._simulate_block_replication(self.source_table_path, self.dr_table_path)
        
        # Step 4: Run incremental sync
        print("\n[Phase 4] Running incremental sync...")
        success2 = manager.sync()
        self.assertTrue(success2)
        
        # Verify only new files were processed
        final_count = self.spark.table(f"test_catalog.{self.db}.{self.table}").count()
        print(f"Final count: {final_count}")
        
        # Should have added 200 more rows (2 files * 100 rows)
        self.assertGreater(final_count, initial_count, "Count should increase")
        
        # Check state
        state = manager.state.load_state(self.db, self.table)
        print(f"\nState after incremental sync:")
        print(f"  Total runs: {len(state['runs'])}")
        print(f"  Total files processed: {state['total_files_processed']}")
        
        self.assertEqual(len(state['runs']), 2, "Should have 2 runs")
        self.assertGreaterEqual(state['total_files_processed'], 3, "Should have processed at least initial 3 files")
    
    def test_03_no_changes_sync(self):
        """Test sync when no new files exist (idempotent)."""
        print("\n" + "="*60)
        print("TEST 3: No Changes Sync (Idempotent)")
        print("="*60)
        
        # Setup
        source_data_path = self.source_table_path / "data"
        self._create_sample_parquet_data(source_data_path, num_files=2)
        self._simulate_block_replication(self.source_table_path, self.dr_table_path)
        
        self.spark.conf.set("spark.sql.catalog.test_catalog.warehouse",
                           str(self.dr_warehouse))
        
        manager = IcebergSyncManager(
            replicated_base_path=str(self.dr_warehouse),
            catalog_name="test_catalog",
            db=self.db,
            table_name=self.table,
            warehouse_path=str(self.dr_warehouse),
            state_dir=self.state_dir,
            spark_session=self.spark
        )
        
        # First sync
        print("\n[Phase 1] Initial sync...")
        success1 = manager.sync()
        self.assertTrue(success1)
        
        count1 = self.spark.table(f"test_catalog.{self.db}.{self.table}").count()
        
        # Second sync without changes
        print("\n[Phase 2] Sync again without changes...")
        success2 = manager.sync()
        self.assertTrue(success2)
        
        count2 = self.spark.table(f"test_catalog.{self.db}.{self.table}").count()
        
        # Counts should be identical
        self.assertEqual(count1, count2, "Count should not change")
        
        # Check state shows no new files in second run
        state = manager.state.load_state(self.db, self.table)
        self.assertEqual(len(state['runs']), 2)
        self.assertEqual(state['runs'][1]['files_processed'], 0, "Second run should process 0 files")
    
    def test_04_component_integration(self):
        """Test individual components working together."""
        print("\n" + "="*60)
        print("TEST 4: Component Integration")
        print("="*60)
        
        # Create test data
        source_data_path = self.source_table_path / "data"
        self._create_sample_parquet_data(source_data_path, num_files=3)
        self._simulate_block_replication(self.source_table_path, self.dr_table_path)
        
        # Test FileScanner
        print("\n[Test] FileScanner...")
        scanner = FileScanner(self.spark)
        dr_data_path = self.dr_table_path / "data"
        found_files = scanner.scan_data_files(str(dr_data_path))
        self.assertGreater(len(found_files), 0, "Should find files")
        print(f"  ✅ Found {len(found_files)} files")
        
        # Test MetadataTracker
        print("\n[Test] MetadataTracker...")
        self.spark.conf.set("spark.sql.catalog.test_catalog.warehouse",
                           str(self.dr_warehouse))
        
        tracker = MetadataTracker(self.spark, "test_catalog", str(self.dr_warehouse))
        
        # Create test table
        data = [{'id': 1, 'name': 'test'}]
        df = self.spark.createDataFrame(data)
        tracker.create_table(self.db, self.table, df)
        
        self.assertTrue(tracker.table_exists(self.db, self.table))
        print(f"  ✅ Created and verified Iceberg table")
        
        # Test StateManager
        print("\n[Test] StateManager...")
        state_mgr = StateManager(self.state_dir)
        state_mgr.save_state(self.db, self.table, 5, 500, ["file1"], True)
        state = state_mgr.load_state(self.db, self.table)
        self.assertEqual(state['total_files_processed'], 5)
        print(f"  ✅ State saved and loaded correctly")
        
        # Test calculate_delta
        print("\n[Test] Delta Calculation...")
        current = {"file1", "file2", "file3"}
        tracked = {"file1"}
        delta = calculate_delta(current, tracked)
        self.assertEqual(delta['new_count'], 2)
        print(f"  ✅ Delta calculated: {delta['new_count']} new files")


if __name__ == '__main__':
    unittest.main(verbosity=2)

