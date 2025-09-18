from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from perplexity.client import fetch_perplexity_response
from utils.parser import parse_perplexity_response
from firebase_admin import credentials, firestore, initialize_app, messaging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from urllib.parse import urlparse
import atexit

# 🔐 Firebase Init
cred = credentials.Certificate("serviceAccountKey.json")
initialize_app(cred)
db = firestore.client()

# 🚀 FastAPI App
app = FastAPI()

# 🌐 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔔 Push Notifications
def send_push_notification(token: str, title: str, body: str):
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        token=token,
    )
    try:
        response = messaging.send(message)
        print("✅ Notification sent:", response)
    except Exception as e:
        print("❌ Notification error:", e)

@app.get("/")
def root():
    return {"status": "success", "message": "🚀 Askarg Backend is live!"}

@app.get("/ping")
def ping():
    return {"message": "pong"}

@app.post("/test-notification")
def test_notification(token: str = Body(...)):
    send_push_notification(token, "Test Push", "You got this from Askarg backend 🚀")
    return {"message": "Test notification sent"}

# 🔍 Platform extraction for backend filtering
def extract_platform_from_link(url):
    domain = urlparse(url).netloc.lower()
    if "linkedin.com" in domain:
        return "LinkedIn"
    elif "indeed.com" in domain:
        return "Indeed"
    elif "internshala.com" in domain:
        return "Internshala"
    elif "angel.co" in domain or "wellfound.com" in domain:
        return "AngelList"
    elif "amazon.jobs" in domain:
        return "Amazon"
    elif "microsoft.com" in domain:
        return "Microsoft"
    elif "cognizant.com" in domain:
        return "Cognizant"
    elif "ibm.com" in domain:
        return "IBM"
    elif "google.com" in domain:
        return "Google"
    elif "hackerearth.com" in domain:
        return "HackerEarth"
    elif "radixweb.com" in domain:
        return "Radixweb"
    elif "github.com" in domain:
        return "GitHub"
    else:
        return "Other"

def filter_unique_platform_posts(posts):
    seen_platforms = set()
    filtered = []
    for post in posts:
        link = post.get("link", "")
        platform = extract_platform_from_link(link)
        if platform not in seen_platforms and platform != "Other":
            seen_platforms.add(platform)
            filtered.append(post)
        if len(filtered) == 5:
            break
    return filtered

