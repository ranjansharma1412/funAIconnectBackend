import os
from firebase_admin import credentials, messaging, initialize_app

try:
    cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase_adminsdk.json')
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        initialize_app(cred)
    else:
        initialize_app()
except ValueError:
    pass

token = "dy6YIDLmQBmkcFDiKQAuTY:APA91bEi9OgEf7KvfkfIhG9UsL4LkZdF1KvW7JdgEng4V2cH3FMCCVBVAFu3jDt56WvxJq-3m0_N8Vcg9jxyIeH5rMh6nI4DkauJjzcS49GgAdOqkN8rYc0"
title = "Friend Request"
body = "You have a new friend request! Tap to see."
data = {
    "category": "FRIEND_REQUEST",
    "test_id": "12345",
    "title": title,
    "body": body
}

print(f"Sending notification to token: {token}...")
message = messaging.Message(
    data=data,
    token=token,
    android=messaging.AndroidConfig(
        priority='high'
    ),
    apns=messaging.APNSConfig(
        payload=messaging.APNSPayload(
            aps=messaging.Aps(content_available=True)
        )
    )
)

try:
    response = messaging.send(message)
    print("Notification sent successfully! Response:", response)
except Exception as e:
    print("Failed to send:", e)
