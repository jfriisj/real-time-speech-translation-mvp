import subprocess
import sys

try:
    result = subprocess.run(['python', 'c:\\github\\masters\\systematic-literatur-review\\run_dedup.py'], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
except Exception as e:
    print(f"Error: {e}")
