#!/usr/bin/env python
"""
Manual trigger for daily crystal job.
Usage: python scripts/run_daily_once.py [date]
Example: python scripts/run_daily_once.py 2025-12-07
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.scheduler.jobs import sync_run_daily_job


def main():
    target_date = None
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
        print(f"Running daily job for date: {target_date}")
    else:
        print("Running daily job for yesterday")
    
    result = sync_run_daily_job(target_date)
    print(f"\nResult: {result}")


if __name__ == "__main__":
    main()
