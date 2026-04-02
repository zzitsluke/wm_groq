# W&M Study Suite — Development Roadmap

**Prepared for:** Professor Swan
**Prepared by:** Luke Kovats | kovatsluke@gmail.com
**Current version:** v1.0 — single-course, localStorage-based study tool hosted on PythonAnywhere

---

## Overview

This document outlines three phases of future development, progressing from optional student accounts to full institutional integration. Each phase builds on the last. The intent is to give any developer you bring on a clear picture of the architecture, recommended tools, and implementation steps so they can pick up where v1.0 left off without starting from scratch.

The current stack is:
- **Backend:** Python / Flask (`app.py`)
- **Frontend:** Single HTML file (`static/index.html`)
- **AI:** Groq API (LLM proxy, `llama-3.3-70b-versatile` and `llama-3.1-8b-instant`)
- **Hosting:** PythonAnywhere (Developer plan)
- **Progress storage:** Browser `localStorage` — no server-side database in v1.0

All three phases can be built on top of this foundation without replacing it. The Flask backend and single-file frontend are intentionally simple, which makes them easy to extend incrementally.

---

## Known Limitations of v1.0

Before reading the roadmap, it helps to understand what v1.0 deliberately does not do and why:

| Limitation | Why It Exists | Phase That Addresses It |
|---|---|---|
| Progress lost if student clears cache or switches devices | No database; localStorage only | Phase 1 |
| No instructor visibility into student engagement | No data layer | Phase 2 |
| Students must navigate to an external URL | Not integrated with Canvas | Phase 3 |
| Only one course supported | Content is hardcoded in `index.html` | Phase 3 |
| No server-side rate limiting | Added complexity not needed for a pilot | Pre-Phase 1 quick-win (see Next Steps) |
| No automated content updates | Requires developer to edit HTML | Phase 3 |

---

## Phase 1 — Student Accounts & Cross-Device Progress

### What this unlocks

Students can log in and have their progress (studied modules, mastery scores, pinned content, streaks) follow them across devices and browsers. Currently all of this lives in the browser's `localStorage` and is lost if a student clears their cache or uses a different device.

This phase also sets up the data layer that Phases 2 and 3 depend on. Even if you never implement Phase 2, Phase 1's database infrastructure is worth having as enrollment scales.

### Why Supabase

**Supabase** is a hosted database service with built-in user authentication. It is the lowest-friction path to adding accounts to this app because:
- Free tier supports up to 50,000 monthly active users and 500MB database storage
- Provides auth (email/password, magic link, Google OAuth) out of the box
- JavaScript SDK can be dropped directly into `index.html` — no major restructuring needed
- No server management required — the database is hosted and maintained by Supabase
- Row-level security policies enforce that students can only read/write their own progress rows

> **Critical limitation of the free tier:** Supabase automatically pauses free projects after **7 days of inactivity** (no API calls or database queries). During an active semester this is never an issue, but over winter break or summer break the project will be paused and students will get errors on first login after the break. You would need to manually log in to Supabase and click **Restore** before the semester resumes.
>
> **Recommendation:** Use the free tier to build and test Phase 1. Before the first full semester goes live, upgrade to the **Supabase Pro plan ($25/month)** — it removes the inactivity pause entirely and adds daily backups. This raises the total monthly cost to ~$35–40/month but is the right call for a production classroom tool.

**Alternative considered:** Firebase (Google). Supabase is preferred here because it uses standard PostgreSQL (familiar to most developers), has a cleaner JavaScript SDK, and keeps data in a format that is easy to export if you ever migrate away.

---

### Implementation Steps

#### Step 1 — Create a Supabase project

1. Go to **supabase.com** and create a new organization and project
2. Choose a region close to your students (e.g., US East)
3. Save the database password somewhere secure — you may need it for direct DB access later

Create the following tables using the **Table Editor** in the Supabase dashboard:

**`profiles` table** — one row per student
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | primary key, references `auth.users.id` |
| `email` | text | student's W&M email |
| `display_name` | text | optional; can be set by student |
| `created_at` | timestamp with time zone | auto-set on insert |

