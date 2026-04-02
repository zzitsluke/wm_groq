"""
W&M Strategic Marketing Study Suite — Flask Backend (Groq Edition)
==================================================================
Proxies Groq API calls so the API key never touches the browser.
Serves the frontend HTML as a static file.

Groq uses an OpenAI-compatible API format, so the translation layer
is minimal compared to other providers.

Usage:
    pip install -r requirements.txt
    export GROQ_API_KEY=gsk_...
    python app.py

Get a free API key at: https://console.groq.com
"""

import os
import logging
import time

from dotenv import load_dotenv
load_dotenv()  # loads .env file automatically

import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# ── App setup ─────────────────────────────────────────────────────────────────

app = Flask(__name__, static_folder="static")
CORS(app)

# ── Always return JSON errors, never HTML ─────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": {"message": "Endpoint not found"}}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": {"message": f"Internal server error: {e}"}}), 500

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Groq uses an OpenAI-compatible chat completions endpoint
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Allowed models — free tier includes all of these
# See full list at: https://console.groq.com/docs/models
ALLOWED_MODELS = {
    "llama-3.3-70b-versatile",    # recommended — best quality on free tier
    "llama-3.1-8b-instant",       # fastest, lightest
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
}

# Per-request output token cap
MAX_TOKENS_CAP = 2000


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_api_key() -> str:
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "GROQ_API_KEY environment variable is not set. "
            "Get a free key at https://console.groq.com"
        )
    return key


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


def to_anthropic_response(groq_response: dict, model: str) -> dict:
    """
    Convert Groq's OpenAI-compatible response into the Anthropic response
    shape the frontend expects — so no JS changes are needed.

    Groq path:     choices[0].message.content
    Anthropic path: content[0].text
    """
    try:
        text = groq_response["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise ValueError(
            f"Unexpected Groq response structure: {e}. "
            f"Keys received: {list(groq_response.keys())}"
        )

    return {
        "content": [{"type": "text", "text": text}],
        "model": groq_response.get("model", model),
        "role": "assistant",
        "stop_reason": "end_turn",
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the frontend HTML."""
    return send_from_directory("static", "index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Proxy endpoint. Accepts Anthropic-style request body from the frontend,
    forwards to Groq, and returns an Anthropic-shaped response.

    Expected request body:
    {
        "model": "llama-3.3-70b-versatile",
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": "..."}]
    }
    """
    try:
        body = request.get_json(force=True)
    except Exception:
        return jsonify({"error": {"message": "Invalid JSON body"}}), 400

    # ── Validation ────────────────────────────────────────────────────────────

    model = body.get("model", "llama-3.3-70b-versatile")
    if model not in ALLOWED_MODELS:
        return jsonify({"error": {"message": f"Model '{model}' is not allowed."}}), 400

    messages = body.get("messages", [])
    if not messages or not isinstance(messages, list):
        return jsonify({"error": {"message": "messages array is required."}}), 400

    try:
        max_tokens = min(int(body.get("max_tokens", 1000)), MAX_TOKENS_CAP)
    except (ValueError, TypeError):
        return jsonify({"error": {"message": "max_tokens must be a number."}}), 400

    # ── Get API key ───────────────────────────────────────────────────────────

    try:
        api_key = get_api_key()
    except EnvironmentError as e:
        logger.error(str(e))
        return jsonify({"error": {"message": str(e)}}), 500

    # ── Build and send Groq request ───────────────────────────────────────────

    payload = to_groq_payload(messages, model, max_tokens)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    logger.info(f"Forwarding to Groq model={model} max_tokens={max_tokens}")

    last_error = None
    for attempt in range(3):
        try:
            resp = requests.post(
                GROQ_API_URL, json=payload, headers=headers, timeout=120.0
            )

            logger.info(f"Groq API responded with status {resp.status_code}")

            if resp.status_code == 401:
                return jsonify({"error": {"message": "Invalid Groq API key. Generate a new one at console.groq.com and update your .env file."}}), 401

            if resp.status_code == 429:
                retry_after = resp.headers.get("retry-after", "60")
                return jsonify({"error": {"message": f"Groq rate limit reached. Wait {retry_after}s and try again. Consider using a smaller model or fewer requests."}}), 429

            if resp.status_code != 200:
                try:
                    groq_err = resp.json()
                    msg = groq_err.get("error", {}).get("message", resp.text)
                except Exception:
                    msg = resp.text
                return jsonify({"error": {"message": f"Groq API error ({resp.status_code}): {msg}"}}), resp.status_code

            groq_data = resp.json()
            break  # success

        except requests.Timeout:
            return jsonify({"error": {"message": "Request to Groq API timed out after 120s."}}), 504
        except requests.ConnectionError as e:
            last_error = e
            logger.warning(f"Connection error calling Groq (attempt {attempt + 1}/3): {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)
    else:
        logger.error(f"All Groq retries exhausted: {last_error}")
        return jsonify({"error": {"message": "Could not connect to Groq API. Check your internet connection or try again shortly."}}), 502

    # ── Translate response to Anthropic shape ─────────────────────────────────

    try:
        anthropic_response = to_anthropic_response(groq_data, model)
    except ValueError as e:
        logger.error(f"Response translation error: {e}")
        return jsonify({"error": {"message": str(e)}}), 500

    return jsonify(anthropic_response), 200


@app.route("/health")
def health():
    """Simple health check for deployment platforms."""
    return jsonify({"status": "ok", "service": "wm-study-suite", "provider": "groq"})


# ── Dev server ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    logger.info(f"Starting W&M Study Suite (Groq) on port {port} (debug={debug})")
    app.run(host="127.0.0.1", port=port, debug=debug)
