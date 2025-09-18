import os
import hashlib
from datetime import datetime
from google.cloud import firestore
from google.oauth2 import service_account

# Load credentials from service account JSON
service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "serviceAccountKey.json")
credentials = service_account.Credentials.from_service_account_file(service_account_path)

# Initialize Firestore client with credentials
db = firestore.Client(credentials=credentials)

def upload_post(collection: str, title: str, description: str, link: str):
    """
    Uploads a post to the given Firestore collection with duplicate prevention.

    Args:
        collection (str): Firestore collection name ('news', 'jobs', etc.)
        title (str): Title of the content
        description (str): Description/content body
        link (str): Source link (used in deduplication)

    Returns:
        None
    """
    doc_id = hashlib.md5(f"{title}-{link}".encode()).hexdigest()

    doc_ref = db.collection(collection).document(doc_id)
    doc_ref.set({
        "title": title,
        "description": description,
        "link": link,
        "is_saved": False,
        "is_seen": False,
        "posted_on": datetime.utcnow()
    })

    print(f"[UPLOAD] ✅ Added to '{collection}': {title}")
