#!/bin/bash
#
# Linting Script for File Vault Dedupe Backend
# Author: Jubel Ahmed
#
# Usage:
#   ./lint.sh [check|fix]
#
#   check  - Check code quality without making changes (default)
#   fix    - Auto-fix formatting, imports, and linting issues
#
# This script uses Ruff for formatting, import sorting, and linting,
# and MyPy for type checking.

set -e

# Default to 'check' mode if no argument provided
MODE=${1:-check}

# Validate mode argument
if [ "$MODE" != "check" ] && [ "$MODE" != "fix" ]; then
    echo "❌ Invalid mode: $MODE"
    echo "Usage: ./lint.sh [check|fix]"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "🔍 Running linting tools..."
echo ""

# Ruff - fast linter, formatter, and import sorter (replaces Black + isort)
echo "🚀 Running Ruff (formatting, import sorting, and linting)..."
if [ "$MODE" = "fix" ]; then
    ruff format .
    ruff check --fix .
    echo "✅ Ruff formatting and fixes applied"
else
    ruff format --check . || {
        echo "❌ Ruff found formatting issues. Run './lint.sh fix' to auto-fix"
        exit 1
    }
    ruff check . || {
        echo "❌ Ruff found linting issues. Run './lint.sh fix' to auto-fix"
        exit 1
    }
    echo "✅ Ruff check passed (formatting, imports, and linting)"
fi

# MyPy - type checker (non-blocking)
echo ""
echo "🔬 Running MyPy (type checking)..."
mypy . --ignore-missing-imports || {
    echo "⚠️  MyPy found type issues (non-blocking)"
}
echo "✅ MyPy check completed"

echo ""
echo "✨ All linting checks completed!"

