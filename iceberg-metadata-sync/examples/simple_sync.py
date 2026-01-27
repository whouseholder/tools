"""
Example: Simple sync for a single table.
"""
from src.sync_manager import IcebergSyncManager

def main():
    # Configure your environment
    REPLICATED_PATH = "/ifs/dr/warehouse"
    CATALOG = "dr_catalog"
    DATABASE = "mydb"
    TABLE = "users"
    WAREHOUSE = "/ifs/dr/warehouse"
    
    print(f"Syncing table: {DATABASE}.{TABLE}")
    print("="*60)
    
    # Create sync manager
    manager = IcebergSyncManager(
        replicated_base_path=REPLICATED_PATH,
        catalog_name=CATALOG,
        db=DATABASE,
        table_name=TABLE,
        warehouse_path=WAREHOUSE,
        state_dir="/tmp/iceberg_sync_state"
    )
    
    # Run sync
    success = manager.sync()
    
    if success:
        print("\n✅ Sync completed successfully!")
        print("\nTable Statistics:")
        manager.get_stats()
    else:
        print("\n❌ Sync failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

