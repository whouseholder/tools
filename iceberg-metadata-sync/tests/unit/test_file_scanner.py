"""Unit tests for FileScanner."""
import unittest
from pathlib import Path
import tempfile
import shutil

from src.file_scanner import FileScanner


class TestFileScanner(unittest.TestCase):
    """Test FileScanner functionality."""
    
    def setUp(self):
        """Create temporary test directory with sample files."""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        
        # Create sample directory structure
        (self.test_path / "data" / "subdir1").mkdir(parents=True)
        (self.test_path / "data" / "subdir2").mkdir(parents=True)
        
        # Create sample parquet files
        self.files = [
            self.test_path / "data" / "file1.parquet",
            self.test_path / "data" / "file2.parquet",
            self.test_path / "data" / "subdir1" / "file3.parquet",
            self.test_path / "data" / "subdir2" / "file4.parquet",
        ]
        
        for file_path in self.files:
            file_path.write_text("dummy parquet data")
        
        # Create non-parquet file (should be ignored)
        (self.test_path / "data" / "readme.txt").write_text("readme")
    
    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)
    
    def test_scan_local_files(self):
        """Test scanning local filesystem."""
        scanner = FileScanner(spark_session=None)
        
        data_path = str(self.test_path / "data")
        found_files = scanner.scan_data_files(data_path)
        
        # Should find 4 parquet files
        self.assertEqual(len(found_files), 4)
        
        # Verify files are absolute paths
        for file_path in found_files:
            self.assertTrue(Path(file_path).is_absolute())
            self.assertTrue(file_path.endswith('.parquet'))
    
    def test_scan_empty_directory(self):
        """Test scanning empty directory."""
        scanner = FileScanner(spark_session=None)
        
        empty_dir = self.test_path / "empty"
        empty_dir.mkdir()
        
        found_files = scanner.scan_data_files(str(empty_dir))
        
        self.assertEqual(len(found_files), 0)
    
    def test_scan_nonexistent_directory(self):
        """Test scanning non-existent directory."""
        scanner = FileScanner(spark_session=None)
        
        found_files = scanner.scan_data_files("/nonexistent/path")
        
        self.assertEqual(len(found_files), 0)
    
    def test_get_file_stats(self):
        """Test getting file statistics."""
        scanner = FileScanner(spark_session=None)
        
        data_path = str(self.test_path / "data")
        found_files = scanner.scan_data_files(data_path)
        
        stats = scanner.get_file_stats(found_files)
        
        self.assertEqual(stats['count'], 4)
        self.assertIn('total_size_bytes', stats)
        self.assertIn('sample_files', stats)
        self.assertGreater(stats['total_size_bytes'], 0)


if __name__ == '__main__':
    unittest.main()

