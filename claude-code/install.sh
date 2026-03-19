#!/usr/bin/env bash
# =============================================================================
# Claude Code Marketplace Installer (macOS / Linux)
# =============================================================================
#
# Usage:
#   # Install default marketplace (suriyel/longtaskforagent)
#   curl -fsSL https://raw.githubusercontent.com/suriyel/longtaskforagent/main/claude-code/install.sh | bash
#
#   # Install from a different source
#   curl -fsSL ... | bash -s -- <source> [--name <name>] [--update] [--force]
#
# Examples:
#   # Default - installs suriyel/longtaskforagent
#   curl -fsSL https://raw.githubusercontent.com/suriyel/longtaskforagent/main/claude-code/install.sh | bash
#
#   # GitHub shorthand
#   curl -fsSL ... | bash -s -- owner/repo
#
#   # GitLab
#   curl -fsSL ... | bash -s -- https://gitlab.com/company/plugins.git --name company-plugins
#
#   # Self-hosted Git (SSH)
#   curl -fsSL ... | bash -s -- git@git.example.com:team/plugins.git
#
#   # Local path (development)
#   curl -fsSL ... | bash -s -- ./my-marketplace --name test-market
#
# After installation, use Claude Code to install plugins:
#   /plugin install <plugin-name>@<marketplace-name>
#
set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

CLAUDE_PLUGINS_DIR="${HOME}/.claude/plugins"
MARKETPLACES_DIR="${CLAUDE_PLUGINS_DIR}/marketplaces"
KNOWN_MARKETPLACES_FILE="${CLAUDE_PLUGINS_DIR}/known_marketplaces.json"
MARKETPLACE_MANIFEST=".claude-plugin/marketplace.json"

# =============================================================================
# Color Output
# =============================================================================

if [[ -t 1 ]]; then
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[0;33m'
  BLUE='\033[0;34m'
  BOLD='\033[1m'
  RESET='\033[0m'
else
  RED=''
  GREEN=''
  YELLOW=''
  BLUE=''
  BOLD=''
  RESET=''
fi

info()    { echo -e "${BLUE}ℹ${RESET} $*"; }
success() { echo -e "${GREEN}✓${RESET} $*"; }
warn()    { echo -e "${YELLOW}!${RESET} $*"; }
error()   { echo -e "${RED}✗${RESET} $*" >&2; }
die()     { error "$@"; exit 1; }

# =============================================================================
# Argument Parsing
# =============================================================================

# Extract default source from script URL (if piped from curl)
# When run as: curl -fsSL https://raw.githubusercontent.com/owner/repo/main/... | bash
# We can extract owner/repo from the URL
SCRIPT_URL=""
if [[ -n "${BASH_SOURCE[0]}" ]]; then
  # Try to get URL from various sources
  if [[ -f "/proc/$$/fd/0" ]] && [[ -t 0 ]]; then
    : # stdin is terminal, not piped
  fi
fi

# Default source extracted from this script's URL
# This script lives at: https://raw.githubusercontent.com/suriyel/longtaskforagent/main/claude-code/install.sh
# So the default marketplace is: suriyel/longtaskforagent
DEFAULT_SOURCE="suriyel/longtaskforagent"

SOURCE=""
NAME=""
UPDATE=false
FORCE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name|-n)
      NAME="$2"
      shift 2
      ;;
    --update|-u)
      UPDATE=true
      shift
      ;;
    --force|-f)
      FORCE=true
      shift
      ;;
    --help|-h)
      head -35 "$0" | tail -30
      exit 0
      ;;
    -*)
      die "Unknown option: $1\nUse --help for usage information."
      ;;
    *)
      if [[ -z "$SOURCE" ]]; then
        SOURCE="$1"
      else
        die "Multiple sources specified. Please provide only one source."
      fi
      shift
      ;;
  esac
done

# Use default source if none provided
if [[ -z "$SOURCE" ]]; then
  SOURCE="$DEFAULT_SOURCE"
  info "No source specified, using default: $SOURCE"
fi

# =============================================================================
# Helper Functions
# =============================================================================

# Check if command exists
check_cmd() {
  if ! command -v "$1" &>/dev/null; then
    return 1
  fi
  return 0
}

