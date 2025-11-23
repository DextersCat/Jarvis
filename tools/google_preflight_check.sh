#!/usr/bin/env bash
set -euo pipefail
cd /root/JARVIS
output=$(python3 diagnostics/google_services_check.py)
echo "$output"
summary=$(echo "$output" | grep '^Summary:' || true)
if echo "$summary" | grep -q 'gemini:FAIL' && echo "$summary" | grep -q 'custom_search:PASS' && echo "$summary" | grep -q 'gmail:PASS' && echo "$summary" | grep -q 'calendar:PASS' && echo "$summary" | grep -q 'tasks:PASS'; then
  if echo "$summary" | grep -q 'docs:PASS' && echo "$summary" | grep -q 'sheets:PASS' && echo "$summary" | grep -q 'slides:PASS' && echo "$summary" | grep -q 'drive:PASS'; then
    echo "Google preflight PASS (Gemini parked)"
    exit 0
  fi
fi
echo "Google preflight FAIL — investigate before making changes." >&2
exit 1
