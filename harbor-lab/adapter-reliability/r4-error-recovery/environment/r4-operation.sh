#!/usr/bin/env bash
set -euo pipefail

STATE="/tmp/r4-attempt-count"
OUTPUT="/app/output"

if [[ -f "$STATE" ]]; then
    count=$(cat "$STATE")
else
    count=0
fi

count=$((count + 1))
printf '%s\n' "$count" > "$STATE"

mkdir -p "$OUTPUT"

case "$count" in
    1)
        echo "attempt=1 status=transient_failure" \
            >> "$OUTPUT/attempts.log"

        echo "R4_TRANSIENT_ERROR: simulated temporary failure." >&2
        exit 17
        ;;

    2)
        echo "attempt=2 status=success" \
            >> "$OUTPUT/attempts.log"

        printf 'Recovered after one retry\n' \
            > "$OUTPUT/result.txt"

        echo "R4_SUCCESS: recovery completed."
        ;;

    *)
        echo "attempt=$count status=unexpected_extra_call" \
            >> "$OUTPUT/attempts.log"

        echo "R4_ERROR: unexpected additional invocation." >&2
        exit 18
        ;;
esac
