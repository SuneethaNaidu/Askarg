from fastapi import APIRouter, Body
from firebase_admin import firestore
from utils.fcm import send_fcm_notification

router = APIRouter()
db = firestore.client()

@router.post("/send-chat-notification")
async def send_chat_notification(payload: dict = Body(...)):
    room_id = payload.get("roomId")
    sender_uid = payload.get("sender")
    message = payload.get("text")

    room_ref = db.collection("chat_rooms").document(room_id)
    room_doc = room_ref.get()
    if not room_doc.exists:
        return {"error": "Room not found"}

    participants = room_doc.to_dict().get("participants", [])
    recipients = [uid for uid in participants if uid != sender_uid]

    for recipient_uid in recipients:
        user_doc = db.collection("users").document(recipient_uid).get()
        if user_doc.exists:
            fcm_token = user_doc.to_dict().get("fcm_token")
            if fcm_token:
                send_fcm_notification(
                    token=fcm_token,
                    title="New Message",
                    body=message
                )

    return {"status": "Notification sent"}
