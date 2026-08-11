import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.2-1b-instruct")


class LLMParseError(Exception):
    """Raised whenever the LLM can't be reached or its output isn't usable JSON."""
    pass


_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        if not NVIDIA_API_KEY:
            raise LLMParseError("NVIDIA_API_KEY is not configured")
        _client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=NVIDIA_API_KEY)
    return _client


SYSTEM_PROMPT = """You are an NLU engine for an admin chatbot that manages user records.
The admin may issue ONE or MULTIPLE actions in a single message.
Output ONLY a valid JSON array (no extra text, no markdown fences) where each element has this exact structure:
{
  "action": "add" | "update" | "delete" | "unknown",
  "email": "<email address if mentioned, else null>",
  "name": "<person's first name if mentioned and no email is given, else null>",
  "fields": {"phone": "<value>", "city": "<value>", "name": "<value>", "email": "<value>"}
}

Rules:
- Always return a JSON array, even for a single action: [{...}]
- "add": creating a new user. fields should include any attributes provided.
- "update": changing one or more attributes of an existing user identified by name or email. fields contains only the changed field(s).
- "delete": removing a user identified by name or email.
- If you cannot confidently determine any action, return [{"action": "unknown", "email": null, "name": null, "fields": {}}]
- NEVER invent or guess an email or name that was not explicitly written in the message. If no email or name is present, set them to null.
- Only include keys in "fields" that were actually mentioned in the message.
- Output raw JSON array only. No explanation, no markdown."""


def _strip_fences(text: str) -> str:
    """Remove markdown code fences if the LLM wraps its output."""
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


def _normalise_intent(intent: dict) -> dict:
    """Ensure every intent dict has the required keys."""
    if "action" not in intent:
        raise LLMParseError("LLM intent missing 'action' key")
    intent.setdefault("email", None)
    intent.setdefault("name", None)
    intent.setdefault("fields", {})
    return intent


def _extract_intents(content: str) -> list:
    """
    Parse the LLM's raw text into a list of intent dicts.
    Handles three cases robustly:
      1. Correct: JSON array  -> [{...}, {...}]
      2. LLM ignored instructions: multiple bare objects -> {...}\n{...}
      3. Single object (old behaviour): {...}
    """
    text = _strip_fences(content)

    # Try parsing as-is first (covers cases 1 and 3)
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [_normalise_intent(i) for i in data]
        if isinstance(data, dict):
            return [_normalise_intent(data)]
    except json.JSONDecodeError:
        pass

    # Fallback: extract every JSON object in the raw text (case 2)
    intents = []
    decoder = json.JSONDecoder()
    idx = 0
    while idx < len(text):
        # Skip whitespace between objects
        while idx < len(text) and text[idx] in ' \t\n\r':
            idx += 1
        if idx >= len(text):
            break
        try:
            obj, end_idx = decoder.raw_decode(text, idx)
            intents.append(_normalise_intent(obj))
            idx += end_idx - idx
        except json.JSONDecodeError:
            break

    if not intents:
        raise LLMParseError("Could not extract any valid JSON intent from LLM response")
    return intents


def parse(message: str) -> list:
    """Call the LLM and return a list of intent dicts (always a list, even for one action)."""
    try:
        client = get_client()
        completion = client.chat.completions.create(
            model=NVIDIA_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            temperature=0.2,
            top_p=0.7,
            max_tokens=512,
            stream=False,
        )
        content = completion.choices[0].message.content
        if not content:
            raise LLMParseError("Empty response from LLM")
        return _extract_intents(content)
    except LLMParseError:
        raise
    except Exception as e:
        raise LLMParseError(f"LLM parsing failed: {e}")