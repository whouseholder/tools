"""Unit tests for utility functions."""
import unittest

from src.utils import calculate_delta, format_bytes


class TestUtils(unittest.TestCase):
    """Test utility functions."""
    
    def test_calculate_delta_all_new(self):
        """Test delta calculation with all new files."""
        current = {"file1", "file2", "file3"}
        tracked = set()
        
        delta = calculate_delta(current, tracked)
        
        self.assertEqual(delta['new_count'], 3)
        self.assertEqual(delta['orphaned_count'], 0)
        self.assertEqual(delta['common_count'], 0)
    
    def test_calculate_delta_all_tracked(self):
        """Test delta calculation when all files are tracked."""
        current = {"file1", "file2", "file3"}
        tracked = {"file1", "file2", "file3"}
        
        delta = calculate_delta(current, tracked)
        
        self.assertEqual(delta['new_count'], 0)
        self.assertEqual(delta['orphaned_count'], 0)
        self.assertEqual(delta['common_count'], 3)
    
    def test_calculate_delta_mixed(self):
        """Test delta calculation with mix of new, common, and orphaned."""
        current = {"file1", "file2", "file3", "file4"}
        tracked = {"file2", "file3", "file5"}
        
        delta = calculate_delta(current, tracked)
        
        self.assertEqual(delta['new_count'], 2)  # file1, file4
        self.assertEqual(delta['orphaned_count'], 1)  # file5
        self.assertEqual(delta['common_count'], 2)  # file2, file3
        
        self.assertIn("file1", delta['new_files'])
        self.assertIn("file4", delta['new_files'])
        self.assertIn("file5", delta['orphaned_files'])
    
    def test_format_bytes(self):
        """Test byte formatting."""
        self.assertEqual(format_bytes(0), "0.00 B")
        self.assertEqual(format_bytes(1023), "1023.00 B")
        self.assertEqual(format_bytes(1024), "1.00 KB")
        self.assertEqual(format_bytes(1024 * 1024), "1.00 MB")
        self.assertEqual(format_bytes(1024 * 1024 * 1024), "1.00 GB")
        self.assertEqual(format_bytes(1536 * 1024 * 1024), "1.50 GB")


if __name__ == '__main__':
    unittest.main()