@app.api_route("/fetch-and-upload", methods=["GET", "POST"])
def fetch_and_upload(token: str = Body(default=None)):
    prompts = {
        "news_articles": (
            "Generate exactly 5 very recent technology news stories, published within the last 5 days, strictly relevant to students, early-career developers, and tech learners. "
            "Focus on real-world innovation and learning impact, especially in rural (Tier 2/3) and metro areas. Avoid any repeated, outdated, or irrelevant content. "
            "Return only the output as a strict JSON array of 5 objects, where each object must contain: "
            "\"title\": short and clear headline (string), "
            "\"summary\": max 60 words, student-friendly, plain English, no jargon, "
            "\"link\": valid HTTPS URL from a real, trustworthy source. "
            "Use only the most trusted international and Indian sources such as: WSJ, TechCrunch, EdSurge, Times of India, Indian Express, The Hindu, BBC, The Verge, Reuters, TIME, EdTechReview, HolonIQ, Nikkei Asia, Microsoft News, EdTech Hub, EdSurge, UNESCO, etc. "
            "Only cover these categories: Advanced AI in Education, Must-Have Tech Gadgets, Digital Classroom Innovations, Major Tech Industry Shifts, Internship & Job Opportunities, AI Tools, Bootcamps, Campus Entrepreneurship, Cybersecurity for Students, Scholarships, Green Tech in Education, Women in STEM, Regional Language EdTech, and Student Empowerment in Tier 2/3. "
            "Do not include news older than 5 days, AI-generated content, or repeated stories. Output must be clean JSON array. No comments or notes."
        ),
        "jobs": (
            "Fetch exactly 5 currently active, verified, and relevant job listings for freshers, recent graduates, or early-career software professionals in India. "
            "Include remote, hybrid, or onsite roles. Listings must be posted within the last 3 days only and should not be duplicated. "
            "Each job must be from a different platform. "
            "Allowed platforms: LinkedIn Jobs, Indeed India, Internshala, AngelList (Wellfound), Microsoft Careers, Amazon Jobs, Google Careers, Radixweb, Cognizant, Infosys, IBM, GitHub Jobs, EdTech platforms. "
            "If fewer than 5 unique platforms have results, allow duplicates from the most recent and relevant platforms to fill the list. "
            "Each job must include the following fields: "
            "- \"title\": Job title (short and clear) "
            "- \"company\": Employer name "
            "- \"location\": City, Remote, or Hybrid "
            "- \"link\": A valid, direct job application or listing URL "
            "Respond only with a clean JSON array of 5 job objects. Do not include any text, notes, summaries, or explanations outside the JSON."
        ),
        "internships": (
            "Fetch up to 5 currently active and verified internship opportunities in India for students and fresh graduates in software-related roles. "
            "These internships must be suitable for learners with little to no professional experience and should preferably mention that they offer a stipend if available. "
            "Domains must include Web Development, Mobile App Development (Android/iOS), AI/ML, Data Science, Cybersecurity, Cloud Computing, or QA/Testing. "
            "Only return roles from the last 7 days — no expired, duplicated, or irrelevant listings. "
            "Prefer internships from different platforms in this list: Internshala, AngelList Talent (angel.co/jobs), LinkedIn Internships, Turing, Microsoft Careers, Google Careers, IBM Careers, Cognizant Careers, HackerEarth Jobs, leading EdTech platforms. "
            "If fewer than 5 unique platforms have results, allow duplicates from the most recent and relevant platforms to fill the list. "
            "Return the output strictly as a clean JSON array of up to 5 internship objects, where each object contains only: "
            "\"title\" (string), \"company\" (string), \"location\" (Remote/City), and \"link\" (valid HTTPS apply URL). "
            "Do not include any extra information, summaries, explanations, headings, or formatting outside the JSON array."
        )
    }

    notifications_sent = []

    for collection, prompt in prompts.items():
        print(f"[FETCH] {collection}")
        content = fetch_perplexity_response(prompt)
        if not content:
            print(f"❌ Failed to fetch {collection}")
            continue

        posts = parse_perplexity_response(content)

        if collection in ["jobs", "internships"]:
            posts = filter_unique_platform_posts(posts)

        print(f"✅ Parsed {len(posts)} entries for {collection}")
        new_count = 0

        for post in posts:
            title = post.get("title", "").strip()
            link = post.get("link", "").strip()
            if not title or not link:
                continue

            timestamp = datetime.utcnow()

            if collection == "news_articles":
                exists = db.collection("news_articles").where("title", "==", title).get()
                if exists:
                    print(f"⚠️ Skipping duplicate news: {title}")
                    continue

                db.collection("news_articles").document().set({
                    "title": title,
                    "summary": post.get("summary", post.get("description", "")),
                    "fullContent": "",
                    "source": "",
                    "url": link,
                    "timestamp": timestamp,
                    "keywords": []
                })
            else:
                exists = db.collection("internships_jobs").where("title", "==", title).where("link", "==", link).get()
                if exists:
                    print(f"⚠️ Skipping duplicate job/internship: {title}")
                    continue

                db.collection("internships_jobs").document().set({
                    "title": title,
                    "company": post.get("company", "Not specified"),
                    "location": post.get("location", "Not specified"),
                    "type": "Job" if collection == "jobs" else "Internship",
                    "link": link,
                    "timestamp": timestamp,
                    "keywords": []
                })

            new_count += 1

        if new_count > 0 and token:
            notif_title = {
                "news_articles": "New Tech News 🔔",
                "jobs": "Jobs Updated 💼",
                "internships": "Internships Updated 🎓"
            }[collection]
            notif_body = {
                "news_articles": "New articles have been added.",
                "jobs": "New job posts available.",
                "internships": "Fresh internships just added."
            }[collection]
            send_push_notification(token, notif_title, notif_body)
            notifications_sent.append(collection)

        print(f"✅ Uploaded {new_count} new items to {collection}")

    return {
        "status": "success",
        "notified": notifications_sent,
        "collections": list(prompts.keys())
    }

# 🧹 Delete Old Data
def delete_old_content():
    try:
        cutoff = datetime.combine(datetime.utcnow().date() - timedelta(days=1), datetime.min.time())
        news_deleted = db.collection("news_articles").where("timestamp", "<", cutoff).stream()
        for doc in news_deleted:
            doc.reference.delete()
            print(f"🧹 Deleted old news: {doc.id}")

        jobs_deleted = db.collection("internships_jobs").where("timestamp", "<", cutoff).stream()
        for doc in jobs_deleted:
            doc.reference.delete()
            print(f"🧹 Deleted old job/internship: {doc.id}")
    except Exception as e:
        print("❌ Error deleting old content:", e)

def delete_old_chat_messages():
    try:
        cutoff = datetime.combine(datetime.utcnow().date() - timedelta(days=1), datetime.min.time())
        rooms = db.collection("chat_rooms").stream()
        for room in rooms:
            messages = (
                db.collection("chat_rooms")
                .document(room.id)
                .collection("messages")
                .where("timestamp", "<", cutoff)
                .stream()
            )
            for msg in messages:
                msg.reference.delete()
                print(f"🧹 Deleted old message in room {room.id}: {msg.id}")
    except Exception as e:
        print("❌ Error deleting old messages:", e)

# 🔁 Scheduler
def auto_fetch():
    print("⏰ Running scheduled fetch-and-upload (no token)...")
    try:
        fetch_and_upload(token=None)
        delete_old_content()
        delete_old_chat_messages()
    except Exception as e:
        print("❌ Scheduler error:", e)

scheduler = BackgroundScheduler()
scheduler.add_job(auto_fetch, 'interval', hours=1)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# ✅ Manual Delete Route
@app.get("/delete-old")
def manual_delete():
    delete_old_content()
    delete_old_chat_messages()
    return {"status": "Old content and messages deleted"}
