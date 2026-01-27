"""
Simple integration test using mock Spark for local testing.
Tests the workflow without requiring full Iceberg dependencies.
"""
import unittest
from pathlib import Path
import tempfile
import shutil

from src.file_scanner import FileScanner
from src.state_manager import StateManager
from src.utils import calculate_delta


class TestSimpleIntegration(unittest.TestCase):
    """
    Simple integration test without PySpark dependencies.
    Tests the core workflow of file discovery and state management.
    """
    
    def setUp(self):
        """Set up test environment."""
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
    
    def _create_dummy_parquet_files(self, output_path: Path, num_files: int = 3):
        """
        Create dummy parquet files (just empty files with .parquet extension).
        
        Args:
            output_path: Where to write files
            num_files: Number of files to create
        
        Returns:
            List of created file paths
        """
        output_path.mkdir(parents=True, exist_ok=True)
        
        created_files = []
        
        for i in range(num_files):
            file_path = output_path / f"data_{i:04d}.parquet"
            file_path.write_text(f"dummy parquet data for file {i}")
            created_files.append(file_path)
        
        print(f"Created {len(created_files)} dummy parquet files")
        return created_files
    
    def _simulate_block_replication(self, source_path: Path, dest_path: Path):
        """
        Simulate block-level replication using file copy.
        
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
    
    def test_01_file_discovery_after_replication(self):
        """Test file discovery in replicated location."""
        print("\n" + "="*60)
        print("TEST 1: File Discovery After Replication")
        print("="*60)
        
        # Step 1: Create files at source
        source_data_path = self.source_table_path / "data"
        source_files = self._create_dummy_parquet_files(source_data_path, num_files=5)
        
        # Step 2: Simulate block replication
        self._simulate_block_replication(self.source_table_path, self.dr_table_path)
        
        # Step 3: Scan replicated location
        scanner = FileScanner(spark_session=None)  # Local filesystem scanning
        dr_data_path = self.dr_table_path / "data"
        
        found_files = scanner.scan_data_files(str(dr_data_path))
        
        # Verify
        print(f"\n✅ Found {len(found_files)} files at DR location")
        self.assertEqual(len(found_files), 5, "Should find all 5 replicated files")
        
        # Get stats
        stats = scanner.get_file_stats(found_files)
        print(f"   Total size: {stats['total_size_gb']:.6f} GB")
        print(f"   Sample files:")
        for f in stats['sample_files'][:3]:
            print(f"     - {Path(f).name}")
    
    def test_02_incremental_detection(self):
        """Test detection of new files between syncs."""
        print("\n" + "="*60)
        print("TEST 2: Incremental File Detection")
        print("="*60)
        
        # Initial setup: 3 files
        source_data_path = self.source_table_path / "data"
        self._create_dummy_parquet_files(source_data_path, num_files=3)
        self._simulate_block_replication(self.source_table_path, self.dr_table_path)
        
        scanner = FileScanner(spark_session=None)
        dr_data_path = self.dr_table_path / "data"
        
        # First scan
        print("\n[Phase 1] Initial scan...")
        initial_files = scanner.scan_data_files(str(dr_data_path))
        print(f"   Found {len(initial_files)} files initially")
        
        # Simulate these were tracked by Iceberg
        tracked_files = initial_files.copy()
        
        # Add more files at source
        print("\n[Phase 2] Adding 2 more files at source...")
        for i in range(3, 5):
            file_path = source_data_path / f"data_{i:04d}.parquet"
            file_path.write_text(f"dummy parquet data for file {i}")
        
        # Replicate again
        print("\n[Phase 3] Replicating to DR...")
        self._simulate_block_replication(self.source_table_path, self.dr_table_path)
        
        # Second scan
        print("\n[Phase 4] Scanning after replication...")
        current_files = scanner.scan_data_files(str(dr_data_path))
        print(f"   Found {len(current_files)} files total")
        
        # Calculate delta
        print("\n[Phase 5] Calculating delta...")
        delta = calculate_delta(current_files, tracked_files)
        
        print(f"\n📊 Delta Results:")
        print(f"   Total current:  {delta['total_current']}")
        print(f"   Total tracked:  {delta['total_tracked']}")
        print(f"   New files:      {delta['new_count']}")
        print(f"   Common files:   {delta['common_count']}")
        
        # Verify
        self.assertEqual(delta['new_count'], 2, "Should detect 2 new files")
        self.assertEqual(delta['common_count'], 3, "Should have 3 common files")
        
        print("\n✅ Correctly detected incremental changes")
    
    def test_03_state_persistence_across_syncs(self):
        """Test state management across multiple sync operations."""
        print("\n" + "="*60)
        print("TEST 3: State Persistence")
        print("="*60)
        
        state_mgr = StateManager(self.state_dir)
        
        # Simulate first sync
        print("\n[Sync 1] Processing 3 files...")
        state_mgr.save_state(
            db=self.db,
            table=self.table,
            new_files_count=3,
            new_rows_count=300,
            new_files=["file1.parquet", "file2.parquet", "file3.parquet"],
            success=True
        )
        
        # Simulate second sync
        print("[Sync 2] Processing 2 more files...")
        state_mgr.save_state(
            db=self.db,
            table=self.table,
            new_files_count=2,
            new_rows_count=200,
            new_files=["file4.parquet", "file5.parquet"],
            success=True
        )
        
        # Simulate third sync with no changes
        print("[Sync 3] No new files...")
        state_mgr.save_state(
            db=self.db,
            table=self.table,
            new_files_count=0,
            new_rows_count=0,
            new_files=[],
            success=True
        )
        
        # Check state
        stats = state_mgr.get_stats(self.db, self.table)
        
        print(f"\n📊 State Statistics:")
        print(f"   Total runs:        {stats['total_runs']}")
        print(f"   Successful runs:   {stats['successful_runs']}")
        print(f"   Files processed:   {stats['total_files_processed']}")
        print(f"   Rows processed:    {stats['total_rows_processed']}")
        
        # Verify
        self.assertEqual(stats['total_runs'], 3)
        self.assertEqual(stats['successful_runs'], 3)
        self.assertEqual(stats['total_files_processed'], 5)
        self.assertEqual(stats['total_rows_processed'], 500)
        
        print("\n✅ State correctly persisted across syncs")
    
    def test_04_end_to_end_workflow(self):
        """Test complete workflow: replicate -> scan -> detect -> track."""
        print("\n" + "="*60)
        print("TEST 4: End-to-End Workflow")
        print("="*60)
        
        scanner = FileScanner(spark_session=None)
        state_mgr = StateManager(self.state_dir)
        
        source_data_path = self.source_table_path / "data"
        dr_data_path = self.dr_table_path / "data"
        
        # === SYNC 1: Initial sync ===
        print("\n[SYNC 1] Initial sync with 3 files")
        print("-" * 60)
        
        # Create and replicate
        self._create_dummy_parquet_files(source_data_path, num_files=3)
        self._simulate_block_replication(self.source_table_path, self.dr_table_path)
        
        # Scan
        current_files = scanner.scan_data_files(str(dr_data_path))
        tracked_files = set()  # No files tracked yet
        
        # Calculate delta
        delta = calculate_delta(current_files, tracked_files)
        print(f"  New files to process: {delta['new_count']}")
        
        # Save state
        state_mgr.save_state(self.db, self.table, delta['new_count'], 
                            delta['new_count'] * 100, list(delta['new_files']), True)
        
        # Update tracked files (simulating Iceberg metadata update)
        tracked_files = current_files.copy()
        
        print(f"  ✅ Sync 1 complete: {delta['new_count']} files processed")
        
        # === SYNC 2: Incremental sync ===
        print("\n[SYNC 2] Incremental sync with 2 new files")
        print("-" * 60)
        
        # Add more files
        for i in range(3, 5):
            file_path = source_data_path / f"data_{i:04d}.parquet"
            file_path.write_text(f"dummy data {i}")
        
        # Replicate
        self._simulate_block_replication(self.source_table_path, self.dr_table_path)
        
        # Scan
        current_files = scanner.scan_data_files(str(dr_data_path))
        
        # Calculate delta
        delta = calculate_delta(current_files, tracked_files)
        print(f"  New files to process: {delta['new_count']}")
        
        # Save state
        state_mgr.save_state(self.db, self.table, delta['new_count'],
                            delta['new_count'] * 100, list(delta['new_files']), True)
        
        tracked_files = current_files.copy()
        
        print(f"  ✅ Sync 2 complete: {delta['new_count']} files processed")
        
        # === SYNC 3: No changes ===
        print("\n[SYNC 3] Sync with no changes")
        print("-" * 60)
        
        # Scan (no replication, no new files)
        current_files = scanner.scan_data_files(str(dr_data_path))
        
        # Calculate delta
        delta = calculate_delta(current_files, tracked_files)
        print(f"  New files to process: {delta['new_count']}")
        
        # Save state
        state_mgr.save_state(self.db, self.table, delta['new_count'],
                            0, [], True)
        
        print(f"  ✅ Sync 3 complete: No changes detected")
        
        # === FINAL VERIFICATION ===
        print("\n[VERIFICATION] Final state")
        print("-" * 60)
        
        stats = state_mgr.get_stats(self.db, self.table)
        
        print(f"  Total syncs:       {stats['total_runs']}")
        print(f"  Total files:       {stats['total_files_processed']}")
        print(f"  Total rows:        {stats['total_rows_processed']}")
        
        self.assertEqual(stats['total_runs'], 3)
        self.assertEqual(stats['total_files_processed'], 5)
        self.assertEqual(stats['total_rows_processed'], 500)
        
        print("\n✅ End-to-end workflow validated successfully!")


if __name__ == '__main__':
    unittest.main(verbosity=2)

