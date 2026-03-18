"""
Real-time Ingestion Monitor
Shows live progress of the ingestion service
"""
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import config


def count_files_in_directory(directory: Path) -> int:
    """Count total files in directory (recursive)"""
    if not directory.exists():
        return 0
    
    count = 0
    for root, dirs, files in os.walk(directory):
        count += len(files)
    return count


def get_last_fetched_time() -> str:
    """Get last fetched timestamp"""
    if config.LAST_FETCHED_TIME_FILE.exists():
        try:
            with open(config.LAST_FETCHED_TIME_FILE, 'r') as f:
                timestamp_str = f.read().strip()
                dt = datetime.fromisoformat(timestamp_str)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
    return "Never"


def get_csv_stats() -> dict:
    """Get stats from CSV tracking files"""
    total_success = 0
    total_failed = 0
    
    if not config.ENTRY_TRACK_DIR.exists():
        return {'success': 0, 'failed': 0}
    
    for csv_file in config.ENTRY_TRACK_DIR.glob('*.csv'):
        try:
            with open(csv_file, 'r') as f:
                lines = f.readlines()[1:]  # Skip header
                for line in lines:
                    if ',success,' in line:
                        total_success += 1
                    elif ',failed,' in line:
                        total_failed += 1
        except:
            pass
    
    return {'success': total_success, 'failed': total_failed}


def get_faiss_stats() -> dict:
    """Get FAISS index statistics"""
    total_files = 0
    partitions = 0
    
    if config.VECTOR_DB_DIR.exists():
        for partition_dir in config.VECTOR_DB_DIR.iterdir():
            if partition_dir.is_dir():
                partitions += 1
                files = count_files_in_directory(partition_dir)
                total_files += files
    
    return {'partitions': partitions, 'files': total_files}


def print_status():
    """Print current status"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("=" * 80)
    print(" " * 20 + "CAR MATCH SERVICE - INGESTION MONITOR")
    print("=" * 80)
    print()
    
    # Last fetched time
    last_fetched = get_last_fetched_time()
    print(f"Last Fetched:     {last_fetched}")
    
    # CSV tracking stats
    csv_stats = get_csv_stats()
    print(f"[OK] Total Success: {csv_stats['success']:,}")
    print(f"[ERR] Total Failed: {csv_stats['failed']:,}")
    
    if csv_stats['success'] + csv_stats['failed'] > 0:
        success_rate = (csv_stats['success'] / (csv_stats['success'] + csv_stats['failed'])) * 100
        print(f"Success Rate:     {success_rate:.1f}%")
    
    print()
    
    # FAISS database stats
    faiss_stats = get_faiss_stats()
    print(f"FAISS Partitions: {faiss_stats['partitions']}")
    print(f"FAISS Files:      {faiss_stats['files']}")
    
    print()
    print("-" * 80)
    
    # Configuration
    print(f"Batch Size:       {config.INGESTION_BATCH_SIZE}")
    print(f"Poll Interval:    {config.INGESTION_POLL_INTERVAL}s")
    print(f"Worker Threads:   {config.INGESTION_WORKER_THREADS}")
    print(f"Lookback Hours:   {config.INGESTION_LOOKBACK_HOURS}")
    
    print()
    print("=" * 80)
    print(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Press Ctrl+C to exit")
    print("=" * 80)


def main():
    """Main monitoring loop"""
    print("Starting ingestion monitor...")
    print("Monitoring directories:")
    print(f"  - Vector DB: {config.VECTOR_DB_DIR}")
    print(f"  - Entry Track: {config.ENTRY_TRACK_DIR}")
    print()
    
    try:
        while True:
            print_status()
            time.sleep(5)  # Update every 5 seconds
    except KeyboardInterrupt:
        print("\n\nMonitor stopped.")


if __name__ == "__main__":
    main()
