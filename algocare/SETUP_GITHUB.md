# Algocare — GitHub Actions + Cron-job.org Setup Guide

## Step 1: Push Project to GitHub

From Termux, inside your algocare folder:

```bash
git init
git remote add origin https://github.com/YOUR_USERNAME/Algocare.git
git add .
git commit -m "initial: algocare v1"
git branch -M main
git push -u origin main
```

---

## Step 2: Add GitHub Secrets

Go to your repo on GitHub:
**Settings → Secrets and variables → Actions → New repository secret**

Add these 5 secrets one by one:

| Secret Name | Value |
|---|---|
| `GEMINI_API_KEY` | Your Gemini API key |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |
| `FACEBOOK_PAGE_TOKEN` | Your Facebook Page access token |
| `FACEBOOK_PAGE_ID` | Your Facebook Page ID |

---

## Step 3: Create a GitHub Personal Access Token (PAT)

The workflow commits memory updates back to the repo.
It needs write permission.

1. Go to: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click **Generate new token (classic)**
3. Name it: `algocare-actions`
4. Expiration: 90 days (or No expiration)
5. Scopes: check **repo** (full repo access)
6. Click Generate — copy the token immediately

Then add it as a secret:
- Name: `GH_PAT`
- Value: the token you just copied

Now update the workflow to use it — replace this line in `.github/workflows/post.yml`:

```yaml
      - name: Checkout repo
        uses: actions/checkout@v4
```

With:

```yaml
      - name: Checkout repo
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GH_PAT }}
```

Commit and push this change.

---

## Step 4: Test Manual Trigger

1. Go to your repo on GitHub
2. Click **Actions** tab
3. Click **Algocare Auto Post**
4. Click **Run workflow** → **Run workflow**
5. Watch the run — it should complete green
6. Check your Facebook page for the post
7. Check Telegram for the success alert

---

## Step 5: Get Your Webhook URL for Cron-job.org

GitHub allows external services to trigger workflows via the API.

Your webhook URL format:
```
https://api.github.com/repos/YOUR_USERNAME/Algocare/dispatches
```

Replace `YOUR_USERNAME` with your actual GitHub username.

You also need your PAT token (from Step 3) for the request header.

---

## Step 6: Set Up Cron-job.org

1. Go to https://cron-job.org and create a free account
2. Click **Create cronjob**
3. Set these 8 jobs (one per posting time):

For each job:

**URL:**
```
https://api.github.com/repos/YOUR_USERNAME/Algocare/dispatches
```

**Request method:** POST

**Request headers:**
```
Authorization: Bearer YOUR_PAT_TOKEN
Accept: application/vnd.github+json
Content-Type: application/json
```

**Request body:**
```json
{"event_type": "trigger_post"}
```

**Schedule times (GST = UTC+4):**

| Job | Cron-job.org Schedule |
|---|---|
| Post 1 | 06:00 daily |
| Post 2 | 08:30 daily |
| Post 3 | 10:30 daily |
| Post 4 | 12:30 daily |
| Post 5 | 14:30 daily |
| Post 6 | 16:30 daily |
| Post 7 | 18:30 daily |
| Post 8 | 21:00 daily |

4. Enable each job and save.

---

## Step 7: Verify Everything Works

After setting up cron-job.org, wait for the next scheduled time.
You should see:

1. ✅ Cron-job.org shows successful HTTP 204 response
2. ✅ GitHub Actions run completes green
3. ✅ Facebook post appears on your page
4. ✅ Telegram alert: "✅ Posted: ..."
5. ✅ New commit in repo: `auto: post 2026-05-26 08:30`

---

## Updating Facebook Token (every ~60 days)

When your token expires:
1. Get new token from Meta for Developers
2. Go to GitHub → Settings → Secrets → `FACEBOOK_PAGE_TOKEN`
3. Click Update → paste new token → Save
4. Done — no code changes needed

---

## Safe Mode

If 5 consecutive publishes fail, the system pauses automatically.
You will receive a Telegram alert: "SAFE MODE ACTIVATED"

To reset safe mode, edit this file in your repo:
```
config/safe_mode.json
```
Change `consecutive_failures` to `0` and commit.
