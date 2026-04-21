import requests
import json
import time
from config import GROQ_API_KEY, GROQ_MODEL, MAX_RETRIES


def ask_llm(prompt: str, temperature: float = 0.2, max_tokens: int = 512) -> str:
    """
    Send a prompt to Groq (Llama3) and return the response text.
    Retries up to MAX_RETRIES times on failure.
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set in .env")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.HTTPError as e:
            print(f"[LLM] HTTP error attempt {attempt}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt)
        except Exception as e:
            print(f"[LLM] Error attempt {attempt}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(1)

    raise RuntimeError(f"LLM failed after {MAX_RETRIES} attempts")