**`progress` table** — one row per student, upserted on each session
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | primary key |
| `user_id` | uuid | foreign key → `profiles.id`; unique constraint |
| `studied_topics` | jsonb | array of studied module names |
| `mastery` | jsonb | object: `{ "Topic Name": 85, ... }` |
| `pinned_items` | jsonb | array of pinned content objects |
| `streak` | integer | current day-streak count |
| `sessions` | integer | total session count |
| `last_visit` | text | ISO date string of last visit |
| `updated_at` | timestamp with time zone | updated on every upsert |

**Row-level security policies to add:**
```sql
-- Students can only read their own progress
CREATE POLICY "Users read own progress" ON progress
  FOR SELECT USING (auth.uid() = user_id);

-- Students can only write their own progress
CREATE POLICY "Users write own progress" ON progress
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users update own progress" ON progress
  FOR UPDATE USING (auth.uid() = user_id);
```

Enable RLS on both tables: **Table Editor → progress → RLS → Enable**.

4. In Supabase → **Settings → API**, copy:
   - **Project URL** (looks like `https://abcdefgh.supabase.co`)
   - **anon public key** (safe to embed in frontend JavaScript)

---

#### Step 2 — Add the Supabase SDK to the frontend

At the top of `static/index.html`, inside the `<head>` tag, add:

```html
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script>
  const SUPABASE_URL = 'https://your-project.supabase.co';
  const SUPABASE_KEY = 'your-anon-public-key';
  const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
</script>
```

The anon key is safe to expose in frontend code — Supabase's row-level security policies (set up in Step 1) enforce that users can only access their own data even with this key.

---

#### Step 3 — Add a login/signup modal

Add a modal that appears on first load if no active session is found. **Guest mode should remain available** — students who don't want to log in continue using the tool with localStorage as today.

```javascript
async function checkSession() {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    document.getElementById('loginModal').style.display = 'flex';
  } else {
    await loadProgressFromDB(session.user.id);
  }
}

async function signIn(email, password) {
  const { data, error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) {
    showToast('Sign-in failed: ' + error.message);
  } else {
    document.getElementById('loginModal').style.display = 'none';
    await loadProgressFromDB(data.user.id);
  }
}

async function signUp(email, password) {
  const { error } = await supabase.auth.signUp({ email, password });
  if (error) {
    showToast('Sign-up failed: ' + error.message);
  } else {
    showToast('Check your email to confirm your account before signing in.');
  }
}

function continueAsGuest() {
  document.getElementById('loginModal').style.display = 'none';
  // Progress continues to use localStorage as in v1.0
}
```

**Email domain restriction (recommended):** To limit sign-ups to W&M students, you can add a check before calling `signUp`:
```javascript
if (!email.endsWith('@wm.edu') && !email.endsWith('@email.wm.edu')) {
  showToast('Please use your W&M email address.');
  return;
}
```

---

#### Step 4 — Sync progress to and from the database

Replace the current `localStorage` reads and writes with functions that sync to Supabase when a user is logged in, and fall back to `localStorage` for guests:

```javascript
async function loadProgressFromDB(userId) {
  const { data, error } = await supabase
    .from('progress')
    .select('*')
    .eq('user_id', userId)
    .single();

  if (data) {
    studiedTopics = new Set(data.studied_topics || []);
    topicMastery  = data.mastery || {};
    pinnedItems   = data.pinned_items || [];
    streak        = data.streak || 0;
    sessions      = data.sessions || 0;   // matches frontend variable name
    // Note: wm_lastTopic and wm_lastMode (last-session restore) stay in localStorage —
    // they are UI state, not progress data, and don't need cloud sync
    updateStreakDisplay();
    renderTopics();
  } else if (error && error.code !== 'PGRST116') {
    // PGRST116 = no rows found (new user), which is fine
    console.warn('Error loading progress:', error.message);
  }
}

async function saveProgressToDB() {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    // Guest mode — use localStorage as before
    localStorage.setItem('wm_studied', JSON.stringify([...studiedTopics]));
    localStorage.setItem('wm_mastery', JSON.stringify(topicMastery));
    localStorage.setItem('wm_pinned', JSON.stringify(pinnedItems));
    return;
  }

  const { error } = await supabase.from('progress').upsert({
    user_id:        user.id,
    studied_topics: [...studiedTopics],
    mastery:        topicMastery,
    pinned_items:   pinnedItems,
    streak:         streak,
    sessions:       sessions,
    last_visit:     new Date().toISOString().split('T')[0],
    updated_at:     new Date().toISOString()
  }, { onConflict: 'user_id' });

  if (error) console.warn('Error saving progress:', error.message);
}
```

