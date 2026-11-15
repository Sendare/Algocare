from pathlib import Path

print("🚀 Fixing absolute paths to relative paths...")

# 1. Fix auth.js (Redirects and Topbar links)
auth_path = Path("assets/auth.js")
src = auth_path.read_text()

# Fix logOut redirect
src = src.replace('window.location.href = "/";', 'window.location.href = (window.APP_ROOT || "") + "index.html";')

# Fix email confirmation redirect
src = src.replace('window.location.href = "/dashboard.html";', 'window.location.href = (window.APP_ROOT || "") + "dashboard.html";')

# Fix Topbar links
src = src.replace('<a href="/dashboard.html"', '<a href="${window.APP_ROOT || \'\'}dashboard.html"')
src = src.replace('<a href="/login.html"', '<a href="${window.APP_ROOT || \'\'}login.html"')

auth_path.write_text(src)
print("✅ Fixed auth.js paths")

# 2. Fix dashboard.js (Card links)
dash_path = Path("assets/dashboard.js")
src = dash_path.read_text()

src = src.replace('linkArticles.href = `/${prog}/index.html`;', 'linkArticles.href = `./${prog}/index.html`;')
src = src.replace('linkPractice.href = `/${prog}/cbt/practice-setup.html`;', 'linkPractice.href = `./${prog}/cbt/practice-setup.html`;')
src = src.replace('linkRealfeel.href = `/${prog}/cbt/exam-setup.html`;', 'linkRealfeel.href = `./${prog}/cbt/exam-setup.html`;')
src = src.replace('linkLeaderboard.href = `/leaderboard.html?prog=${prog}`;', 'linkLeaderboard.href = `./leaderboard.html?prog=${prog}`;')

dash_path.write_text(src)
print("✅ Fixed dashboard.js paths")

# 3. Fix templates/dashboard.html
dash_html = Path("templates/dashboard.html")
src = dash_html.read_text()
src = src.replace('<a href="/dashboard.html"', '<a href="./dashboard.html"')
dash_html.write_text(src)
print("✅ Fixed dashboard.html paths")

# 4. Fix templates/leaderboard.html & assets/leaderboard.js
lb_html = Path("templates/leaderboard.html")
src = lb_html.read_text()
src = src.replace('<a href="./index.html"', '<a href="./index.html"') # Already fine, but checking
lb_html.write_text(src)

lb_js = Path("assets/leaderboard.js")
src = lb_js.read_text()
src = src.replace('window.location.href = "/login.html";', 'window.location.href = "./login.html";')
lb_js.write_text(src)
print("✅ Fixed leaderboard paths")

# 5. Add APP_ROOT variable to build_pages.py
bp = Path("scripts/build.py")
src = bp.read_text()
if "window.APP_ROOT" not in src:
    src = src.replace(
        '<script src="{root_rel}assets/auth.js"></script>',
        '<script>window.APP_ROOT = "{root_rel}";</script>\n<script src="{root_rel}assets/auth.js"></script>'
    )
    bp.write_text(src)
    print("✅ Added APP_ROOT variable to build.py")

print("🎉 All paths fixed.")