# Parse source URL and determine type
parse_source() {
  local src="$1"

  # Local path: ./path, ../path, /path, ~/
  if [[ "$src" == ./* ]] || [[ "$src" == ../* ]] || [[ "$src" == /* ]] || [[ "$src" == ~* ]]; then
    local abs_path
    abs_path=$(cd "$(dirname "$src")" 2>/dev/null && pwd)/$(basename "$src") 2>/dev/null || abs_path="$src"
    echo "local|$abs_path|$src"
    return 0
  fi

  # GitHub shorthand: owner/repo
  if [[ "$src" =~ ^[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+$ ]]; then
    local owner repo
    owner=$(echo "$src" | cut -d'/' -f1)
    repo=$(echo "$src" | cut -d'/' -f2)
    repo="${repo%.git}"
    echo "github|$owner/$repo|https://github.com/$owner/$repo.git"
    return 0
  fi

  # GitHub URL: https://github.com/owner/repo[.git]
  if [[ "$src" =~ ^https?://github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+?)(\.git)?/?$ ]]; then
    local owner repo
    owner="${BASH_REMATCH[1]}"
    repo="${BASH_REMATCH[2]}"
    echo "github|$owner/$repo|https://github.com/$owner/$repo.git"
    return 0
  fi

  # Git URL (http, https, ssh, git@)
  if [[ "$src" =~ ^(https?|git|ssh):// ]] || [[ "$src" =~ ^git@ ]]; then
    echo "url|$src|$src"
    return 0
  fi

  # Try as local path (relative without ./)
  if [[ -d "$src" ]]; then
    local abs_path
    abs_path=$(cd "$src" && pwd)
    echo "local|$abs_path|$src"
    return 0
  fi

  die "Cannot determine source type: $src\n\nSupported formats:\n  - GitHub shorthand: owner/repo\n  - GitHub URL: https://github.com/owner/repo[.git]\n  - Git URL: https://..., git@..., ssh://...\n  - Local path: ./path, /abs/path, ~/path"
}

# Read JSON field (simple extraction, no jq required)
json_get() {
  local file="$1"
  local field="$2"
  grep -o "\"$field\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" "$file" 2>/dev/null | head -1 | sed 's/.*: *"\([^"]*\)".*/\1/'
}

# Check if marketplace exists in known_marketplaces.json
marketplace_exists() {
  local name="$1"
  [[ -f "$KNOWN_MARKETPLACES_FILE" ]] && grep -q "\"$name\"" "$KNOWN_MARKETPLACES_FILE"
}

# Update known_marketplaces.json
update_known_marketplaces() {
  local name="$1"
  local source_type="$2"
  local source_value="$3"
  local install_location="$4"
  local timestamp
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")

  # Create plugins directory if needed
  mkdir -p "$CLAUDE_PLUGINS_DIR"

  # Initialize file if not exists
  if [[ ! -f "$KNOWN_MARKETPLACES_FILE" ]]; then
    echo '{}' > "$KNOWN_MARKETPLACES_FILE"
  fi

  # Build source object
  local source_json
  case "$source_type" in
    github)
      source_json="{\"source\":\"github\",\"repo\":\"$source_value\"}"
      ;;
    url)
      source_json="{\"source\":\"url\",\"url\":\"$source_value\"}"
      ;;
    local)
      source_json="{\"source\":\"local\",\"path\":\"$source_value\"}"
      ;;
  esac

  # Use python if available for proper JSON handling
  if check_cmd python3; then
    python3 - "$name" "$source_json" "$install_location" "$timestamp" <<'PYTHON' "$KNOWN_MARKETPLACES_FILE"
import json, sys
name, source_json, location, timestamp, filepath = sys.argv[1:6]
with open(filepath, 'r') as f:
    data = json.load(f)
data[name] = {
    "source": json.loads(source_json),
    "installLocation": location,
    "lastUpdated": timestamp
}
with open(filepath, 'w') as f:
    json.dump(data, f, indent=2)
PYTHON
  elif check_cmd python; then
    python - "$name" "$source_json" "$install_location" "$timestamp" <<'PYTHON' "$KNOWN_MARKETPLACES_FILE"
import json, sys
name, source_json, location, timestamp, filepath = sys.argv[1:6]
with open(filepath, 'r') as f:
    data = json.load(f)
data[name] = {
    "source": json.loads(source_json),
    "installLocation": location,
    "lastUpdated": timestamp
}
with open(filepath, 'w') as f:
    json.dump(data, f, indent=2)
