#!/usr/bin/env bash
# =============================================================================
# Claude Code Marketplace Installer (macOS / Linux)
# =============================================================================
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/suriyel/longtaskforagent/main/claude-code/install.sh | bash
#
# After installation, use Claude Code to install plugins:
#   /plugin install long-task@longtaskforagent
#
set -euo pipefail

# =============================================================================
# Configuration (modify these for different marketplaces)
# =============================================================================

MARKETPLACE_GIT_URL="https://github.com/suriyel/longtaskforagent.git"
MARKETPLACE_NAME="longtaskforagent"

# =============================================================================
# Paths
# =============================================================================

CLAUDE_PLUGINS_DIR="${HOME}/.claude/plugins"
MARKETPLACES_DIR="${CLAUDE_PLUGINS_DIR}/marketplaces"
TARGET_DIR="${MARKETPLACES_DIR}/${MARKETPLACE_NAME}"
KNOWN_MARKETPLACES_FILE="${CLAUDE_PLUGINS_DIR}/known_marketplaces.json"

# =============================================================================
# Color Output
# =============================================================================

if [[ -t 1 ]]; then
  GREEN='\033[0;32m'
  BLUE='\033[0;34m'
  BOLD='\033[1m'
  RESET='\033[0m'
else
  GREEN=''
  BLUE=''
  BOLD=''
  RESET=''
fi

info()    { echo -e "${BLUE}ℹ${RESET} $*"; }
success() { echo -e "${GREEN}✓${RESET} $*"; }

# =============================================================================
# Pre-flight Check
# =============================================================================

if ! command -v git &>/dev/null; then
  echo "Error: git is not installed" >&2
  exit 1
fi

# =============================================================================
# Install
# =============================================================================

info "Installing marketplace: $MARKETPLACE_NAME"

# Remove existing if present
if [[ -d "$TARGET_DIR" ]]; then
  info "Removing existing installation..."
  rm -rf "$TARGET_DIR"
fi

# Clone repository
info "Cloning from: $MARKETPLACE_GIT_URL"
mkdir -p "$MARKETPLACES_DIR"
git clone --depth 1 "$MARKETPLACE_GIT_URL" "$TARGET_DIR"

# Update known_marketplaces.json
info "Registering marketplace..."
mkdir -p "$CLAUDE_PLUGINS_DIR"

if [[ ! -f "$KNOWN_MARKETPLACES_FILE" ]]; then
  echo '{}' > "$KNOWN_MARKETPLACES_FILE"
fi

# Use Python for reliable JSON update
if command -v python3 &>/dev/null || command -v python &>/dev/null; then
  PYTHON_CMD=$(command -v python3 || command -v python)
  "$PYTHON_CMD" - "$MARKETPLACE_NAME" "$MARKETPLACE_GIT_URL" "$TARGET_DIR" <<'PYTHON' "$KNOWN_MARKETPLACES_FILE"
import json, sys
name, git_url, target_dir, filepath = sys.argv[1:5]
with open(filepath, 'r') as f:
    data = json.load(f)
from datetime import datetime
data[name] = {
    "source": {"source": "github", "repo": git_url.replace("https://github.com/", "").replace(".git", "")},
    "installLocation": target_dir,
    "lastUpdated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
}
with open(filepath, 'w') as f:
    json.dump(data, f, indent=2)
PYTHON
fi

# =============================================================================
# Success
# =============================================================================

echo ""
echo -e "${BOLD}${GREEN}✓ Marketplace installed successfully!${RESET}"
echo ""
echo "  Name: $MARKETPLACE_NAME"
echo "  Path: $TARGET_DIR"
echo ""
echo -e "${BOLD}To install plugins, use Claude Code:${RESET}"
echo "  /plugin install long-task@$MARKETPLACE_NAME"
echo ""
