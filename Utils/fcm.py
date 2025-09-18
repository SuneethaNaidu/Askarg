from firebase_admin import messaging

def send_fcm_notification(token: str, title: str, body: str):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
    )
    try:
        response = messaging.send(message)
        print("✅ Chat Notification sent:", response)
    except Exception as e:
        print("❌ Chat Notification error:", e)