PYTHON
  else
    # Fallback: simple text manipulation (less robust)
    warn "Python not found, using fallback JSON update (may be less reliable)"

    # Remove existing entry if present
    local temp_file
    temp_file=$(mktemp)
    grep -v "\"$name\"" "$KNOWN_MARKETPLACES_FILE" > "$temp_file" 2>/dev/null || true

    # Add new entry
    local entry="\"$name\":{\"source\":$source_json,\"installLocation\":\"$install_location\",\"lastUpdated\":\"$timestamp\"}"

    if [[ $(wc -c < "$temp_file") -le 3 ]]; then
      # Empty file, just {}
      echo "{$entry}" > "$KNOWN_MARKETPLACES_FILE"
    else
      # Append to existing
      sed "s/}$/,$entry}/" "$temp_file" > "$KNOWN_MARKETPLACES_FILE"
    fi
    rm -f "$temp_file"
  fi
}

# =============================================================================
# Pre-flight Checks
# =============================================================================

info "Pre-flight checks..."

# Check git
if ! check_cmd git; then
  die "Git is not installed.\n\nInstall git:\n  macOS:   brew install git\n  Ubuntu:  sudo apt install git\n  Fedora:  sudo dnf install git"
fi

# Check python (optional but recommended)
if ! check_cmd python3 && ! check_cmd python; then
  warn "Python not found. JSON updates may be less reliable."
fi

# =============================================================================
# Parse Source
# =============================================================================

info "Parsing source: $SOURCE"

PARSED_SOURCE=$(parse_source "$SOURCE")
SOURCE_TYPE=$(echo "$PARSED_SOURCE" | cut -d'|' -f1)
SOURCE_VALUE=$(echo "$PARSED_SOURCE" | cut -d'|' -f2)
SOURCE_URL=$(echo "$PARSED_SOURCE" | cut -d'|' -f3)

info "Source type: $SOURCE_TYPE"
case "$SOURCE_TYPE" in
  github)
    info "  Repository: $SOURCE_VALUE"
    ;;
  url)
    info "  URL: $SOURCE_VALUE"
    ;;
  local)
    info "  Path: $SOURCE_VALUE"
    ;;
esac

# =============================================================================
# Clone or Copy Marketplace
# =============================================================================

# Create temp directory for git clone
TEMP_DIR=""
cleanup() {
  if [[ -n "$TEMP_DIR" ]] && [[ -d "$TEMP_DIR" ]]; then
    rm -rf "$TEMP_DIR"
  fi
}
trap cleanup EXIT

# Clone or copy to temp location first to get manifest
if [[ "$SOURCE_TYPE" == "local" ]]; then
  LOCAL_PATH="$SOURCE_VALUE"

  if [[ ! -d "$LOCAL_PATH" ]]; then
    die "Local path does not exist: $LOCAL_PATH"
  fi

  MANIFEST_PATH="$LOCAL_PATH/$MARKETPLACE_MANIFEST"
  if [[ ! -f "$MANIFEST_PATH" ]]; then
    die "Marketplace manifest not found: $MANIFEST_PATH\n\nA valid marketplace must contain .claude-plugin/marketplace.json\nSee: https://code.claude.com/docs/en/plugin-marketplaces"
  fi

  MARKETPLACE_NAME=$(json_get "$MANIFEST_PATH" "name")
  if [[ -z "$MARKETPLACE_NAME" ]]; then
    die "Missing required field 'name' in marketplace.json\nFile: $MANIFEST_PATH"
  fi

  # Use provided name or manifest name
  if [[ -n "$NAME" ]]; then
    MARKETPLACE_NAME="$NAME"
  fi

else
  # Git source - clone to temp
  TEMP_DIR=$(mktemp -d)
  info "Cloning: $SOURCE_URL"

  if ! git clone --depth 1 "$SOURCE_URL" "$TEMP_DIR" 2>&1; then
    die "Failed to clone repository: $SOURCE_URL\n\nTroubleshooting:\n  - Check your network connection\n  - Verify the repository URL is correct\n  - For private repos, ensure git credentials are configured:\n    GitHub:    gh auth login\n    GitLab:    Configure ~/.ssh/config or GITLAB_TOKEN\n    Self-hosted: Configure SSH keys or credential helper"
  fi

  MANIFEST_PATH="$TEMP_DIR/$MARKETPLACE_MANIFEST"
  if [[ ! -f "$MANIFEST_PATH" ]]; then
    die "Marketplace manifest not found: $MANIFEST_PATH\n\nA valid marketplace must contain .claude-plugin/marketplace.json\nSee: https://code.claude.com/docs/en/plugin-marketplaces"
  fi

  MARKETPLACE_NAME=$(json_get "$MANIFEST_PATH" "name")
  if [[ -z "$MARKETPLACE_NAME" ]]; then
    die "Missing required field 'name' in marketplace.json\nFile: $MANIFEST_PATH"
  fi

  if [[ -n "$NAME" ]]; then
    MARKETPLACE_NAME="$NAME"
  fi
