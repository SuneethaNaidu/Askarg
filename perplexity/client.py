import os
import requests
from typing import Optional

# ✅ Correct endpoint for pplx-* keys (no /v1)
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

def fetch_perplexity_response(prompt: str) -> Optional[str]:
    """
    Calls the Perplexity API (Sonar Pro model) and returns the response text.
    """
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("[ERROR] PERPLEXITY_API_KEY not set in environment variables.")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": "You are Askarg AI Assistant helping students find tech news and jobs. Always respond in pure JSON format without explanations or markdown."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.5
    }

    try:
        response = requests.post(PERPLEXITY_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        content = response.json().get("choices", [])[0]["message"]["content"]
        return content.strip()
    except requests.exceptions.HTTPError as http_err:
        print(f"[HTTP ERROR] {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[ERROR] Perplexity API call failed: {e}")
    
    return None
