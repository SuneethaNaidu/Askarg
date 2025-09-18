import os
import uuid
from datetime import datetime, timedelta, timezone
from firebase_admin import credentials, firestore, initialize_app
from services.perplexity import fetch_perplexity_response
from utils.parser import parse_perplexity_response

# 🔹 Initialize Firebase Admin
cred = credentials.Certificate("serviceAccountKey.json")
initialize_app(cred)
db = firestore.client()

# 🔹 Define refined prompts
PROMPTS = {
    "news_articles": "Give me 5 latest technology news articles with clickable links. Focus on AI, software, or hardware trends.",
    "internships": "Give me 5 latest software development internships for students in India. Mention company name, location, internship type, and a direct application link.",
    "jobs": "Give me 5 latest remote software developer jobs. Mention job title, company name, job type, and a direct apply link."
}

# 🔥 DELETE old news_articles (older than 2 days)
def delete_old_news_articles():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=2)

    articles_ref = db.collection("news_articles")
    old_articles = articles_ref.where("timestamp", "<", cutoff).stream()

    deleted_count = 0
    for doc in old_articles:
        doc.reference.delete()
        deleted_count += 1

    print(f"🧹 Deleted {deleted_count} old news articles.")

# 🔥 DELETE old internships and jobs (older than 2 days)
def delete_old_internships_jobs():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=2)

    jobs_ref = db.collection("internships_jobs")
    old_docs = jobs_ref.where("timestamp", "<", cutoff).stream()

    deleted_count = 0
    for doc in old_docs:
        doc.reference.delete()
        deleted_count += 1

    print(f"🧹 Deleted {deleted_count} old internships/jobs.")

# ⬆️ Upload News
def upload_news(posts: list):
    for post in posts:
        doc_id = str(uuid.uuid4())
        db.collection("news_articles").document(doc_id).set({
            "title": post.get("title", ""),
            "summary": post.get("description", ""),
            "fullContent": "",
            "source": "",
            "url": post.get("link", ""),
            "timestamp": datetime.now(timezone.utc),
            "keywords": []
        })
    print(f"📥 Uploaded {len(posts)} news articles.")

# ⬆️ Upload Internships / Jobs
def upload_internships_jobs(posts: list, is_job=True):
    for post in posts:
        doc_id = str(uuid.uuid4())
        db.collection("internships_jobs").document(doc_id).set({
            "title": post.get("title", ""),
            "company": post.get("company", ""),
            "location": post.get("location", ""),
            "type": "Job" if is_job else "Internship",
            "link": post.get("link", ""),
            "timestamp": datetime.now(timezone.utc),
            "keywords": []
        })
    print(f"📥 Uploaded {len(posts)} {'jobs' if is_job else 'internships'}.")

# 🚀 Main Orchestrator
def main():
    print("🔁 Starting fetch and upload process...")

    # ✅ Auto-delete old documents
    delete_old_news_articles()
    delete_old_internships_jobs()

    for collection, prompt in PROMPTS.items():
        print(f"\n📡 Fetching data for: {collection}")
        raw_response = fetch_perplexity_response(prompt)

        if not raw_response:
            print(f"❌ Failed to fetch data for: {collection}")
            continue

        posts = parse_perplexity_response(raw_response)

        if collection == "news_articles":
            upload_news(posts)
        elif collection == "jobs":
            upload_internships_jobs(posts, is_job=True)
        elif collection == "internships":
            upload_internships_jobs(posts, is_job=False)

    print("✅ Fetch and upload process completed.")

if __name__ == "__main__":
    main()
