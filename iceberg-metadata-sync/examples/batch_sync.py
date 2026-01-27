"""
Example: Sync multiple tables in batch.
"""
from src.sync_manager import IcebergSyncManager
from pyspark.sql import SparkSession

def sync_multiple_tables(tables_config):
    """
    Sync multiple tables using shared SparkSession.
    
    Args:
        tables_config: List of dicts with table configuration
    """
    # Create shared Spark session (reuse across tables)
    spark = SparkSession.builder \
        .appName("Iceberg-Multi-Table-Sync") \
        .config("spark.jars.packages",
                "org.apache.iceberg:iceberg-spark-runtime-3.3_2.12:1.2.0") \
        .config("spark.sql.extensions",
                "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.driver.memory", "8g") \
        .config("spark.executor.memory", "16g") \
        .getOrCreate()
    
    results = []
    
    for config in tables_config:
        db = config['database']
        table = config['table']
        
        print(f"\n{'='*80}")
        print(f"Syncing: {db}.{table}")
        print(f"{'='*80}")
        
        try:
            manager = IcebergSyncManager(
                replicated_base_path=config['replicated_path'],
                catalog_name=config['catalog'],
                db=db,
                table_name=table,
                warehouse_path=config['warehouse'],
                state_dir=config.get('state_dir', '/tmp/iceberg_sync_state'),
                spark_session=spark  # Reuse spark session
            )
            
            success = manager.sync()
            results.append({
                'table': f"{db}.{table}",
                'success': success
            })
            
        except Exception as e:
            print(f"❌ Error syncing {db}.{table}: {e}")
            results.append({
                'table': f"{db}.{table}",
                'success': False,
                'error': str(e)
            })
    
    spark.stop()
    
    # Print summary
    print(f"\n{'='*80}")
    print("SYNC SUMMARY")
    print(f"{'='*80}")
    
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print(f"Total tables: {len(results)}")
    print(f"Successful:   {successful}")
    print(f"Failed:       {failed}")
    
    if failed > 0:
        print("\nFailed tables:")
        for r in results:
            if not r['success']:
                error = r.get('error', 'Unknown error')
                print(f"  - {r['table']}: {error}")
    
    return failed == 0


def main():
    # Configure tables to sync
    tables = [
        {
            'replicated_path': '/ifs/dr/warehouse',
            'catalog': 'dr_catalog',
            'database': 'sales',
            'table': 'transactions',
            'warehouse': '/ifs/dr/warehouse'
        },
        {
            'replicated_path': '/ifs/dr/warehouse',
            'catalog': 'dr_catalog',
            'database': 'sales',
            'table': 'customers',
            'warehouse': '/ifs/dr/warehouse'
        },
        {
            'replicated_path': '/ifs/dr/warehouse',
            'catalog': 'dr_catalog',
            'database': 'analytics',
            'table': 'events',
            'warehouse': '/ifs/dr/warehouse'
        }
    ]
    
    success = sync_multiple_tables(tables)
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())

