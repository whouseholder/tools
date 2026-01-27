# Iceberg Metadata Sync

Incremental metadata synchronization tool for Apache Iceberg tables after storage replication (OneFS, DistCp, etc.).

## Problem Statement

When migrating or replicating Apache Iceberg tables using block-level replication (Dell EMC Isilon OneFS SyncIQ, Hadoop DistCp, etc.), the data files are copied but the Iceberg manifest files still reference the original storage paths. This tool efficiently updates Iceberg metadata to point to the new storage location without requiring full table scans.

## Features

- ✅ **Incremental Updates** - Only processes new files since last sync
- ✅ **No Full Table Scans** - Uses metadata comparison for efficiency
- ✅ **State Management** - Tracks processed files across runs
- ✅ **Iceberg 1.2+ Support** - Compatible with older Iceberg versions
- ✅ **Production Ready** - Error handling, logging, and monitoring
- ✅ **Flexible** - Works with any storage backend (HDFS, S3, ADLS, OneFS)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run initial sync
python -m src.sync_manager \
    --replicated-path /ifs/dr/warehouse \
    --catalog dr_catalog \
    --database mydb \
    --table mytable \
    --warehouse /ifs/dr/warehouse

# Run incremental sync (only new files)
python -m src.sync_manager \
    --replicated-path /ifs/dr/warehouse \
    --catalog dr_catalog \
    --database mydb \
    --table mytable \
    --warehouse /ifs/dr/warehouse
```

## Architecture

```
┌─────────────────────┐
│ Source Storage      │
│ (e.g., /ifs/prod)   │
└──────────┬──────────┘
           │
           │ OneFS SyncIQ / DistCp
           │ (Block Replication)
           ▼
┌─────────────────────┐
│ DR Storage          │
│ (e.g., /ifs/dr)     │
└──────────┬──────────┘
           │
           │ Iceberg Metadata Sync
           │ (This Tool)
           ▼
┌─────────────────────┐
│ Updated Iceberg     │
│ Metadata            │
└─────────────────────┘
```

## How It Works

1. **Scan Filesystem** - List all parquet files in replicated location
2. **Query Iceberg Metadata** - Get files currently tracked by Iceberg
3. **Calculate Delta** - Find new files not yet in metadata
4. **Selective Read** - Read only new parquet files (not entire table)
5. **Append to Iceberg** - Add new data with updated manifest paths
6. **Save State** - Checkpoint for next run

## Project Structure

```
iceberg-metadata-sync/
├── src/
│   ├── sync_manager.py      # Main sync orchestration
│   ├── file_scanner.py      # Filesystem scanning
│   ├── metadata_tracker.py  # Iceberg metadata operations
│   ├── state_manager.py     # Persistence and checkpointing
│   └── utils.py            # Utilities
├── tests/
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── fixtures/           # Test data
├── config/
│   └── sync_config.yaml    # Configuration templates
├── scripts/
│   ├── setup.sh           # Environment setup
│   └── run_sync.sh        # Automation script
├── examples/
│   └── sample_sync.py     # Usage examples
└── docs/
    ├── USAGE.md           # Detailed usage guide
    └── ARCHITECTURE.md    # Architecture details
```

## Performance

| Table Size | Approach | Time | Cost |
|------------|----------|------|------|
| 5TB (10K files) | Full Scan | 2 hours | High |
| 5TB (50 new files) | Incremental | 5 minutes | Low |

## Requirements

- Python 3.8+
- PySpark 3.2+
- Apache Iceberg 1.2+
- Access to replicated storage

## Documentation

- [Usage Guide](docs/USAGE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)

## License

MIT