Call `saveProgressToDB()` anywhere `localStorage.setItem` is currently called. The upsert ensures that a student's row is created on first save and updated on every subsequent save.

---

#### Phase 1 — Testing checklist before going live

- [ ] New student can sign up and receives a confirmation email
- [ ] After confirming email, student can sign in
- [ ] Progress saved in one browser session appears when logging in from a different browser
- [ ] Guest mode still works — progress stores in localStorage and tool functions normally
- [ ] Signing out clears the session (call `supabase.auth.signOut()`)
- [ ] Row-level security: one student cannot read another student's progress row (test via Supabase dashboard → SQL Editor)

---

#### Estimated developer effort
2–4 days for a developer familiar with JavaScript and REST APIs.

#### Cost impact
Supabase free tier covers this use case entirely. No additional monthly cost.

---

## Phase 2 — Instructor Analytics Dashboard

### What this unlocks

A separate instructor-facing view at `/instructor` showing class-wide engagement: which modules students are studying most, per-topic mastery scores aggregated across all students, time-of-day usage patterns, and automated email alerts for modules where the class average falls below a threshold.

**Phase 1 must be complete before Phase 2.** The analytics layer requires the Supabase database set up in Phase 1 — there is no student data to analyze without it.

---

### Architecture overview

The cleanest implementation is a separate password-protected route (`/instructor`) served by the existing Flask app, pulling aggregated data from Supabase via their Python SDK. A separate static HTML page (`instructor.html`) handles the frontend visualization. No new hosting infrastructure is needed.

```
/instructor  (GET, POST)
    └─▶ Flask checks session["instructor"] == True
    └─▶ If not authenticated, serve instructor_login.html
    └─▶ If authenticated, serve instructor.html

/instructor/data  (GET, requires instructor session)
    └─▶ Flask queries Supabase using service-role key
    └─▶ Returns aggregated progress JSON
    └─▶ instructor.html renders charts from this data
```

---

### Implementation Steps

#### Step 1 — Install the Supabase Python SDK on PythonAnywhere

In the PythonAnywhere Bash console:
```
pip3 install supabase==2.10.0 --user
```

Add to `requirements.txt` (pin to an exact version to prevent breaking changes on future deploys):
```
supabase==2.10.0
```

> Always pin to a real version number. Running `pip3 install supabase` without a version pin will install whatever is current at deployment time, which may introduce incompatibilities later.

---

#### Step 2 — Add environment variables

In PythonAnywhere **Web tab → Environment Variables**, add:

| Variable | Value |
|---|---|
| `INSTRUCTOR_PASSWORD` | A strong password you choose (15+ characters recommended) |
| `SUPABASE_URL` | Your Supabase project URL (`https://your-project.supabase.co`) |
| `SUPABASE_SERVICE_KEY` | Your Supabase **service role key** (not the anon key) |
| `SECRET_KEY` | A long random string (used by Flask for session signing) |

> **Service role key vs. anon key:** The service role key bypasses row-level security and can read all student rows — which is what the instructor dashboard needs. It must never be sent to or used in frontend JavaScript. Keep it exclusively in backend environment variables.

To generate a good `SECRET_KEY` from the PythonAnywhere Bash console:
```
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

#### Step 3 — Add the `/instructor` route to `app.py`

```python
from supabase import create_client, Client
from flask import session, redirect, request, jsonify, send_from_directory
import os

# Initialize Supabase client (add near the top of app.py, after other imports)
supabase_admin: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_KEY")
)

app.secret_key = os.environ.get("SECRET_KEY")


@app.route("/instructor", methods=["GET", "POST"])
def instructor():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == os.environ.get("INSTRUCTOR_PASSWORD"):
            session["instructor"] = True
            return redirect("/instructor")
        # Wrong password — return to login with error flag
        return send_from_directory("static", "instructor_login.html"), 401

    if not session.get("instructor"):
        return send_from_directory("static", "instructor_login.html")

    return send_from_directory("static", "instructor.html")


