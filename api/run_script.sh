# !/bin/sh

SCRIPTS=(
    "receiver.enhance_process.py"
    "receiver.enhance_update.py"
    "receiver.relevance_process.py"
)

# Base directory for scripts (update this path)
BASE_DIR="subscriber"

# Virtual environment Python interpreter (update this path)
PYTHON_INTERPRETER="python3"

# Log directory (update this path)
LOG_DIR="/var/log"

# Loop through each script
for SCRIPT in "${SCRIPTS[@]}"; do
    COUNT=$(pgrep -f "$SCRIPT" | wc -l)
    # Check if the script is already running
    if [ "$COUNT" -eq 0 ]; then
        echo "No instances of $SCRIPT are running. Starting the script..."
        $PYTHON_INTERPRETER "$BASE_DIR/$SCRIPT" "103.42.50.120" "5008" >> "$LOG_DIR/$SCRIPT.log" 2>&1 &
    else
        echo "$SCRIPT is already running ($COUNT instance(s)). No Action."
    fi
done