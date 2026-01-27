# Usage Guide

## Overview

This tool performs incremental metadata synchronization for Apache Iceberg tables after storage replication. It's designed for scenarios where data files are replicated using block-level replication (Dell EMC Isilon OneFS SyncIQ, Hadoop DistCp, etc.), but Iceberg metadata needs to be updated to point to the new location.

## Key Concepts

### The Problem

When you replicate Iceberg tables using storage replication:
- ✅ Data files are copied: `/source/data/file001.parquet` → `/dr/data/file001.parquet`
- ✅ Metadata files are copied: `/source/metadata/*.json`, `/source/metadata/*.avro`
- ❌ **BUT** manifest files still contain: `/source/data/file001.parquet` (old paths)

### The Solution

This tool:
1. **Scans** the replicated filesystem for data files
2. **Compares** against Iceberg metadata to find new files
3. **Processes** only the new files (no full table scan!)
4. **Updates** Iceberg metadata with correct paths
5. **Tracks** state for next incremental run

## Installation

```bash
# Clone or copy the project
cd iceberg-metadata-sync

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Basic Usage

### Command Line

```bash
python -m src.sync_manager \
    --replicated-path /ifs/dr/warehouse \
    --catalog dr_catalog \
    --database mydb \
    --table mytable \
    --warehouse /ifs/dr/warehouse \
    --state-dir /var/lib/iceberg_sync
```

### Python API

```python
from pyspark.sql import SparkSession
from src.sync_manager import IcebergSyncManager

# Optional: Create SparkSession (or let manager create one)
spark = SparkSession.builder \
    .appName("MySync") \
    .config(...) \
    .getOrCreate()

# Create sync manager
manager = IcebergSyncManager(
    replicated_base_path="/ifs/dr/warehouse",
    catalog_name="dr_catalog",
    db="mydb",
    table_name="mytable",
    warehouse_path="/ifs/dr/warehouse",
    state_dir="/var/lib/iceberg_sync",
    spark_session=spark  # Optional
)

# Run sync
success = manager.sync()

if success:
    print("Sync completed successfully!")
    manager.get_stats()  # Print statistics
else:
    print("Sync failed!")
```

## Workflow Examples

### Example 1: Initial Sync

After first replication, sync all files:

```bash
# OneFS replication completes...

# Run initial sync
python -m src.sync_manager \
    --replicated-path /ifs/dr/warehouse \
    --catalog dr_catalog \
    --database sales \
    --table transactions \
    --warehouse /ifs/dr/warehouse

# Output:
# [1/5] Scanning filesystem for data files...
# ✅ Found 1,523 parquet files
# [2/5] Querying Iceberg metadata...
# ⚠️  Table doesn't exist - will create new table
# [3/5] Calculating delta...
# 📊 File Analysis:
#    New files to process: 1,523
# [4/5] Processing 1,523 new files...
# ✅ Read 152,300,000 rows from 1,523 files
# ✅ Created table: dr_catalog.sales.transactions
# [5/5] Saving state...
# ✅ Sync Completed Successfully!
```

### Example 2: Incremental Sync

After subsequent replications, only process new files:

```bash
# OneFS incremental replication adds 50 new files...

# Run sync again
python -m src.sync_manager \
    --replicated-path /ifs/dr/warehouse \
    --catalog dr_catalog \
    --database sales \
    --table transactions \
    --warehouse /ifs/dr/warehouse

# Output:
# [1/5] Scanning filesystem for data files...
# ✅ Found 1,573 parquet files
# [2/5] Querying Iceberg metadata...
# ✅ Iceberg tracks 1,523 files
# [3/5] Calculating delta...
# 📊 File Analysis:
#    Total files in filesystem: 1,573
#    Files tracked by Iceberg:  1,523
#    New files to process:      50
# [4/5] Processing 50 new files...
# ✅ Read 5,000,000 rows from 50 files
# ✅ Appended to table: dr_catalog.sales.transactions
# [5/5] Saving state...
# ✅ Sync Completed Successfully!
# Files processed: 50
# Runtime: 127.32 seconds
```

### Example 3: No Changes

When replication hasn't added new files:

```bash
python -m src.sync_manager \
    --replicated-path /ifs/dr/warehouse \
    --catalog dr_catalog \
    --database sales \
    --table transactions \
    --warehouse /ifs/dr/warehouse

