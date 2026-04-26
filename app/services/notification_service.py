import firebase_admin
from firebase_admin import credentials, messaging
import os
import logging

try:
    # Try to initialize the firebase admin SDK
    # It assumes the GOOGLE_APPLICATION_CREDENTIALS environment variable is set or 
    # firebase_adminsdk.json is present in the parent directory.
    cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase_adminsdk.json')
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        # Failsafe fallback initialization if no explicit cert path
        firebase_admin.initialize_app()
except ValueError:
    # App is already initialized
    pass
except Exception as e:
    logging.warning(f"Firebase Admin SDK could not be initialized: {e}. Push notifications will fail silently.")

def _send_notification(fcm_token, title, body, data_payload):
    """Internal helper to send a targeted FCM string."""
    if not fcm_token:
        # Token is empty or none, don't execute
        return False
        
    try:
        # We enforce string format for all keys and values in data_payload dictionary
        safe_data = {str(k): str(v) for k, v in data_payload.items()} if data_payload else {}
        
        # Add title and body to data payload to make it a data-only message
        safe_data['title'] = str(title)
        safe_data['body'] = str(body)
        
        message = messaging.Message(
            data=safe_data,
            token=fcm_token,
            android=messaging.AndroidConfig(
                priority='high'
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(content_available=True)
                )
            )
        )
        response = messaging.send(message)
        logging.info(f"Successfully sent message: {response}")
        return True
    except Exception as e:
        logging.error(f"Error sending FCM notification: {e}")
        return False

def send_like_notification(target_user, from_username, post_id):
    """Trigger when someone likes a post. Notifies the post owner."""
    if not target_user or not target_user.fcm_token:
        return False
        
    title = "New Like"
    body = f"{from_username} liked your post!"
    data = {
        "category": "LIKE",
        "postId": str(post_id)
    }
    
    return _send_notification(target_user.fcm_token, title, body, data)

def send_comment_notification(target_user, from_username, post_id):
    """Trigger when someone comments on a post."""
    if not target_user or not target_user.fcm_token:
        return False
        
    title = "New Comment"
    body = f"{from_username} commented on your post!"
    data = {
        "category": "COMMENT",
        "postId": str(post_id)
    }
    
    return _send_notification(target_user.fcm_token, title, body, data)

def send_chat_notification(target_user, from_username, chat_id, text_preview, sender_id=None):
    """Trigger when someone sends a direct chat message offline."""
    if not target_user or not target_user.fcm_token:
        return False
        
    title = f"New message from {from_username}"
    # Truncate for preview
    body = text_preview if len(text_preview) < 50 else text_preview[:47] + "..."
    if not body:
        body = "Sent an attachment"
        
    data = {
        "category": "CHAT",
        "chatId": str(chat_id),
        "userId": str(sender_id) if sender_id else ""
    }
    
    return _send_notification(target_user.fcm_token, title, body, data)