@app.route("/instructor/data")
def instructor_data():
    if not session.get("instructor"):
        return jsonify({"error": "Unauthorized"}), 401

    result = supabase_admin.table("progress").select("*").execute()
    return jsonify(result.data)


@app.route("/instructor/logout")
def instructor_logout():
    session.pop("instructor", None)
    return redirect("/instructor")
```

---

#### Step 4 — Build the dashboard frontend (`static/instructor.html`)

The instructor dashboard is a self-contained HTML page. It fetches `/instructor/data` on load and renders three views:

**Module engagement bar chart** — how many students have studied each module:
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
async function loadDashboard() {
  const res = await fetch('/instructor/data');
  if (!res.ok) { window.location = '/instructor'; return; }
  const students = await res.json();

  // Count how many students studied each topic
  const topicCounts = {};
  const topicScores = {};

  students.forEach(s => {
    (s.studied_topics || []).forEach(topic => {
      topicCounts[topic] = (topicCounts[topic] || 0) + 1;
    });
    Object.entries(s.mastery || {}).forEach(([topic, score]) => {
      if (!topicScores[topic]) topicScores[topic] = [];
      topicScores[topic].push(score);
    });
  });

  // Average mastery per topic
  const avgMastery = Object.fromEntries(
    Object.entries(topicScores).map(([t, scores]) => [
      t, Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
    ])
  );

  // Identify weak topics (class average below 70%)
  const weakTopics = Object.entries(avgMastery)
    .filter(([, avg]) => avg < 70)
    .sort(([, a], [, b]) => a - b);

  renderEngagementChart(topicCounts, students.length);
  renderMasteryChart(avgMastery);
  renderWeakTopicAlerts(weakTopics);
  renderSummaryStats(students);
}
</script>
```

**Summary stats block** — total enrolled students, average session count, average streak:
```javascript
function renderSummaryStats(students) {
  const totalStudents = students.length;
  const avgSessions = students.reduce((s, u) => s + (u.sessions || 0), 0) / totalStudents;
  const avgStreak = students.reduce((s, u) => s + (u.streak || 0), 0) / totalStudents;

  document.getElementById('stat-students').textContent = totalStudents;
  document.getElementById('stat-sessions').textContent = avgSessions.toFixed(1);
  document.getElementById('stat-streak').textContent = avgStreak.toFixed(1);
}
```

**Weak topic alerts** — rendered as a simple HTML list below the charts:
```javascript
function renderWeakTopicAlerts(weakTopics) {
  const list = document.getElementById('weak-topics');
  if (weakTopics.length === 0) {
    list.innerHTML = '<p style="color: green;">No topics below 70% — class is on track.</p>';
    return;
  }
  list.innerHTML = weakTopics.map(([topic, avg]) =>
    `<div class="alert">⚠️ <strong>${topic}</strong> — class average: ${avg}%</div>`
  ).join('');
}
```

---

#### Step 5 — Automated weak-topic email alerts (optional)

Use **SendGrid** (free tier: 100 emails/day) to email the instructor when a module's class average drops below a configurable threshold. This can be triggered from a Flask route called periodically via a PythonAnywhere scheduled task.

Install the SendGrid library:
```
pip3 install sendgrid --user
```

Add to `requirements.txt`:
```
sendgrid==6.11.0
```

Add to environment variables:
```
SENDGRID_API_KEY=your-sendgrid-key
ALERT_EMAIL=professor@wm.edu
ALERT_THRESHOLD=70
```

Scheduled task function in `app.py` or a separate `tasks.py`:
```python
import sendgrid
from sendgrid.helpers.mail import Mail

def check_and_alert():
    result = supabase_admin.table("progress").select("mastery").execute()
    topic_scores = {}
    for row in result.data:
        for topic, score in (row.get("mastery") or {}).items():
            topic_scores.setdefault(topic, []).append(score)

    threshold = int(os.environ.get("ALERT_THRESHOLD", 70))
    weak = {t: sum(s)/len(s) for t, s in topic_scores.items() if sum(s)/len(s) < threshold}

    if not weak:
        return

    body = "The following modules have class averages below {}%:\n\n".format(threshold)
    for topic, avg in sorted(weak.items(), key=lambda x: x[1]):
        body += f"  • {topic}: {avg:.0f}%\n"

    sg = sendgrid.SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
    message = Mail(
        from_email="alerts@yourdomain.com",
        to_emails=os.environ.get("ALERT_EMAIL"),
        subject="W&M Study Suite — Low Mastery Alert",
        plain_text_content=body
    )
    sg.send(message)
```

