"""
File scanner for discovering data files in replicated storage.
"""
import logging
from typing import Set, List
from pathlib import Path

logger = logging.getLogger(__name__)


class FileScanner:
    """
    Scans filesystem to discover parquet data files.
    Works with local filesystem or distributed storage via Spark.
    """
    
    def __init__(self, spark_session=None):
        """
        Initialize file scanner.
        
        Args:
            spark_session: Optional SparkSession for distributed scanning
        """
        self.spark = spark_session
    
    def scan_data_files(self, data_path: str, file_extension: str = ".parquet") -> Set[str]:
        """
        Scan directory recursively for data files.
        
        Args:
            data_path: Root path to scan
            file_extension: File extension to filter (default: .parquet)
        
        Returns:
            Set of absolute file paths
        """
        if self.spark:
            return self._scan_with_spark(data_path, file_extension)
        else:
            return self._scan_local(data_path, file_extension)
    
    def _scan_with_spark(self, data_path: str, file_extension: str) -> Set[str]:
        """Scan using Spark's Hadoop FileSystem API (efficient for distributed storage)."""
        logger.info(f"Scanning with Spark: {data_path}")
        
        sc = self.spark.sparkContext
        jvm = sc._jvm
        hadoop_conf = sc._jsc.hadoopConfiguration()
        
        try:
            fs = jvm.org.apache.hadoop.fs.FileSystem.get(
                jvm.java.net.URI(data_path),
                hadoop_conf
            )
            
            path = jvm.org.apache.hadoop.fs.Path(data_path)
            
            if not fs.exists(path):
                logger.warning(f"Path does not exist: {data_path}")
                return set()
            
            data_files = set()
            file_iterator = fs.listFiles(path, True)  # recursive=True
            
            file_count = 0
            while file_iterator.hasNext():
                file_status = file_iterator.next()
                file_path = file_status.getPath().toString()
                
                if file_path.endswith(file_extension):
                    data_files.add(file_path)
                    file_count += 1
            
            logger.info(f"Found {len(data_files)} {file_extension} files")
            return data_files
            
        except Exception as e:
            logger.error(f"Error scanning with Spark: {e}")
            raise
    
    def _scan_local(self, data_path: str, file_extension: str) -> Set[str]:
        """Scan using local filesystem (for testing)."""
        logger.info(f"Scanning local filesystem: {data_path}")
        
        path = Path(data_path)
        
        if not path.exists():
            logger.warning(f"Path does not exist: {data_path}")
            return set()
        
        # Recursively find all files with extension
        data_files = set()
        for file_path in path.rglob(f"*{file_extension}"):
            if file_path.is_file():
                data_files.add(str(file_path.absolute()))
        
        logger.info(f"Found {len(data_files)} {file_extension} files")
        return data_files
    
    def get_file_stats(self, file_paths: Set[str]) -> dict:
        """
        Get basic statistics about discovered files.
        
        Args:
            file_paths: Set of file paths
        
        Returns:
            Dictionary with stats (count, total_size, etc.)
        """
        stats = {
            'count': len(file_paths),
            'sample_files': sorted(list(file_paths))[:5]
        }
        
        # Try to get size information
        if not self.spark:
            total_size = 0
            for file_path in file_paths:
                try:
                    total_size += Path(file_path).stat().st_size
                except:
                    pass
            stats['total_size_bytes'] = total_size
            stats['total_size_gb'] = total_size / (1024**3)
        
        return stats

