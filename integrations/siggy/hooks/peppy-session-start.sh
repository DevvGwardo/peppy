#!/bin/bash
# Peppy Session Start Hook for Siggy
# Automatically indexes the codebase when a Siggy workflow starts
#
# Installation:
#   Copy to: .siggy/hooks/session-start.sh
#   Or symlink: ln -s /path/to/peppy/integrations/siggy/hooks/peppy-session-start.sh .siggy/hooks/session-start.sh
#
# Configuration (in .siggy.yml):
#   plugins:
#     peppy:
#       enabled: true
#       auto_index: true
#       reindex_interval: 60  # minutes

set -euo pipefail

# Get the current working directory (project root)
PROJECT_ROOT="${PWD}"

# Configuration defaults (can be overridden by environment variables)
PEPPY_ENABLED="${PEPPY_ENABLED:-true}"
PEPPY_AUTO_INDEX="${PEPPY_AUTO_INDEX:-true}"
PEPPY_REINDEX_INTERVAL="${PEPPY_REINDEX_INTERVAL:-60}"  # minutes
PEPPY_INDEX_PATH="${PEPPY_INDEX_PATH:-.}"

# Cache directory
PEPPY_CACHE_DIR="${PROJECT_ROOT}/.peppy_cache"
INDEX_MARKER="${PEPPY_CACHE_DIR}/.last_indexed"
CONFIG_CACHE="${PEPPY_CACHE_DIR}/.siggy_config"

# Colors for output (if terminal supports it)
if [[ -t 2 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    RED='' GREEN='' YELLOW='' BLUE='' NC=''
fi

# Function to log to Siggy's event stream
log_peppy_event() {
    local topic="$1"
    local message="$2"
    local level="${3:-info}"

    # Log to Siggy if available
    if command -v siggy-log-event >/dev/null 2>&1; then
        siggy-log-event "$topic" "{\"message\": \"$message\", \"source\": \"peppy\", \"level\": \"$level\"}"
    fi

    # Also log to stderr with color
    case "$level" in
        error)   echo -e "${RED}[Peppy] $message${NC}" >&2 ;;
        warning) echo -e "${YELLOW}[Peppy] $message${NC}" >&2 ;;
        success) echo -e "${GREEN}[Peppy] $message${NC}" >&2 ;;
        *)       echo -e "${BLUE}[Peppy]${NC} $message" >&2 ;;
    esac
}

