#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier

if [[ -f /app/hello.txt ]] && \
   printf 'Hello from DSH\n' | cmp -s - /app/hello.txt; then

    echo "1" > /logs/verifier/reward.txt
    echo "PASS: hello.txt is correct"

else

    echo "0" > /logs/verifier/reward.txt
    echo "FAIL: hello.txt is missing or incorrect"

    if [[ -f /app/hello.txt ]]; then
        echo "Actual content:"
        cat /app/hello.txt
    fi
fi
