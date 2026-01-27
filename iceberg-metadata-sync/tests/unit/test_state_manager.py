"""Unit tests for StateManager."""
import unittest
from pathlib import Path
import tempfile
import shutil
import json

from src.state_manager import StateManager


class TestStateManager(unittest.TestCase):
    """Test StateManager functionality."""
    
    def setUp(self):
        """Create temporary state directory."""
        self.state_dir = tempfile.mkdtemp()
        self.manager = StateManager(self.state_dir)
    
    def tearDown(self):
        """Clean up state directory."""
        shutil.rmtree(self.state_dir)
    
    def test_load_empty_state(self):
        """Test loading state when no previous state exists."""
        state = self.manager.load_state("testdb", "testtable")
        
        self.assertIsNone(state['last_run_time'])
        self.assertEqual(state['total_files_processed'], 0)
        self.assertEqual(state['total_rows_processed'], 0)
        self.assertEqual(len(state['runs']), 0)
    
    def test_save_and_load_state(self):
        """Test saving and loading state."""
        # Save state
        self.manager.save_state(
            db="testdb",
            table="testtable",
            new_files_count=10,
            new_rows_count=1000,
            new_files=["file1.parquet", "file2.parquet"],
            success=True
        )
        
        # Load state
        state = self.manager.load_state("testdb", "testtable")
        
        self.assertIsNotNone(state['last_run_time'])
        self.assertEqual(state['total_files_processed'], 10)
        self.assertEqual(state['total_rows_processed'], 1000)
        self.assertEqual(len(state['runs']), 1)
        self.assertTrue(state['runs'][0]['success'])
    
    def test_accumulate_state(self):
        """Test that state accumulates across multiple saves."""
        # First run
        self.manager.save_state(
            db="testdb",
            table="testtable",
            new_files_count=5,
            new_rows_count=500,
            new_files=["file1.parquet"],
            success=True
        )
        
        # Second run
        self.manager.save_state(
            db="testdb",
            table="testtable",
            new_files_count=3,
            new_rows_count=300,
            new_files=["file2.parquet"],
            success=True
        )
        
        # Check accumulated state
        state = self.manager.load_state("testdb", "testtable")
        
        self.assertEqual(state['total_files_processed'], 8)
        self.assertEqual(state['total_rows_processed'], 800)
        self.assertEqual(len(state['runs']), 2)
    
    def test_failed_run_doesnt_increment_totals(self):
        """Test that failed runs don't increment totals."""
        # Successful run
        self.manager.save_state(
            db="testdb",
            table="testtable",
            new_files_count=5,
            new_rows_count=500,
            new_files=[],
            success=True
        )
        
        # Failed run
        self.manager.save_state(
            db="testdb",
            table="testtable",
            new_files_count=10,
            new_rows_count=1000,
            new_files=[],
            success=False
        )
        
        state = self.manager.load_state("testdb", "testtable")
        
        # Should only count successful run
        self.assertEqual(state['total_files_processed'], 5)
        self.assertEqual(state['total_rows_processed'], 500)
        
        # But should have 2 run records
        self.assertEqual(len(state['runs']), 2)
    
    def test_get_stats(self):
        """Test getting statistics."""
        # Add some runs
        self.manager.save_state("testdb", "testtable", 5, 500, [], True)
        self.manager.save_state("testdb", "testtable", 3, 300, [], True)
        self.manager.save_state("testdb", "testtable", 2, 200, [], False)
        
        stats = self.manager.get_stats("testdb", "testtable")
        
        self.assertEqual(stats['total_runs'], 3)
        self.assertEqual(stats['successful_runs'], 2)
        self.assertEqual(stats['failed_runs'], 1)
        self.assertEqual(stats['total_files_processed'], 8)
    
    def test_clear_state(self):
        """Test clearing state."""
        # Save state
        self.manager.save_state("testdb", "testtable", 5, 500, [], True)
        
        # Verify it exists
        state_file = Path(self.state_dir) / "state_testdb_testtable.json"
        self.assertTrue(state_file.exists())
        
        # Clear state
        self.manager.clear_state("testdb", "testtable")
        
        # Verify it's gone
        self.assertFalse(state_file.exists())


if __name__ == '__main__':
    unittest.main()

