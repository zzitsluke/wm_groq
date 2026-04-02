# AI-Powered Study Suite
### An intelligent, course-specific study tool built on large language models

---

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                   │
│   Student selects        AI generates          Student learns    │
│   topic + mode    ──▶   personalized    ──▶   with quizzes,     │
│   (quiz, notes,         content via           flashcards,        │
│    case study...)       Groq LLM API          case studies       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

> **Why this matters for businesses and educators:**
> The rise of generative AI has created an opportunity to move beyond static study materials. This tool demonstrates how organizations can embed LLM-powered interactivity directly into existing educational workflows — with no AI expertise required from the end user, at near-zero infrastructure cost.

---

## Table of Contents
1. [Authors](#authors)
2. [Project Scope](#project-scope)
3. [Project Details](#project-details)
4. [Architecture](#architecture)
5. [Responsible AI Considerations](#responsible-ai-considerations)
6. [References](#references)

---

## Authors

| Name | GitHub |
|---|---|
| [Author 1] | [GitHub Profile]() |
| [Author 2] | [GitHub Profile]() |

---

## Project Scope

This project is narrowly scoped to a **single-course, instructor-defined AI study assistant** — not a general-purpose chatbot or full LMS replacement.

Specifically, the tool:
- Serves **one course at a time**, with module content defined and controlled by the instructor
- Generates **five content types** (flashcards, quizzes, notes, case studies, practice exams) from that content
- Acts as a **stateless AI proxy** — it does not store student data, conversation history, or personally identifiable information
- Is deployed as a **lightweight web application** accessible via a shared URL, with no student installation required

The scope explicitly excludes: user authentication, persistent cloud data, cross-course support, LMS integration, and grading functionality. These are documented as future phases but are not part of the v1.0 build.

---

## Project Details

### The Problem

Business school instructors face a structural challenge: students have access to the same static study materials (slides, readings, notes) semester after semester, but learning outcomes improve when students engage with content actively — through practice, self-testing, and application to novel scenarios. Creating that variety of practice material manually is time-intensive and rarely scales to individual student needs.

### The Solution

This tool takes instructor-provided course content and makes it interactively queryable through a simple web interface. Students select a topic and a study mode, and the system generates targeted content on demand using a large language model.

```
┌──────────────┐     POST /api/chat      ┌──────────────────┐
│   Browser    │ ──────────────────────▶ │  Flask Backend   │
│ (index.html) │                         │    (app.py)      │
│              │ ◀────────────────────── │                  │
└──────────────┘    Anthropic-shaped     └────────┬─────────┘
                       response                   │
                                                  │ Groq API call
                                                  ▼
                                        ┌──────────────────┐
                                        │    Groq LLM      │
                                        │ (llama-3.3-70b)  │
                                        └──────────────────┘
```

### Study Modes

| Mode | Description |
|---|---|
| **Flashcards** | Key concept pairs generated from module content |
| **Quiz** | Multiple-choice questions with explanations and scoring |
| **Notes** | Structured summaries of frameworks and key ideas |
| **Case Study** | AI-generated business scenario with discussion questions |
| **Practice Exam** | Multi-module timed exam with configurable question count |

### Technical Stack

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | HTML / CSS / JavaScript (single file) | Zero build tooling, fully portable |
| Backend | Python / Flask | Lightweight, minimal dependencies |
| LLM Provider | Groq API (llama-3.3-70b-versatile) | Free tier, fast inference, OpenAI-compatible |
| Hosting | GitHub Pages / any Python host | Static demo via GitHub Pages; Flask backend deployable to any Python host |
| Progress Storage | Browser localStorage | No backend database, no PII collected |

### Key Design Decisions

**Why Groq instead of OpenAI?**
Groq's free tier provides sufficient token throughput for a classroom setting at no cost, and its OpenAI-compatible API format minimized frontend changes. The backend translates responses to Anthropic's message shape, which the frontend already expected.

**Why a single HTML file for the frontend?**
Keeping the frontend as a single file with no build step makes the project fully portable. Any developer can open, read, and modify the interface without installing a build toolchain.

**Why no user accounts in v1.0?**
Adding authentication adds infrastructure complexity, privacy obligations, and deployment friction. For a pilot deployment, browser localStorage provides adequate progress persistence per device. Accounts are scoped to Phase 1 of the development roadmap.

### Progress Tracking

Student progress is stored in the browser's `localStorage` under the following keys:

| Key | Contents |
|---|---|
| `wm_studied` | Array of module names the student has engaged with |
| `wm_mastery` | Object mapping module → quiz/exam score percentage |
| `wm_pinned` | Array of pinned content items |
| `wm_streak` | Integer day-streak count |
| `wm_sessions` | Total session count |

This data persists across browser sessions on the same device and is never transmitted to any server.

---

## Architecture

```
project/
├── app.py              # Flask backend — LLM proxy, static file serving
├── requirements.txt    # Python dependencies
├── Procfile            # Production server config (gunicorn)
├── .env                # API key (excluded from distribution)
└── static/
    └── index.html      # Complete frontend — UI, prompts, rendering logic
```

**Request lifecycle:**
1. Student selects a topic and study mode in the browser
2. Frontend constructs a prompt embedding the relevant course content
3. `POST /api/chat` is called with an Anthropic-style request body
4. Flask backend validates the request, injects the Groq API key, and forwards to Groq
5. Groq returns a completion; Flask translates it to the Anthropic response shape
6. Frontend parses and renders the structured output (JSON for quizzes/flashcards, markdown for notes)

---

---

## Responsible AI Considerations

### Transparency
Students are aware they are interacting with an AI-generated study tool. The interface does not present AI-generated content as authoritative or human-authored.

### Accuracy & Hallucination Risk
Large language models can generate plausible but factually incorrect content. All generated material is grounded in instructor-provided course text, which reduces — but does not eliminate — hallucination risk. Students are encouraged to cross-reference generated content with course materials.

### Data Privacy
- No student data is collected, transmitted, or stored server-side
- The API key is held exclusively on the server and never exposed to the browser
- Browser localStorage data never leaves the student's device
- The tool does not log or retain student queries or AI responses

### Academic Integrity
This tool is designed as a **study aid**, not an assignment completion tool. It generates practice content from existing course materials rather than producing work intended for submission. Instructors retain full control over what course content is loaded into the system.

### Model Bias
The underlying LLM (Meta's LLaMA 3.3) may reflect biases present in its training data. Business case studies and scenario generation are areas where cultural and demographic bias can surface. Instructors should review AI-generated case studies before relying on them for class discussion.

### Environmental Cost
LLM inference carries a non-trivial energy cost. This tool mitigates that impact by using a lightweight model for most study modes (`llama-3.1-8b-instant`) and only routing to the larger model (`llama-3.3-70b-versatile`) for complex generation tasks like case studies and exams.

---

## References

> ⚠️ *[Placeholder — insert at least one peer-reviewed research paper less than 3 years old from an approved source. Recommended search terms: "large language models education", "LLM tutoring systems", "AI-generated formative assessment".]*

### Additional Resources
- [Groq API Documentation](https://console.groq.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com)
---
