#!/bin/bash
# BookSea - Update from GitHub
echo "========================================="
echo "  BookSea - GitHub Update"
echo "========================================="

cd "$(dirname "$0")/.." || exit 1

echo "[1/3] Stashing local changes..."
git stash

echo "[2/3] Pulling latest from GitHub..."
git pull origin main

echo "[3/3] Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Update complete! Run 'python run.py' to start the server."
echo "========================================="
