#!/bin/bash

# ================= CONFIGURATION ================= #
BASE_DIR="/Users/jihan/JobData"
PYTHON_BIN="/Library/Frameworks/Python.framework/Versions/3.12/bin/python3"
SCRIPT="$BASE_DIR/BDjobsMaster.py"
RUN_LOG="$BASE_DIR/launchd_run.log"

# ================= START LOG ================= #
echo "[$(date)] 🚀 Starting Bdjobs scraper..." >> "$RUN_LOG"

# ================= KEEP MAC AWAKE ================= #
# -d: prevent display sleep
# -i: prevent idle sleep
# -m: prevent disk sleep
# -s: prevent system sleep
# -u: user active assertion
caffeinate -dimsu &  
CAFFEINATE_PID=$!

# ================= RUN PYTHON SCRIPT ================= #
"$PYTHON_BIN" "$SCRIPT" >> "$RUN_LOG" 2>&1
EXIT_CODE=$?

# ================= ALLOW MAC TO SLEEP ================= #
kill $CAFFEINATE_PID

# ================= LOG RESULT ================= #
if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date)] ✅ Bdjobs scraper finished successfully." >> "$RUN_LOG"
else
    echo "[$(date)] ❌ Bdjobs scraper failed with exit code $EXIT_CODE." >> "$RUN_LOG"
fi
