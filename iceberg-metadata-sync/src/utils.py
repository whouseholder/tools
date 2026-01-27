"""
Utility functions for Iceberg metadata sync.
"""
import logging
from typing import Set


def calculate_delta(current_files: Set[str], tracked_files: Set[str]) -> dict:
    """
    Calculate differences between filesystem and Iceberg metadata.
    
    Args:
        current_files: Files found in filesystem
        tracked_files: Files tracked by Iceberg
    
    Returns:
        Dictionary with delta statistics
    """
    new_files = current_files - tracked_files
    orphaned_files = tracked_files - current_files
    common_files = current_files & tracked_files
    
    return {
        'new_files': new_files,
        'orphaned_files': orphaned_files,
        'common_files': common_files,
        'new_count': len(new_files),
        'orphaned_count': len(orphaned_files),
        'common_count': len(common_files),
        'total_current': len(current_files),
        'total_tracked': len(tracked_files)
    }


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file to write logs to
    """
    handlers = [logging.StreamHandler()]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes into human-readable string.
    
    Args:
        bytes_value: Number of bytes
    
    Returns:
        Formatted string (e.g., "1.5 GB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def print_summary(delta: dict, run_time_seconds: float = None):
    """
    Print a summary of the sync operation.
    
    Args:
        delta: Delta dictionary from calculate_delta
        run_time_seconds: Optional runtime duration
    """
    print("\n" + "="*80)
    print("Sync Summary")
    print("="*80)
    print(f"Files in filesystem:      {delta['total_current']:,}")
    print(f"Files tracked by Iceberg: {delta['total_tracked']:,}")
    print(f"New files to process:     {delta['new_count']:,}")
    
    if delta['orphaned_count'] > 0:
        print(f"⚠️  Orphaned files:         {delta['orphaned_count']:,}")
        print("   (tracked by Iceberg but not in filesystem)")
    
    if run_time_seconds:
        print(f"\nRuntime: {run_time_seconds:.2f} seconds")
    
    print("="*80 + "\n")

