from __future__ import annotations

import argparse
import subprocess
import sys
import time


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, text=True, capture_output=True)


def _containers_stable() -> bool:
    result = _run(["docker", "ps", "--format", "{{.Names}} {{.Status}}"]) 
    if result.returncode != 0:
        return False
    for line in result.stdout.strip().splitlines():
        if not line.strip():
            continue
        _name, status = line.split(" ", maxsplit=1)
        if "Restarting" in status or "Exited" in status:
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify service startup resilience")
    parser.add_argument("--wait-seconds", type=int, default=30)
    args = parser.parse_args()

    up_result = _run(["docker", "compose", "up", "-d"])
    if up_result.returncode != 0:
        print("Failed to start docker compose", file=sys.stderr)
        print(up_result.stderr, file=sys.stderr)
        return 1

    time.sleep(args.wait_seconds)
    if not _containers_stable():
        print("Containers not stable after wait", file=sys.stderr)
        return 1

    print("Startup resilience check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