To schedule this to run weekly: in PythonAnywhere, go to **Tasks** tab → **Add a new scheduled task** → set it to run the script once a week.

---

#### Phase 2 — Testing checklist before going live

- [ ] `/instructor` with the wrong password returns a 401 and does not show data
- [ ] `/instructor` with the correct password shows the dashboard
- [ ] `/instructor/data` without an active instructor session returns 401 (test by opening it in a fresh incognito tab)
- [ ] Dashboard loads without errors when there is student data in Supabase
- [ ] Dashboard renders a meaningful "no data yet" state when the `progress` table is empty
- [ ] Logging out via `/instructor/logout` clears the session and redirects to the login form

---

#### Estimated developer effort
4–7 days for a developer familiar with Python, Flask, and JavaScript charting libraries.

#### Cost impact
SendGrid free tier (100 emails/day) is sufficient. No additional monthly infrastructure cost for this phase.

---

## Phase 3 — Institutional Scale: LMS Integration & Multi-Course

### What this unlocks

The tool integrates directly into Canvas or Blackboard as a launchable module (no separate URL students need to remember), expands to support multiple Mason courses, and gives instructors a self-service content editor so they can update module material without developer involvement.

---

### Part A — LMS Integration (Canvas / Blackboard)

LMS tools communicate via a standard called **LTI 1.3** (Learning Tools Interoperability). When a student clicks the tool inside Canvas, Canvas sends a cryptographically signed token to your Flask app identifying the student — no separate login required. The student is automatically signed in and taken directly to the study tool.

#### How LTI 1.3 works (high level)

```
Student clicks tool in Canvas
    └─▶ Canvas sends signed OIDC login request to /lti/login
    └─▶ Flask validates and redirects back to Canvas
    └─▶ Canvas sends signed launch token to /lti/launch
    └─▶ Flask decodes token, extracts student email/ID
    └─▶ Flask creates or updates Supabase user, sets session
    └─▶ Student is redirected to the study tool, already logged in
```

#### Recommended library: `PyLTI1p3`

> **Maintenance note:** PyLTI1p3's last release was version 2.0.0 in November 2022. The package works and is widely used in production LTI deployments, but it has not been actively updated in several years. Before starting Phase 3, have your developer verify the package is still installable and compatible with the Python version on PythonAnywhere or your chosen host. If it has become unmaintained by the time Phase 3 begins, `lti1p3platform` is an alternative to evaluate.

The LTI adapter also requires `flask-caching` to store OIDC launch state between redirects — install both:

```
pip3 install PyLTI1p3==2.0.0 Flask-Caching==2.3.0 --user
```

Add both to `requirements.txt`:
```
PyLTI1p3==2.0.0
Flask-Caching==2.3.0
```

#### What requires W&M IT involvement

LTI 1.3 uses public/private key pairs for request signing. Registering your tool requires:
1. Providing W&M IT / Canvas administrators with your tool's **OIDC login URL** and **launch URL**
2. Receiving a **client ID** and **platform deployment ID** from Canvas
3. Exchanging public keys (your app signs requests with its private key; Canvas verifies with your public key, and vice versa)

**This step cannot be done by the professor alone.** Contact the Canvas support team at W&M to initiate the LTI tool registration process. Allow 1–4 weeks for IT to process the request, depending on current backlog.

#### LTI configuration file (`lti_config.json`)

```json
{
    "https://canvas.wm.edu": [{
        "default": true,
        "client_id": "your-canvas-client-id",
        "auth_login_url": "https://canvas.wm.edu/api/lti/authorize_redirect",
        "auth_token_url": "https://canvas.wm.edu/login/oauth2/token",
        "key_set_url": "https://canvas.wm.edu/api/lti/security/jwks",
        "key_set": null,
        "deployment_ids": ["your-deployment-id"]
    }]
}
```

#### Flask LTI routes

