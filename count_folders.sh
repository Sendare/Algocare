#!/bin/bash
cd ~/Algocare

echo "=== FOLDER FILE COUNTS (top-level and nested) ==="
find . -not -path './.git*' -type d | while read -r dir; do
  count=$(find "$dir" -maxdepth 1 -type f | wc -l)
  echo "$count files -- $dir"
done | sort -rn

echo -e "\n=== TOP-LEVEL FILES (not in any folder) ==="
find . -maxdepth 1 -type f -not -path './.git*'

