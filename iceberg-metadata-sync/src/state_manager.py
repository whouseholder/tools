"""
State manager for tracking sync progress across runs.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


class StateManager:
    """
    Manages persistent state for incremental syncs.
    Tracks processed files, run history, and sync metadata.
    """
    
    def __init__(self, state_dir: str):
        """
        Initialize state manager.
        
        Args:
            state_dir: Directory to store state files
        """
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_state_file(self, db: str, table: str) -> Path:
        """Get path to state file for a table."""
        return self.state_dir / f"state_{db}_{table}.json"
    
    def load_state(self, db: str, table: str) -> Dict:
        """
        Load state from previous run.
        
        Args:
            db: Database name
            table: Table name
        
        Returns:
            State dictionary
        """
        state_file = self._get_state_file(db, table)
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    logger.info(f"Loaded state from: {state_file}")
                    logger.info(f"Last run: {state.get('last_run_time', 'Never')}")
                    return state
            except Exception as e:
                logger.warning(f"Error loading state file: {e}")
        
        logger.info("No previous state found, starting fresh")
        return self._create_empty_state()
    
    def _create_empty_state(self) -> Dict:
        """Create empty state structure."""
        return {
            'last_run_time': None,
            'total_files_processed': 0,
            'total_rows_processed': 0,
            'runs': [],
            'processed_files': []
        }
    
    def save_state(
        self, 
        db: str, 
        table: str, 
        new_files_count: int,
        new_rows_count: int,
        new_files: List[str],
        success: bool = True
    ):
        """
        Save state after sync run.
        
        Args:
            db: Database name
            table: Table name
            new_files_count: Number of files processed in this run
            new_rows_count: Number of rows processed in this run
            new_files: List of file paths processed
            success: Whether run was successful
        """
        state = self.load_state(db, table)
        
        run_time = datetime.now().isoformat()
        
        # Update state
        state['last_run_time'] = run_time
        
        if success:
            state['total_files_processed'] += new_files_count
            state['total_rows_processed'] += new_rows_count
        
        # Add run record
        state['runs'].append({
            'timestamp': run_time,
            'files_processed': new_files_count,
            'rows_processed': new_rows_count,
            'success': success
        })
        
        # Keep last 100 runs
        state['runs'] = state['runs'][-100:]
        
        # Keep track of recently processed files (last 10000)
        state['processed_files'] = (state.get('processed_files', []) + new_files)[-10000:]
        
        # Save to file
        state_file = self._get_state_file(db, table)
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            logger.info(f"Saved state to: {state_file}")
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def get_stats(self, db: str, table: str) -> Dict:
        """
        Get statistics from state.
        
        Args:
            db: Database name
            table: Table name
        
        Returns:
            Statistics dictionary
        """
        state = self.load_state(db, table)
        
        successful_runs = [r for r in state.get('runs', []) if r['success']]
        failed_runs = [r for r in state.get('runs', []) if not r['success']]
        
        return {
            'total_files_processed': state.get('total_files_processed', 0),
            'total_rows_processed': state.get('total_rows_processed', 0),
            'last_run_time': state.get('last_run_time'),
            'total_runs': len(state.get('runs', [])),
            'successful_runs': len(successful_runs),
            'failed_runs': len(failed_runs),
            'recent_runs': state.get('runs', [])[-5:]
        }
    
    def clear_state(self, db: str, table: str):
        """
        Clear state for a table (useful for testing or reprocessing).
        
        Args:
            db: Database name
            table: Table name
        """
        state_file = self._get_state_file(db, table)
        if state_file.exists():
            state_file.unlink()
            logger.info(f"Cleared state: {state_file}")