fi

# Sanitize name for filesystem
SAFE_NAME=$(echo "$MARKETPLACE_NAME" | sed 's/[<>:"|?*]/_/g')
TARGET_DIR="$MARKETPLACES_DIR/$SAFE_NAME"

# =============================================================================
# Handle Existing Marketplace
# =============================================================================

if [[ -d "$TARGET_DIR" ]]; then
  if [[ "$FORCE" == true ]]; then
    warn "Removing existing marketplace: $TARGET_DIR"
    rm -rf "$TARGET_DIR"
  elif [[ "$UPDATE" == true ]]; then
    info "Updating existing marketplace: $TARGET_DIR"
    rm -rf "$TARGET_DIR"
  else
    die "Marketplace already exists: $MARKETPLACE_NAME\n\nLocation: $TARGET_DIR\n\nUse --update to update or --force to reinstall."
  fi
fi

# =============================================================================
# Install Marketplace
# =============================================================================

mkdir -p "$MARKETPLACES_DIR"

if [[ "$SOURCE_TYPE" == "local" ]]; then
  info "Copying from: $LOCAL_PATH"
  info "          to: $TARGET_DIR"
  cp -R "$LOCAL_PATH" "$TARGET_DIR"
else
  info "Installing to: $TARGET_DIR"
  mv "$TEMP_DIR" "$TARGET_DIR"
fi

# =============================================================================
# Register Marketplace
# =============================================================================

info "Registering marketplace: $MARKETPLACE_NAME"
update_known_marketplaces "$MARKETPLACE_NAME" "$SOURCE_TYPE" "$SOURCE_VALUE" "$TARGET_DIR"

# =============================================================================
# Success Output
# =============================================================================

echo ""
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${BOLD}${GREEN}✓ Marketplace installed successfully!${RESET}"
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo "  Name: $MARKETPLACE_NAME"
echo "  Path: $TARGET_DIR"
echo ""

# List plugins if possible
if [[ -f "$TARGET_DIR/$MARKETPLACE_MANIFEST" ]]; then
  PLUGINS_JSON=$(grep -o '"plugins"[[:space:]]*:[[:space:]]*\[[^\]]*\]' "$TARGET_DIR/$MARKETPLACE_MANIFEST" 2>/dev/null | head -1)
  if [[ -n "$PLUGINS_JSON" ]]; then
    # Count plugins
    PLUGIN_COUNT=$(echo "$PLUGINS_JSON" | grep -o '"name"' | wc -l | tr -d ' ')
    if [[ "$PLUGIN_COUNT" -gt 0 ]]; then
      echo "Available plugins ($PLUGIN_COUNT):"

      # Extract plugin names and versions
      if check_cmd python3 || check_cmd python; then
        ${PYTHON_CMD:-python3} - "$TARGET_DIR/$MARKETPLACE_MANIFEST" <<'PYTHON'
import json, sys
with open(sys.argv[1], 'r') as f:
    manifest = json.load(f)
for plugin in manifest.get('plugins', []):
    name = plugin.get('name', 'unknown')
    version = plugin.get('version', 'unknown')
    desc = plugin.get('description', '')
    print(f"  - {name} (v{version})")
    if desc:
        print(f"    {desc}")
PYTHON
      else
        # Fallback: simple grep
        grep -o '"name"[[:space:]]*:[[:space:]]*"[^"]*"' "$TARGET_DIR/$MARKETPLACE_MANIFEST" | head -5 | while read -r line; do
          plugin_name=$(echo "$line" | sed 's/.*: *"\([^"]*\)".*/\1/')
          echo "  - $plugin_name"
        done
      fi
      echo ""
    fi
  fi
fi

echo -e "${BOLD}To install plugins, use Claude Code:${RESET}"
echo "  /plugin install <plugin-name>@$MARKETPLACE_NAME"
echo ""
