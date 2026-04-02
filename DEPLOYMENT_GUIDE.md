# W&M Study Suite — Deployment Guide

**Prepared for:** Professor Swan
**Prepared by:** Luke Kovats | kovatsluke@gmail.com
**Estimated setup time:** 30–45 minutes
**Total monthly cost:** ~$12–15/month

---

## What You'll Be Setting Up

This guide walks you through hosting the W&M Strategic Marketing Study Suite online so your students can access it from a permanent link — no installation required on their end. You will need to create two accounts: one for the AI service (Groq) and one for the web hosting (PythonAnywhere). Once complete, share the link with your class and the tool runs itself.

**What you'll have when this is done:**
- A permanent URL your students can bookmark (e.g., `https://professorswan.pythonanywhere.com`)
- An AI-powered study tool that generates quizzes, flashcards, notes, case studies, and practice exams from your course content
- A Groq billing account with optional spending limits so there are no surprise charges
- A working deployment you can reload or update at any time from your browser

---

## Before You Begin — Checklist

Have these ready before starting:

- [ ] The `wm_groq.zip` file (provided by your developer)
- [ ] A W&M email address (used for both account signups)
- [ ] A credit or debit card (required by Groq; PythonAnywhere Developer plan is $10/month)
- [ ] 30–45 minutes of uninterrupted time
- [ ] A plain-text note or password manager to store your API key safely

> **Tip:** Do this on a desktop or laptop computer, not a phone or tablet. The PythonAnywhere interface does not work well on mobile.

---

## Step 1 — Create a Groq Account (AI Service)

Groq powers the AI responses inside the tool. It is a third-party service (not affiliated with W&M) that provides access to large language models via a pay-per-use API.

### 1a. Sign up

1. Open a new browser tab and go to **console.groq.com**
2. Click **Sign Up** and register with your W&M email address
3. Verify your email when the confirmation message arrives

### 1b. Add a payment method

1. Once logged in, click your account icon in the top right → **Settings**
2. Go to the **Billing** tab
3. Click **Add Payment Method** and enter your card details

> **Why a card is required:** Groq charges based on usage (tokens processed). The charges for a single classroom are very low — typically $2–5/month for a class of 30 students using the tool regularly. Adding a card simply enables the service; you will not be charged until students start using it.

### 1c. Set a spending limit (strongly recommended)

1. In the Groq console, go to **Settings → Limits**
2. Set a **Monthly Spend Limit** of $10–15
3. Optionally enable email alerts at 50% and 90% of your limit

> This prevents any scenario where unexpectedly high usage results in a large charge. If the limit is reached, the tool will stop returning AI responses until the next billing cycle — students will see an error message rather than you receiving an unexpected bill.

### 1d. Create an API key

1. In the Groq console, go to **API Keys** (left sidebar)
2. Click **Create API Key**
3. Give it a descriptive name: `WM Study Suite`
4. Click **Create**
5. **Copy the key immediately and save it in a secure note** — it will never be shown again. It starts with `gsk_`

> **Security note:** This key is linked directly to your billing account. Never paste it into an email, a shared Google Doc, a Slack message, or any public forum. If it is ever accidentally exposed, return to the Groq console, delete the key, and create a new one.

---

## Step 2 — Create a PythonAnywhere Account (Web Hosting)

PythonAnywhere hosts the application files and gives you a permanent public URL. It handles the web server so your students can reach the tool from any browser.

### 2a. Sign up

1. Go to **pythonanywhere.com** in a new tab
2. Click **Pricing & Signup**, then **Create a Beginner account** to explore the interface — but note you will upgrade in the next step
3. Choose a username carefully — this becomes your permanent URL. Something professional works best: `professorswan`, `swanwm`, or similar
4. Verify your email address

### 2b. Upgrade to the Developer plan

1. Go to **Account** (top right) → **Upgrade**
2. Select the **Developer plan — $10/month**
3. Complete the payment

> **Why the paid plan is required:** The free PythonAnywhere tier restricts outbound HTTP connections — meaning the app cannot contact the Groq API. The Developer plan removes this restriction. It also gives you more CPU time, which keeps the app responsive during class sessions.

---

## Step 3 — Upload the App Files

### 3a. Upload the zip file

1. From the PythonAnywhere dashboard, click the **Files** tab at the top
2. You will see a file browser showing your home directory (`/home/YOURUSERNAME/`)
3. Click **Upload a file**
4. Select the `wm_groq.zip` file from your computer and wait for the upload to complete (it is a small file — should take under 30 seconds)

### 3b. Extract the files

1. Click the **Consoles** tab → under "Start a new console", click **Bash**
2. A terminal window will open in your browser
3. Type the following command and press **Enter**:
   ```
   unzip wm_groq.zip
   ```
4. You should see a list of files being extracted. When it finishes, type:
   ```
   ls
   ```
   You should see a folder named `wm_groq` listed in the output.

