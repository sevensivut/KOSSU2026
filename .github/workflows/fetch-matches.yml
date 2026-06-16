name: Update Match Data

on:
  schedule:
    - cron: '*/2 * * * *'
  workflow_dispatch:
  push:
    branches:
      - main

permissions:
  contents: write

jobs:
  update-data:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install requests

      - name: Run script
        env:
          RAPIDAPI_KEY: ${{ secrets.RAPIDAPI_KEY }}
        run: |
          python scripts/fetch_matches.py

      - name: Commit and push
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git stash --include-untracked
          git pull origin main --no-rebase
          git stash pop || true
          git add -f data/matches.json
          if git diff --staged --quiet; then
            echo "No changes to commit"
          else
            git commit -m "Update data $(date -u +'%Y-%m-%d %H:%M:%S')"
            git push origin main
          fi