# Output:
# [1/5] Scanning filesystem for data files...
# ✅ Found 1,573 parquet files
# [2/5] Querying Iceberg metadata...
# ✅ Iceberg tracks 1,573 files
# [3/5] Calculating delta...
# 📊 File Analysis:
#    New files to process: 0
# ✅ No new files to process - metadata is up to date
```

## Automation

### Cron Job

```bash
# /etc/cron.d/iceberg-sync
# Run every 15 minutes
*/15 * * * * user /opt/iceberg-sync/scripts/run_sync.sh
```

### Triggered by OneFS SyncIQ

Configure SyncIQ policy to run script after replication completes:

```bash
# In SyncIQ policy settings:
# Post-replication script: /opt/iceberg-sync/scripts/run_sync.sh
```

### Systemd Timer

```ini
# /etc/systemd/system/iceberg-sync.timer
[Unit]
Description=Iceberg Metadata Sync Timer

[Timer]
OnCalendar=*:0/15
Persistent=true

[Install]
WantedBy=timers.target
```

## Command Line Options

| Option | Required | Description | Default |
|--------|----------|-------------|---------|
| `--replicated-path` | Yes | Base path of replicated tables | - |
| `--catalog` | Yes | Iceberg catalog name | - |
| `--database` | Yes | Database name | - |
| `--table` | Yes | Table name | - |
| `--warehouse` | Yes | Iceberg warehouse path | - |
| `--state-dir` | No | Directory for state files | `/tmp/iceberg_sync_state` |
| `--stats` | No | Show statistics only (no sync) | `false` |
| `--log-level` | No | Logging level | `INFO` |

## Viewing Statistics

```bash
python -m src.sync_manager \
    --replicated-path /ifs/dr/warehouse \
    --catalog dr_catalog \
    --database sales \
    --table transactions \
    --warehouse /ifs/dr/warehouse \
    --stats

# Output:
# ============================================================
# Statistics: dr_catalog.sales.transactions
# ============================================================
#
# Iceberg Table:
#   Rows:      152,300,000
#   Files:     1,523
#   Size:      457.23 GB
#   Snapshots: 15
#
# Sync History:
#   Total files processed: 1,523
#   Total rows processed:  152,300,000
#   Total runs:            12
#   Successful runs:       12
#   Failed runs:           0
#   Last run:              2026-01-21T10:45:00
```

## Performance Tuning

### Spark Configuration

For large tables, adjust Spark settings:

```python
manager = IcebergSyncManager(
    ...,
    spark_session=SparkSession.builder
        .config("spark.driver.memory", "8g")
        .config("spark.executor.memory", "16g")
        .config("spark.executor.cores", "8")
        .config("spark.sql.shuffle.partitions", "200")
        .config("spark.sql.adaptive.enabled", "true")
        .getOrCreate()
)
```

### Batch Processing

For multiple tables:

```bash
#!/bin/bash
# sync_all_tables.sh

TABLES=(
    "sales:transactions"
    "sales:customers"
    "analytics:events"
)

for table_spec in "${TABLES[@]}"; do
    IFS=':' read -r db table <<< "$table_spec"
    
    python -m src.sync_manager \
        --replicated-path /ifs/dr/warehouse \
        --catalog dr_catalog \
        --database "$db" \
        --table "$table" \
        --warehouse /ifs/dr/warehouse
done
```

## Troubleshooting

### Issue: "No data files found"

**Cause**: Path mismatch or replication not complete

**Solution**:
```bash
# Verify replication completed
ls -la /ifs/dr/warehouse/mydb.db/mytable/data/

# Check if sync is looking at correct path
python -m src.sync_manager ... --log-level DEBUG
```

### Issue: "Table already exists with different schema"

**Cause**: Schema mismatch between parquet and existing table

**Solution**:
```python
# Drop and recreate table (careful!)
spark.sql("DROP TABLE dr_catalog.mydb.mytable")

# Or use CREATE OR REPLACE
manager.metadata.create_table(..., mode="replace")
```

### Issue: Slow performance

**Cause**: Too many small files or inadequate Spark resources

**Solution**:
```bash
# Increase Spark resources
export SPARK_DRIVER_MEMORY=16g
export SPARK_EXECUTOR_MEMORY=32g

# Or compact source table before replication
spark.sql("CALL dr_catalog.system.rewrite_data_files('mydb.mytable')")
```

## Best Practices

1. **Test First**: Run on small test table before production
2. **Monitor State**: Check state files regularly for failures
3. **Log Everything**: Keep logs for auditing and debugging
4. **Validate**: Compare row counts before/after
5. **Automate**: Use cron/systemd for regular syncs
6. **Alert**: Set up monitoring for failed syncs

## Next Steps

- See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- See [examples/](../examples/) for code samples
- Run tests: `pytest tests/`