> **If `unzip` fails with "command not found":** Try `python3 -m zipfile -e wm_groq.zip .` instead.

> **If you already have a `wm_groq` folder** from a previous attempt and want to replace it, run `rm -rf wm_groq` before unzipping.

---

## Step 4 — Install Python Dependencies

The app requires a small set of Python packages. These are listed in `requirements.txt` and need to be installed once.

Still in the Bash console from Step 3, type these commands **one at a time**, pressing Enter after each:

```
cd wm_groq
pip3 install -r requirements.txt --user
```

Wait for installation to complete — this typically takes 1–3 minutes. You will see a series of "Downloading..." and "Installing..." lines scroll past.

**Success check:** The last line should say something like:
```
Successfully installed flask-3.1.0 flask-cors-5.0.0 requests-2.32.3 gunicorn-23.0.0 python-dotenv-1.0.1
```

> **If you see any red error lines mentioning permission errors**, remove `--user` from the pip3 command and try again without it, or ask your developer.

> **If a specific package fails to install**, note the package name and contact your developer — it may need a version pin adjustment for PythonAnywhere's environment.

---

## Step 5 — Configure the Web App

### 5a. Create the web app entry

1. Go to the **Web** tab in the PythonAnywhere dashboard
2. Click **Add a new web app**
3. Click **Next** on the domain name screen (your free subdomain is already selected)
4. Select **Manual configuration** (not any of the framework shortcuts)
5. Select the newest Python version available — **Python 3.12** or **Python 3.13** if shown, otherwise the highest number listed. Do not select Python 3.10 — PythonAnywhere no longer offers it on accounts created after March 2025.
6. Click **Next**

You are now on the web app configuration page. You will come back to this page often.

### 5b. Set the source code path

1. Scroll down to the **Code** section
2. In the **Source code** field, enter:
   ```
   /home/YOURUSERNAME/wm_groq
   ```
   Replace `YOURUSERNAME` with your actual PythonAnywhere username (visible in the URL bar and at the top of the dashboard).

### 5c. Edit the WSGI configuration file

The WSGI file tells PythonAnywhere how to start your Flask application.

1. On the same Web tab, scroll to the **Code** section
2. Click the link next to **WSGI configuration file** — it will look like `/var/www/YOURUSERNAME_pythonanywhere_com_wsgi.py`
3. A text editor will open in your browser with some default content
4. **Select all the text and delete it entirely**
5. Paste the following, replacing `YOURUSERNAME` with your username:

```python
import sys
import os

path = '/home/YOURUSERNAME/wm_groq'
if path not in sys.path:
    sys.path.append(path)

os.chdir(path)

from app import app as application
```

6. Click **Save** (top right of the editor)

> **Double-check:** Make sure there are no extra spaces or characters after `YOURUSERNAME` in the path. A typo here is the single most common cause of a failed deployment.

---

## Step 6 — Add Your Groq API Key

The API key must be provided as an environment variable — it is never stored in the code files.

1. Return to the **Web** tab
2. Scroll down to the **Environment variables** section
3. Click **Add a new variable** (or the `+` button depending on your PythonAnywhere version)
4. Enter the following:

   | Name | Value |
   |---|---|
   | `GROQ_API_KEY` | Your key from Step 1 (starts with `gsk_...`) |

5. Click the checkmark or **Save** button to confirm

> **Verification tip:** After saving, the key value is masked (shown as dots). Click the eye icon if available to confirm the value was saved correctly before proceeding.

> **If you need to update this key later** (e.g., you accidentally shared it and need to rotate it), simply delete the old variable here and add the new one, then reload the app (Step 7).

---

## Step 7 — Launch the App

1. Scroll to the top of the **Web** tab
2. Click the large green **Reload** button next to your domain name
3. Wait about 10–15 seconds for the app to restart
4. Click your URL at the top of the page:
   ```
   https://YOURUSERNAME.pythonanywhere.com
   ```

The study tool should load in your browser within a few seconds. Try selecting a topic and generating a flashcard to verify the AI connection is working.

**Share this link with your students. It is permanently live — no action needed on your end to keep it running.**

---

## Verifying Everything Works

Before sharing the link with students, run through this quick checklist:

- [ ] The page loads without an error screen
- [ ] You can see the topic selection interface
- [ ] Clicking a topic and selecting "Flashcards" generates a response from the AI (this confirms the Groq API key is working)
- [ ] Clicking "Quiz" generates a multiple-choice question
- [ ] Visiting `https://YOURUSERNAME.pythonanywhere.com/health` shows `{"status": "ok", ...}` — this is a built-in status check; if it returns an error the app has not started correctly
- [ ] The URL looks correct: `https://YOURUSERNAME.pythonanywhere.com`

If any of these fail, see the Troubleshooting section below before sharing with students.

---