```python
from pylti1p3.flask_adapter import FlaskOIDCLogin, FlaskMessageLaunch, FlaskRequest, FlaskCacheDataStorage
from pylti1p3.tool_config import ToolConfJsonFile
from flask_caching import Cache

cache = Cache(app, config={"CACHE_TYPE": "SimpleCache"})

@app.route('/lti/login', methods=['GET', 'POST'])
def lti_login():
    tool_conf = ToolConfJsonFile('lti_config.json')
    launch_data_storage = FlaskCacheDataStorage(cache)
    flask_request = FlaskRequest()
    target_link_uri = flask_request.get_param('target_link_uri')
    if not target_link_uri:
        return "Missing target_link_uri", 400
    oidc_login = FlaskOIDCLogin(flask_request, tool_conf, launch_data_storage=launch_data_storage)
    return oidc_login.enable_check_cookies().redirect(target_link_uri)

@app.route('/lti/launch', methods=['POST'])
def lti_launch():
    tool_conf = ToolConfJsonFile('lti_config.json')
    launch_data_storage = FlaskCacheDataStorage(cache)
    message_launch = FlaskMessageLaunch(FlaskRequest(), tool_conf, launch_data_storage=launch_data_storage)
    launch_data = message_launch.get_launch_data()

    student_email = launch_data.get('email')
    student_name = launch_data.get('name', '')
    course_id = launch_data.get('https://purl.imsglobal.org/spec/lti/claim/context', {}).get('id')

    # Create or sign in the Supabase user for this student
    # Then set a server-side session and redirect to the study tool
    session['user_email'] = student_email
    session['course_id'] = course_id
    return redirect('/')
```

Full LTI 1.3 integration is the most technically complex step in this roadmap. Budget significant developer time and plan for multiple rounds of back-and-forth with W&M IT. Do not underestimate the coordination overhead.

---

### Part B — Multi-Course Architecture

Currently, all course content lives in a single `COURSE_MATERIALS` object in `index.html`. Expanding to multiple courses requires moving content to the database and giving each instructor a way to manage it independently.

#### Step 1 — Add a `courses` table to Supabase

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | primary key |
| `name` | text | e.g., "Strategic Marketing MBA" |
| `course_code` | text | e.g., "MKTG 501" — used as a URL slug |
| `instructor_id` | uuid | links to the instructor's Supabase user |
| `modules` | jsonb | the `COURSE_MATERIALS` object for this course |
| `is_active` | boolean | allows disabling a course without deleting it |
| `created_at` | timestamp with time zone | |
| `updated_at` | timestamp with time zone | |

#### Step 2 — Load course content dynamically

Add a Flask route that returns course content by ID:

```python
@app.route('/api/course/<course_id>')
def get_course(course_id):
    result = supabase_admin.table("courses") \
        .select("modules, name") \
        .eq("id", course_id) \
        .eq("is_active", True) \
        .single() \
        .execute()
    if result.data:
        return jsonify(result.data)
    return jsonify({"error": "Course not found"}), 404
```

In `index.html`, replace the hardcoded `COURSE_MATERIALS` initialization with a dynamic fetch:

```javascript
async function loadCourse(courseId) {
  const res = await fetch(`/api/course/${courseId}`);
  if (!res.ok) {
    showToast('Could not load course content. Please refresh.');
    return;
  }
  const data = await res.json();
  COURSE_MATERIALS = data.modules;
  document.title = data.name + ' — Study Suite';
  renderTopics();
}
```

The course ID can be passed as a URL parameter (`?course=uuid`) or derived from the LTI launch context in Part A.

#### Step 3 — Instructor content editor

Add a simple editor at `/instructor/content` where instructors can update module text without touching code. This eliminates the need to contact a developer every time course content changes.

The editor can be a textarea pre-filled with the current `modules` JSON, with a Save button that POSTs back to a Flask route:

```python
@app.route("/instructor/content", methods=["GET", "POST"])
def instructor_content():
    if not session.get("instructor"):
        return redirect("/instructor")

    if request.method == "POST":
        new_modules = request.json.get("modules")
        course_id = request.json.get("course_id")
        supabase_admin.table("courses").update({"modules": new_modules}).eq("id", course_id).execute()
        return jsonify({"status": "saved"})

    # GET: return current course content for editing
    result = supabase_admin.table("courses").select("*").execute()
    return jsonify(result.data)
```

