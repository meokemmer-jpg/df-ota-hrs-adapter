#!/bin/bash
# DF-OTA-Hrs-Adapter Mac LaunchAgent Runner [CRUX-MK]
# K16 concurrent_spawn protection via mkdir-Mutex
# Welle-37

set -euo pipefail

LOCK_DIR="/tmp/df-ota-hrs-adapter.lock"
LOCK_AGE_LIMIT_S=21600  # 6h

if [ -d "$LOCK_DIR" ]; then
  LOCK_MTIME=$(stat -f %m "$LOCK_DIR" 2>/dev/null || echo 0)
  LOCK_AGE_S=$(( $(date +%s) - LOCK_MTIME ))
  if [ "$LOCK_AGE_S" -gt "$LOCK_AGE_LIMIT_S" ]; then
    rm -rf "$LOCK_DIR"
  fi
fi

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "[df-ota-hrs-adapter] K16 lock held, exiting (ok)" >&2
  exit 3
fi
echo "$$" > "$LOCK_DIR/pid"
trap 'rm -rf "$LOCK_DIR"' EXIT INT TERM

cd "$(dirname "$0")/.."
PYTHONPATH="$(pwd):${PYTHONPATH:-}" python3 -c "
import sys
sys.path.insert(0, '.')
from src.adapter_orchestrator import HrsAdapterOrchestrator
orch = HrsAdapterOrchestrator()
report = orch.run()
print(f'[df-ota-hrs-adapter] loop_id={report.loop_id} status={report.final_status} sandbox={report.sandbox_mode}')
sys.exit(0 if report.final_status in ('complete', 'partial') else 1)
"