## Ongoing Maintenance

Once deployed, the tool requires minimal ongoing attention.

| Task | Frequency | How |
|---|---|---|
| Check Groq usage/billing | Monthly | Log in to console.groq.com → **Usage** tab. Compare against your spend limit. |
| Review Groq billing charges | Monthly | console.groq.com → **Billing** → **Invoices** |
| Reload after unexpected outage | As needed | PythonAnywhere **Web** tab → green **Reload** button |
| Update course content | As needed | Contact your developer — requires editing `static/index.html` and re-uploading |
| Rotate API key | If key is ever exposed | Groq console → delete old key → create new key → update environment variable in PythonAnywhere |

### PythonAnywhere free time allocation

PythonAnywhere Developer accounts include a monthly CPU time allocation. For a study tool with a class of 30 students, you are very unlikely to approach this limit. If you ever receive an email warning about CPU usage, contact your developer.

---

## Troubleshooting

### Students see a generic error page or "Something went wrong"

1. Go to the **Web** tab on PythonAnywhere
2. Scroll down and click **Error log**
3. The most recent error will be at the bottom of the file
4. Common causes:
   - **API key entered incorrectly** (missing characters, extra space): Go back to Step 6 and re-enter the key carefully
   - **WSGI file has a typo** in the path: Re-check Step 5c
   - **App needs a reload**: Click the Reload button on the Web tab

### The page loads but AI responses don't work (spinner keeps spinning)

- The Groq API key may be missing or incorrect — re-check Step 6
- Your Groq account may have hit a rate limit or spending cap — log in to console.groq.com and check **Usage**
- The Groq service may be experiencing downtime — check **status.groq.com** for any active incidents
- If the spinner runs for exactly 2 minutes then stops, the request timed out — this is rarely a configuration issue and usually means Groq is slow; try again in a few minutes

### "Internal Server Error" on every page load

- Open the **Error log** (Web tab → Error log link)
- If you see `ModuleNotFoundError`, a Python package didn't install correctly — return to Step 4 and re-run the pip3 command
- If you see `No module named 'app'`, the WSGI file path is wrong — re-check Step 5c

### AI responses stop working mid-semester

- Log in to console.groq.com and check your **monthly usage** — you may have reached your spend limit
- If you hit the limit before month-end more than once, consider raising it slightly or reminding students to close the tool when not actively using it

### The app was working but now shows a "502 Bad Gateway"

This typically means the web app process crashed. Go to the **Web** tab and click **Reload**. If it continues happening frequently, open the error log and share the contents with your developer.

### Forgot the URL

It is always: `https://YOURUSERNAME.pythonanywhere.com`
Your username is visible at the top of any PythonAnywhere page when logged in.

### You need to update the app (new version from developer)

1. Upload the new `wm_groq.zip` to PythonAnywhere (Files tab)
2. Open a Bash console and run:
   ```
   rm -rf wm_groq
   unzip wm_groq.zip
   cd wm_groq
   pip3 install -r requirements.txt --user
   ```
3. Go to the Web tab and click **Reload**
4. Your environment variables (API key) are preserved — you do not need to re-enter them

---

## Security Notes

- **Your Groq API key is equivalent to a credit card** for AI usage. Keep it private.
- PythonAnywhere stores it encrypted in their environment variable system — it is not visible in your code files or accessible to students.
- Students interact with the AI through your Flask backend — they never see the API key.
- No student data (names, emails, quiz scores) is stored on any server. Progress is stored only in each student's own browser.
- If a student clears their browser cache or switches computers, their progress resets — this is expected behavior in v1.0.

---

## Cost Summary

| Service | Plan | Monthly Cost |
|---|---|---|
| PythonAnywhere | Developer | $10.00 |
| Groq API | Pay-per-use | ~$2–5 (class of 30, typical usage) |
| **Total** | | **~$12–15/month** |

Groq charges are based on tokens (roughly, words) processed. Current rates (as of 2026):

| Model | Used for | Input | Output |
|---|---|---|---|
| `llama-3.1-8b-instant` | Flashcards, quizzes, notes, AI feedback | $0.05 / 1M tokens | $0.08 / 1M tokens |
| `llama-3.3-70b-versatile` | Case studies, practice exams | $0.59 / 1M tokens | $0.79 / 1M tokens |

A single quiz generation typically uses ~3,000 tokens total — about $0.00025 at 8b rates. Even with 30 students each running 50 sessions per month, the total cost stays well under $5. The biggest cost variable is the Practice Exam mode, which sends the most tokens per request (multi-module combined prompts).

The $2–5/month estimate assumes typical classroom use. If students run practice exams repeatedly across many modules, costs can trend toward the higher end.

Verify current rates at **groq.com/pricing** before the semester starts.

---

*Guide prepared by: Luke Kovats — for questions during setup, contact kovatsluke@gmail.com*
