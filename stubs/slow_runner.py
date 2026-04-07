"""Stub runner: sleeps for N seconds (default 15), exits 0."""
import sys
import time

duration = int(sys.argv[1]) if len(sys.argv) > 1 else 15
time.sleep(duration)
print("RESULT: SUCCESS (after delay)")
