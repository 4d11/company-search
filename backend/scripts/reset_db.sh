#!/bin/bash
# Quick script to wipe and re-seed the database
# Usage: ./reset_db.sh [--yes|-y]

set -e  # Exit on error

echo "=========================================="
echo "Database Reset Script"
echo "=========================================="

# Change to backend directory
cd "$(dirname "$0")/.."

# Check for --yes flag
YES_FLAG=""
if [[ "$1" == "--yes" ]] || [[ "$1" == "-y" ]]; then
    YES_FLAG="--yes"
fi

# Run wipe script from backend directory
echo ""
echo "Step 1: Wiping databases..."
python -m scripts.wipe_databases $YES_FLAG

# Run seed script
echo ""
echo "Step 2: Seeding databases..."
python -m scripts.seed

echo ""
echo "=========================================="
echo "✓ Database reset complete!"
echo "=========================================="
