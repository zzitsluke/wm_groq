# Live Code Demo — Agentic Design Focus

> "Most people think 'agentic AI' means robots making autonomous decisions in some complex system. We're going to show you exactly what agentic AI looks like in code — and how simple each pattern actually is."

---

## Demo 1 — "Calling AI is just a POST request"
**`app.py` · Lines 76–90, 178–183**

```python
def to_groq_payload(messages: list, model: str, max_tokens: int) -> dict:
    """
    Build a Groq (OpenAI-compatible) request body from the frontend's
    Anthropic-style messages array. Format is nearly identical so
    translation is minimal.

    Anthropic: [{"role": "user", "content": "..."}]
    Groq/OAI:  [{"role": "user", "content": "..."}]  ← same!
    """
    return {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.85,
    }
```

```python
for attempt in range(3):
    try:
        resp = requests.post(
            GROQ_API_URL, json=payload, headers=headers, timeout=120.0
        )
```

> "This is the entire AI integration. A function that builds a dictionary, and a POST request. That's it."

---

## Demo 2 — "The prompt is code, not a chat box"
**`static/index.html` · Lines 2272–2283, 2842**

```javascript
return `You are creating quiz questions for William & Mary MBA Strategic Marketing students.

COURSE MATERIAL:
${truncated}

Create exactly 5 multiple-choice questions based strictly on this material.

Return ONLY valid JSON (no markdown, no explanation), exactly like this:
{"questions":[{"q":"Question text?","options":["A) option","B) option","C) option","D) option"],"answer":1,"explanation":"Brief explanation of why this is correct, referencing the material."}]}

The answer field is the 0-based index of the correct option. Make questions test genuine understanding, not just recall. Include one application question (applying the concept to a new scenario).`;
```

```javascript
const systemContext = `You are an expert AI tutor for William & Mary MBA students studying Strategic Marketing — specifically the "${selectedTopic}" module. Use the following course material as your knowledge base:\n\n${material}\n\nAnswer clearly and concisely (3-5 sentences unless more depth is needed). Use specific examples from the material. Be encouraging and guide understanding rather than just reciting facts.`;
```

> "Every prompt is assembled fresh at runtime. The course material, the study mode, the student's history — all combined in code before a single token is sent."

---

## Demo 3 — Agentic Pattern 1: Autonomous Model Routing
**`static/index.html` · Line 2199**

```javascript
model: selectedMode === 'casestudy' || selectedMode === 'exam'
    ? 'llama-3.3-70b-versatile'
    : 'llama-3.1-8b-instant',
```

> "Before every API call, the app autonomously decides which model to use based on task complexity. No user input. One line of decision logic — that's an agentic behavior."

---

## Demo 4 — Agentic Pattern 2: Multi-Turn Memory Management
**`static/index.html` · Lines 2846–2849**

```javascript
// chatHistory[0] is the synthetic greeting — skip it for the API call
// chatHistory[1..] is the real conversation; keep only the last 4 messages to cap token growth
const convo = chatHistory.slice(1);
const windowed = convo.length > 5 ? [convo[0], ...convo.slice(-4)] : convo;
const apiMessages = windowed.map((m, i) => {
    if (i === 0) return { role: 'user', content: systemContext + '\n\nStudent question: ' + m.content };
    return { role: m.role, content: m.content };
});
```

> "The AI has no memory between calls — it's stateless. So the app manages context itself. It anchors the first turn to keep the course material in scope, then slides a window of the last 4 turns. The system decides what to remember and what to drop — autonomously."

---

## Demo 5 — Agentic Pattern 3: Self-Repair Loop
**`static/index.html` · Lines 2512–2526**

```javascript
function repairJSON(str) {
  // Remove markdown fences
  str = str.replace(/```json|```/g, '').trim();
  // Try parsing as-is first
  try { return JSON.parse(str); } catch(e) {}
  // Attempt to close truncated JSON by finding last complete question object
  const lastGoodBrace = str.lastIndexOf('"}');
  if (lastGoodBrace !== -1) {
    let repaired = str.slice(0, lastGoodBrace + 2);
    // Close questions array and root object if needed
    const openBrackets = (repaired.match(/\[/g) || []).length - (repaired.match(/\]/g) || []).length;
    const openBraces = (repaired.match(/\{/g) || []).length - (repaired.match(/\}/g) || []).length;
    repaired += ']'.repeat(Math.max(0, openBrackets)) + '}'.repeat(Math.max(0, openBraces));
    try { return JSON.parse(repaired); } catch(e2) {}
  }
  return null;
}
```

> "The system catches its own mistakes and corrects them without the user ever knowing something went wrong. That's autonomous error recovery — a core agentic pattern."

---

## Demo 6 — Agentic Pattern 4: Retry with Exponential Backoff
**`app.py` · Lines 178, 210**

```python
for attempt in range(3):
    ...
    time.sleep(2 ** attempt)  # 1s, then 2s
```

> "If the network drops, the backend retries automatically — waiting longer each time so it doesn't hammer a struggling service. The user sees nothing. The system handles it."

---

## Demo 7 — Agentic Pattern 5: Two-Step Evaluation Pipeline
**`static/index.html` · Lines 2199 + 2603**

```javascript
// Step 1 — Generate scenario (line 2199, 70b model)
model: selectedMode === 'casestudy' || selectedMode === 'exam'
    ? 'llama-3.3-70b-versatile'
    : 'llama-3.1-8b-instant',
```

```javascript
// Step 2 — Evaluate student response (line 2603, independent API call)
content: `You are a William & Mary MBA professor evaluating a student's case study response
for a Strategic Marketing course on "${selectedTopic}".

DISCUSSION QUESTION: ${question}

STUDENT'S ANSWER: ${studentAnswer}`
```

> "One student action triggers a multi-step pipeline: generate a scenario, wait for the student, then evaluate their answer. The system orchestrates both steps. That's an agent acting across multiple turns of reasoning."

---

## Close — Run it live

```bash
python app.py
```

Open browser → select a module → generate a quiz → show the result.

> "Six agentic patterns. The whole backend is under 240 lines of Python. The complexity isn't in the code — it's in the design."
