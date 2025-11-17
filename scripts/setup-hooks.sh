#!/bin/bash
#
# Setup Git Hooks Script
# Author: Jubel Ahmed
#
# This script installs Git hooks from the scripts/hooks directory
# to .git/hooks so they run automatically on Git events.
#
# Usage: ./scripts/setup-hooks.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOKS_SOURCE="$PROJECT_ROOT/scripts/hooks"
GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "🔧 Setting up Git hooks..."

# Check if .git directory exists
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo "❌ Error: .git directory not found. Are you in a Git repository?"
    exit 1
fi

# Check if hooks source directory exists
if [ ! -d "$HOOKS_SOURCE" ]; then
    echo "❌ Error: hooks directory not found at $HOOKS_SOURCE"
    exit 1
fi

# Create .git/hooks directory if it doesn't exist
mkdir -p "$GIT_HOOKS_DIR"

# Install each hook from scripts/hooks
for hook in "$HOOKS_SOURCE"/*; do
    if [ -f "$hook" ]; then
        hook_name=$(basename "$hook")
        hook_dest="$GIT_HOOKS_DIR/$hook_name"
        
        echo "  Installing $hook_name..."
        cp "$hook" "$hook_dest"
        chmod +x "$hook_dest"
    fi
done

echo "✅ Git hooks installed successfully!"
echo ""
echo "Installed hooks:"
ls -1 "$GIT_HOOKS_DIR"/* 2>/dev/null | xargs -n1 basename | sed 's/^/  - /' || echo "  (none)"
echo ""
echo "Hooks will now run automatically on Git events."

