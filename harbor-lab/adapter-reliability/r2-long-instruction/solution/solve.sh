#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from pathlib import Path

body = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789XYZ"

payload = "".join(
    f"R2-{i:04d}|{body}\n"
    for i in range(256)
).encode("ascii")

assert len(payload) == 12288

Path("/app/long_input.txt").write_bytes(payload)
PY
