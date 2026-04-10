#!/usr/bin/env bash
set -uo pipefail

PING_URL="${1:-}"
REPO_DIR="${2:-.}"

if [ -z "$PING_URL" ]; then
  echo "Usage: $0 <ping_url> [repo_dir]"
  exit 1
fi

PING_URL="${PING_URL%/}"
PASS=0

pass() { echo "PASSED -- $1"; PASS=$((PASS + 1)); }
fail() { echo "FAILED -- $1"; }

echo "========================================"
echo "  OpenEnv Submission Validator"
echo "========================================"
echo "Repo:     $REPO_DIR"
echo "Ping URL: $PING_URL"
echo ""

echo "Step 1/3: Pinging HF Space..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "Content-Type: application/json" -d '{}' \
  "$PING_URL/reset" --max-time 30)

if [ "$HTTP_CODE" = "200" ]; then
  pass "HF Space is live and responds to /reset"
else
  fail "HF Space /reset returned HTTP $HTTP_CODE"
  exit 1
fi

echo "Step 2/3: Running docker build..."
if docker build "$REPO_DIR" 2>&1; then
  pass "Docker build succeeded"
else
  fail "Docker build failed"
  exit 1
fi

echo "Step 3/3: Running openenv validate..."
if (cd "$REPO_DIR" && openenv validate 2>&1); then
  pass "openenv validate passed"
else
  fail "openenv validate failed"
  exit 1
fi

echo ""
echo "========================================"
echo "  All 3/3 checks passed!"
echo "  Your submission is ready to submit."
echo "========================================"
