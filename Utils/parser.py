import json
from typing import List, Dict

def parse_perplexity_response(response: str) -> List[Dict[str, str]]:
    """
    Parses a strict JSON response from Perplexity into a list of post dictionaries.
    Handles news, jobs, and internships with flexible key extraction.
    """
    try:
        data = json.loads(response.strip())

        if not isinstance(data, list):
            print("❌ Response is not a JSON array.")
            return []

        posts = []
        for item in data:
            if not isinstance(item, dict):
                continue

            post = {
                "title": item.get("title", "").strip(),
                "description": item.get("summary", item.get("description", "")).strip(),
                "link": item.get("link", "").strip(),
                "company": item.get("company", "").strip(),
                "location": item.get("location", "").strip()
            }

            if post["title"] and post["link"]:
                posts.append(post)

        return posts

    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        return []
