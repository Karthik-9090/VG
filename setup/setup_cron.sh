#!/bin/bash
# Setup Cron for hourly AQI collection (Linux/macOS)
# Run this script to automatically create crontab entry

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_EXECUTABLE=$(which python3)
COLLECTOR_SCRIPT="$PROJECT_ROOT/collector.py"
LOG_FILE="$PROJECT_ROOT/data-pipeline/logs/cron.log"

echo ""
echo "=========================================================================="
echo "Cron Setup for VayuGuard AQI Collection"
echo "=========================================================================="
echo ""
echo "Project Root: $PROJECT_ROOT"
echo "Python Executable: $PYTHON_EXECUTABLE"
echo "Collector Script: $COLLECTOR_SCRIPT"
echo "Log File: $LOG_FILE"
echo ""

# Create cron entry
CRON_ENTRY="0 * * * * cd $PROJECT_ROOT && $PYTHON_EXECUTABLE $COLLECTOR_SCRIPT >> $LOG_FILE 2>&1"

# Check if cron already exists
if crontab -l 2>/dev/null | grep -q "collector.py"; then
    echo "⚠️  Cron entry for collector.py already exists!"
    echo ""
    echo "Current crontab:"
    crontab -l | grep "collector.py" || true
    echo ""
    read -p "Do you want to replace it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remove old entry
        (crontab -l 2>/dev/null | grep -v "collector.py" || true) | crontab -
        echo "✅ Old cron entry removed"
    else
        echo "❌ Setup cancelled"
        exit 1
    fi
fi

# Add new cron entry
(crontab -l 2>/dev/null || true; echo "$CRON_ENTRY") | crontab -

echo "✅ Cron entry created successfully!"
echo ""
echo "=========================================================================="
echo "CRON ENTRY DETAILS"
echo "=========================================================================="
echo ""
echo "Cron Expression: 0 * * * * (every hour at minute 0)"
echo "Full Command:"
echo "  $CRON_ENTRY"
echo ""

echo "=========================================================================="
echo "VERIFICATION"
echo "=========================================================================="
echo ""
echo "To verify the cron job:"
echo "  crontab -l"
echo ""
echo "View cron logs:"
echo "  tail -f $LOG_FILE"
echo ""

echo "=========================================================================="
echo "MANUAL TESTING"
echo "=========================================================================="
echo ""
echo "To test the collection script manually:"
echo "  cd $PROJECT_ROOT"
echo "  RUN_ONCE=1 python3 collector.py"
echo ""

echo "=========================================================================="
echo "DISABLE CRON"
echo "=========================================================================="
echo ""
echo "To disable the cron job:"
echo "  crontab -e"
echo "  # Comment out or delete the line containing 'collector.py'"
echo ""
echo "To remove completely:"
echo "  (crontab -l | grep -v 'collector.py') | crontab -"
echo ""

echo "=========================================================================="
echo ""
