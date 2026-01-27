"""Script to initialize vector stores with metadata."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.utils.config import load_config
from src.utils.logger import setup_logging
from src.vector_store import create_vector_store
from src.metadata.metadata_manager import MetadataManager


def main():
    """Initialize vector stores."""
    print("=" * 60)
    print("Text-to-SQL Agent - Vector Store Initialization")
    print("=" * 60)
    print()
    
    # Load configuration
    config = load_config()
    setup_logging(config.app.log_level)
    
    logger.info("Initializing vector stores...")
    
    # Create vector store
    vector_store = create_vector_store(config.vector_store)
    logger.info(f"Vector store initialized: {config.vector_store.provider}")
    
    # Create metadata manager
    metadata_manager = MetadataManager(vector_store, config.metadata)
    logger.info("Metadata manager initialized")
    
    # Index all tables
    print("\nIndexing metadata from Hive metastore...")
    print("This may take a few minutes depending on the number of tables.\n")
    
    try:
        result = metadata_manager.index_all_tables(force_refresh=True)
        
        print("\n" + "=" * 60)
        print("Indexing Complete!")
        print("=" * 60)
        print(f"Total tables: {result['total_tables']}")
        print(f"Successfully indexed: {result['indexed']}")
        print(f"Failed: {result['failed']}")
        print(f"Duration: {result['duration']:.2f} seconds")
        print()
        
        if result['failed'] > 0:
            logger.warning(f"{result['failed']} tables failed to index")
        
        logger.info("Vector store initialization complete")
        
    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        print(f"\nError: {e}")
        sys.exit(1)
    
    finally:
        metadata_manager.close()


if __name__ == "__main__":
    main()
