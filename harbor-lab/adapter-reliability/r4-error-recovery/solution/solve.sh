#!/usr/bin/env bash
set -euo pipefail

# First invocation must fail with exit code 17.
if /usr/local/bin/r4-operation; then
    echo "ERROR: first invocation unexpectedly succeeded."
    exit 1
else
    rc=$?
    if [[ "$rc" -ne 17 ]]; then
        echo "ERROR: unexpected exit code: $rc"
        exit 1
    fi
fi

# Retry exactly once.
 /usr/local/bin/r4-operation

# Verify the output.
test "$(cat /app/output/result.txt)" = \
    "Recovered after one retry"

test "$(cat /app/output/attempts.log)" = \
    "$(printf 'attempt=1 status=transient_failure\nattempt=2 status=success')"

echo "R4 Oracle solution completed."
