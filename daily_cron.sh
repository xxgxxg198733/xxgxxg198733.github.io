#!/bin/bash
# Daily blog generation + deploy + commit
# Runs via cron before 6am daily (China time UTC+8)
set -e

PROJECT_DIR="/Users/xiaochaoren/taoli-landing"
LOG_FILE="/tmp/taoli-blog-$(date +%Y%m%d).log"

exec >> "$LOG_FILE" 2>&1
echo "=== $(date '+%Y-%m-%d %H:%M:%S') Daily blog pipeline start ==="

cd "$PROJECT_DIR"

# Step 1: Generate 15 new articles
echo "Running daily_blog.py..."
python3 daily_blog.py

# Only continue if new articles were generated
if git diff --name-only | grep -q "blog/"; then
    echo "New articles detected, deploying..."

    # Step 2: Deploy to production
    vercel --prod --scope xxgxxg198733-8844s-projects --yes

    # Step 3: Add, commit, push
    git add blog/ sitemap.xml images/blog/
    git add -u
    git commit -m "Daily blog update: $(date +%Y-%m-%d) batch [skip ci]"
    git push

    echo "=== $(date '+%Y-%m-%d %H:%M:%S') Pipeline complete ==="
else
    echo "No new articles generated, skipping deploy."
fi