# Function to read config from .siggy.yml
read_siggy_config() {
    local siggy_yml="${PROJECT_ROOT}/.siggy.yml"

    if [[ ! -f "$siggy_yml" ]]; then
        return 1
    fi

    # Try to parse with Python (more reliable for YAML)
    if command -v python3 >/dev/null 2>&1; then
        python3 << 'PYEOF'
import yaml
import os
import sys

try:
    with open('.siggy.yml') as f:
        config = yaml.safe_load(f) or {}

    plugins = config.get('plugins', {})
    peppy = plugins.get('peppy', {})

    # Handle boolean shorthand
    if isinstance(peppy, bool):
        peppy = {'enabled': peppy}

    # Output as shell exports
    print(f"PEPPY_ENABLED={str(peppy.get('enabled', True)).lower()}")
    print(f"PEPPY_AUTO_INDEX={str(peppy.get('auto_index', True)).lower()}")
    print(f"PEPPY_REINDEX_INTERVAL={peppy.get('reindex_interval', 60)}")
    print(f"PEPPY_INDEX_PATH={peppy.get('index_path', '.')}")

except Exception as e:
    print(f"# Error reading config: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
    else
        # Fallback: use grep for simple parsing
        if grep -q "peppy:" "$siggy_yml" 2>/dev/null; then
            if grep -q "enabled: false" "$siggy_yml" 2>/dev/null; then
                echo "PEPPY_ENABLED=false"
            else
                echo "PEPPY_ENABLED=true"
            fi
        fi
    fi
}

# Function to check if Peppy is available
check_peppy_available() {
    # Try to import peppy module
    if python3 -c "import peppy" 2>/dev/null; then
        return 0
    fi

    # Check if peppy command exists
    if command -v peppy >/dev/null 2>&1; then
        return 0
    fi

    return 1
}

# Function to check if index is fresh
is_index_fresh() {
    if [[ ! -f "$INDEX_MARKER" ]]; then
        return 1
    fi

    local last_indexed
    last_indexed=$(stat -c %Y "$INDEX_MARKER" 2>/dev/null || stat -f %m "$INDEX_MARKER" 2>/dev/null || echo 0)
    local current_time
    current_time=$(date +%s)
    local age_seconds=$((current_time - last_indexed))
    local interval_seconds=$((PEPPY_REINDEX_INTERVAL * 60))

    [[ $age_seconds -lt $interval_seconds ]]
}

# Function to get index age in human-readable format
get_index_age() {
    if [[ ! -f "$INDEX_MARKER" ]]; then
        echo "never"
        return
    fi

    local last_indexed
    last_indexed=$(stat -c %Y "$INDEX_MARKER" 2>/dev/null || stat -f %m "$INDEX_MARKER" 2>/dev/null || echo 0)
    local current_time
    current_time=$(date +%s)
    local age_seconds=$((current_time - last_indexed))

    if [[ $age_seconds -lt 60 ]]; then
        echo "${age_seconds}s ago"
    elif [[ $age_seconds -lt 3600 ]]; then
        echo "$((age_seconds / 60))m ago"
    else
        echo "$((age_seconds / 3600))h ago"
    fi
}

# Main function
main() {
    # Load configuration from .siggy.yml
    local config_output
    if config_output=$(read_siggy_config 2>/dev/null); then
        eval "$config_output"
    fi

    # Check if Peppy is enabled
    if [[ "$PEPPY_ENABLED" != "true" ]]; then
        log_peppy_event "peppy.disabled" "Peppy plugin is disabled in .siggy.yml" "info"
        return 0
    fi

    # Check if auto-indexing is enabled
    if [[ "$PEPPY_AUTO_INDEX" != "true" ]]; then
        log_peppy_event "peppy.auto_index.disabled" "Auto-indexing is disabled" "info"
        return 0
    fi

    # Check if Peppy is available
    if ! check_peppy_available; then
        log_peppy_event "peppy.unavailable" "Peppy not installed. Install with: pip install peppy" "warning"
        return 0
    fi

    log_peppy_event "peppy.check" "Checking index status (last indexed: $(get_index_age))"

    # Check if index is fresh
    if is_index_fresh; then
        log_peppy_event "peppy.skip" "Index is fresh ($(get_index_age)), skipping re-index" "success"
        return 0
    fi

    log_peppy_event "peppy.index.start" "Preparing to index: ${PEPPY_INDEX_PATH}"

    # Create cache directory
    mkdir -p "$PEPPY_CACHE_DIR"

    # Write a trigger file that tells the Peppy-enhanced agents to index
    cat > "${PEPPY_CACHE_DIR}/.index_request" << EOF
{
    "requested_at": "$(date -Iseconds)",
    "path": "${PEPPY_INDEX_PATH}",
    "project_root": "${PROJECT_ROOT}",
    "reindex_interval": ${PEPPY_REINDEX_INTERVAL}
}
EOF

    # Update marker (will be updated again after actual indexing)
    touch "$INDEX_MARKER"

    log_peppy_event "peppy.index.ready" "Index request queued - Peppy agents will index on first tool call" "success"

    # Output status for Siggy to capture
    echo "PEPPY_STATUS=ready"
    echo "PEPPY_INDEX_PATH=${PEPPY_INDEX_PATH}"
    echo "PEPPY_PROJECT_ROOT=${PROJECT_ROOT}"

    return 0
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
