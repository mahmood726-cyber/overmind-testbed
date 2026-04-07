"""Stub runner: prints the same error line 5 times, exits 1."""
import time

for _ in range(5):
    print("Error: connection refused at 10:30:01 code 42", flush=True)
    time.sleep(0.1)

raise SystemExit(1)
