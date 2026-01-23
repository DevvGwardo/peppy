#!/bin/bash
# Peppy Session Start Hook for Siggy
# Automatically indexes the codebase when a Siggy workflow starts

set -euo pipefail

# Get the current working directory (project root)
PROJECT_ROOT="${PWD}"

# Check if we should skip indexing (e.g., if recently indexed)
PEPPY_CACHE_DIR="${PROJECT_ROOT}/.peppy_cache"
INDEX_MARKER="${PEPPY_CACHE_DIR}/.last_indexed"

# Function to check if index is fresh (less than 1 hour old)
is_index_fresh() {
    if [[ ! -f "$INDEX_MARKER" ]]; then
        return 1
    fi

    local last_indexed
    last_indexed=$(stat -c %Y "$INDEX_MARKER" 2>/dev/null || stat -f %m "$INDEX_MARKER" 2>/dev/null || echo 0)
    local current_time
    current_time=$(date +%s)
    local age=$((current_time - last_indexed))

    # Fresh if less than 3600 seconds (1 hour) old
    [[ $age -lt 3600 ]]
}

# Function to log to Siggy's event stream
log_peppy_event() {
    local topic="$1"
    local message="$2"

    if command -v siggy-log-event >/dev/null 2>&1; then
        siggy-log-event "$topic" "{\"message\": \"$message\", \"source\": \"peppy\"}"
    else
        echo "[Peppy] $message" >&2
    fi
}

# Main indexing logic
main() {
    log_peppy_event "peppy.check" "Checking if codebase indexing is needed"

    # Skip if index is fresh
    if is_index_fresh; then
        log_peppy_event "peppy.skip" "Index is fresh (< 1 hour old), skipping re-index"
        return 0
    fi

    log_peppy_event "peppy.index.start" "Starting codebase indexing at $PROJECT_ROOT"

    # Trigger Claude Code to index via MCP
    # This assumes Claude Code is already running with Peppy MCP server
    # The actual indexing happens when the Siggy workflow starts and Claude calls Peppy

    # Create marker directory if needed
    mkdir -p "$PEPPY_CACHE_DIR"

    # Update marker
    touch "$INDEX_MARKER"

    log_peppy_event "peppy.index.ready" "Peppy ready for indexing - will trigger on first Siggy agent call"

    return 0
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