A JSON editor library like **JSONEditor** (free, CDN-available) provides a structured editing UI that is much less error-prone than a raw textarea.

---

### Part C — Scaling Hosting Beyond PythonAnywhere

At institutional scale (multiple courses, many concurrent users, LTI traffic), PythonAnywhere's WSGI setup (3 web workers on the Developer plan) will become a bottleneck. Note that PythonAnywhere uses its own WSGI server — the `Procfile` in the repo (`gunicorn app:app --workers 2`) is only used when deploying to Render or Railway, not on PythonAnywhere. Consider migrating to:

| Option | Cost | Migration Effort | Notes |
|---|---|---|---|
| **Render** | $7/month (Starter) | Low — uses existing `Procfile` | Easy migration, auto-deploy from GitHub, supports environment variables |
| **Railway** | ~$5–10/month | Low | Similar to Render; good free tier for testing |
| **W&M university servers** | $0 (institutional) | High — requires IT coordination | Proper `wm.edu` subdomain, no third-party cost, but slower to provision |
| **AWS / GCP** | Variable | High | Overkill for this scale; only consider if W&M IT has existing cloud contracts |

The existing `Procfile` in the repo (`web: gunicorn app:app`) is already configured for deployment on Render or Railway — migration is largely a matter of pointing environment variables at the new host.

---

### Phase 3 — Risk Considerations

| Risk | Likelihood | Mitigation |
|---|---|---|
| W&M IT delays LTI registration | High | Start outreach early; LTI is not on a tight timeline for Phase 3 |
| Canvas LTI config errors cause broken launches | Medium | Test with a staging Canvas course before enabling for a live class |
| Content editor allows instructor to corrupt module JSON | Medium | Validate the JSON structure server-side before saving to Supabase |
| Multi-course rollout exposes one course's content to another's students | Low | Row-level security + course ID validation in every API route |

---

### Estimated developer effort

Phase 3 is a multi-week engagement. LTI integration alone typically takes 1–2 weeks including IT coordination. Multi-course architecture is another 1–2 weeks. The content editor is an additional 3–5 days. Budget for a developer with Flask and JavaScript experience, and loop in W&M IT as early as possible — their timeline often drives the overall schedule more than development time does.

---

## Summary

| Phase | Key Features | Prerequisite | Est. Dev Time | Additional Monthly Cost |
|---|---|---|---|---|
| **1** | Student accounts, cross-device sync, guest mode | None (builds on v1.0) | 2–4 days | $0 dev/test (Supabase free); +$25/mo for production (Supabase Pro — avoids inactivity pausing) |
| **2** | Instructor dashboard, mastery charts, email alerts | Phase 1 | 4–7 days | $0 (SendGrid free tier) |
| **3** | LMS integration, multi-course, content editor, hosting migration | Phase 1 + W&M IT | 3–5 weeks | $7–25/month depending on hosting choice |

---

## Recommended Next Steps

1. **If starting Phase 1:** Create the Supabase project first — free tier is fine for development and testing. Before going live with a full class, upgrade to Supabase Pro ($25/month) to prevent the database from pausing over semester breaks. The developer can start building against the free project immediately and upgrade when ready to launch.

2. **If planning Phase 3:** Contact W&M IT / Canvas administrators now, even if Phase 1 hasn't started. LTI registration timelines are outside your control and should not be the last thing on the critical path.

3. **Before engaging a new developer:** Reach out to Luke Kovats (kovatsluke@gmail.com) first for a context handoff. The codebase has intentional design decisions (single-file frontend, Anthropic response format, prompt engineering choices) that are faster to explain than to rediscover.

4. **Rate limiting (quick win for v1.0):** Before any phase work begins, consider adding basic rate limiting to `app.py` using Flask-Limiter. This prevents a single student or a runaway client from exhausting your Groq API quota during a class session and requires less than an hour of developer time:
   ```
   pip3 install Flask-Limiter
   ```
   ```python
   from flask_limiter import Limiter
   from flask_limiter.util import get_remote_address
   limiter = Limiter(app, key_func=get_remote_address, default_limits=["60 per minute"])
   ```

---

*Roadmap prepared by: Luke Kovats | kovatsluke@gmail.com*
*For questions about this document or the codebase, reach out before engaging a new developer — context handoff will save significant ramp-up time.*
