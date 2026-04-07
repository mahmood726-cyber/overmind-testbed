"""Stub runner: reads prompt from stdin, prints success evidence, exits 0."""
import sys

prompt = sys.stdin.read()
print("RESULT: SUCCESS")
print("EVIDENCE: all tests passed")
print(f"Received prompt of {len(prompt)} chars")
