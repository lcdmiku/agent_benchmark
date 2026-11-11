#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from pathlib import Path

files = {
    Path("/app/output/summary.txt"):
        "Project: R3 Multi-file Smoke Test\n"
        "Status: complete\n"
        "Files: 3\n",

    Path("/app/output/data/records.csv"):
        "id,name,status\n"
        "1,alpha,ready\n"
        "2,beta,ready\n"
        "3,gamma,ready\n",

    Path("/app/output/config/settings.json"):
        '{\n'
        '  "project": "R3",\n'
        '  "version": 1,\n'
        '  "enabled": true\n'
        '}\n',
}

for path, content in files.items():
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode("utf-8"))
PY
