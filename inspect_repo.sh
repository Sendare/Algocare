cd ~/Algocare  # adjust path if different

echo "=== CURRENT BRANCH ==="
git branch --show-current

echo -e "\n=== ALL BRANCHES (local + remote) ==="
git branch -a

echo -e "\n=== GIT REMOTE ==="
git remote -v

echo -e "\n=== FULL FILE TREE (including hidden files) ==="
find . -not -path './.git/*' | sort

echo -e "\n=== .gitignore CONTENTS ==="
cat .gitignore 2>/dev/null || echo "(no .gitignore found)"

echo -e "\n=== GIT STATUS ==="
git status

echo -e "\n=== LAST 10 COMMITS ==="
git log --oneline -10

