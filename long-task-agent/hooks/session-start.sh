#!/bin/bash
# session-start.sh — Auto-inject long-task-agent context on session start
#
# This hook runs on: session start, resume, clear, compact
# It injects the Worker guide content so the agent always has context.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check if this is a long-task project (has feature-list.json)
if [ ! -f "feature-list.json" ] && [ ! -f "*/feature-list.json" ]; then
    # Not a long-task project — skip injection
    exit 0
fi

# Read the long-task-guide.md if it exists
GUIDE_FILE=""
if [ -f "long-task-guide.md" ]; then
    GUIDE_FILE="long-task-guide.md"
fi

if [ -z "$GUIDE_FILE" ]; then
    exit 0
fi

# Read guide content
GUIDE_CONTENT=$(<"$GUIDE_FILE")

# Escape for JSON
GUIDE_CONTENT="${GUIDE_CONTENT//\\/\\\\}"
GUIDE_CONTENT="${GUIDE_CONTENT//\"/\\\"}"
GUIDE_CONTENT="${GUIDE_CONTENT//$'\n'/\\n}"
GUIDE_CONTENT="${GUIDE_CONTENT//$'\r'/}"
GUIDE_CONTENT="${GUIDE_CONTENT//$'\t'/\\t}"

# Output as user message to inject context
cat <<JSONEOF
{
  "result": "LONG-TASK-AGENT ACTIVE: This is a multi-session project. Read long-task-guide.md, task-progress.md, and feature-list.json to orient yourself before starting work.",
  "continue": true
}
JSONEOF
