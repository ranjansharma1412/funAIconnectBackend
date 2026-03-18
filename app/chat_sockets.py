from app.extensions import socketio, db
from app.models.chat import Conversation, Message
from app.models.friend import Friend
from flask_socketio import emit, join_room, leave_room
from flask import request
from sqlalchemy import or_, and_
import json

connected_users = {} # user_id -> sid mapping

@socketio.on('connect')
def handle_connect():
    user_id = request.args.get('user_id')
    if user_id:
        connected_users[str(user_id)] = request.sid
        print(f"User {user_id} connected via WebSockets. SID: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    for uid, sid in connected_users.items():
        if sid == request.sid:
            del connected_users[uid]
            print(f"User {uid} disconnected")
            break

@socketio.on('join_chat')
def on_join_chat(data):
    """Join a specific conversation room"""
    user_id = int(data.get('userId'))
    friend_id = int(data.get('friendId'))
    
    # Generate deterministic room name
    room = f"chat_{min(int(user_id), int(friend_id))}_{max(int(user_id), int(friend_id))}"
    join_room(room)
    print(f"User {user_id} joined room {room}")

@socketio.on('leave_chat')
def on_leave_chat(data):
    user_id = int(data.get('userId'))
    friend_id = int(data.get('friendId'))
    room = f"chat_{min(int(user_id), int(friend_id))}_{max(int(user_id), int(friend_id))}"
    leave_room(room)
    print(f"User {user_id} left room {room}")

@socketio.on('send_message')
def handle_send_message(data):
    """
    data = {
        'userId': 1,
        'friendId': 2,
        'text': 'Hello',
        'mediaUrl': None,
        'mediaType': 'text'
    }
    """
    user_id = int(data.get('userId'))
    friend_id = int(data.get('friendId'))
    text = data.get('text')
    media_url = data.get('mediaUrl')
    media_type = data.get('mediaType', 'text')
    
    # Check friends
    friendship = Friend.query.filter(
        or_(
            and_(Friend.user_id == user_id, Friend.friend_id == friend_id),
            and_(Friend.user_id == friend_id, Friend.friend_id == user_id)
        ),
        Friend.status == 'accepted'
    ).first()
    
    if not friendship:
        emit('error', {'message': 'Not accepted friends'})
        return
        
    uid = min(user_id, friend_id)
    fid = max(user_id, friend_id)
    
    # Find or create conversation
    conv = Conversation.query.filter_by(user1_id=uid, user2_id=fid).first()
    if not conv:
        conv = Conversation(user1_id=uid, user2_id=fid)
        db.session.add(conv)
        db.session.commit()
        
    msg = Message(
        conversation_id=conv.id,
        sender_id=user_id,
        text=text,
        media_url=media_url,
        media_type=media_type,
        status='sent'
    )
    db.session.add(msg)
    conv.updated_at = msg.created_at
    db.session.commit()
    
    # Check if friend is online right now
    if str(friend_id) in connected_users:
        msg.status = 'delivered'
        db.session.commit()
    
    room = f"chat_{uid}_{fid}"
    
    # Send message to everyone in room, including sender
    emit('receive_message', msg.to_dict(), room=room)
    
    # Also notify active sessions outside the specific room to update Chat List latest message
    friend_sid = connected_users.get(str(friend_id))
    if friend_sid:
        emit('chat_list_update', conv.to_dict(), room=friend_sid)
        
    sender_sid = connected_users.get(str(user_id))
    if sender_sid:
        emit('chat_list_update', conv.to_dict(), room=sender_sid)

@socketio.on('read_message')
def handle_read_message(data):
    message_id = int(data.get('messageId'))
    user_id = int(data.get('userId'))
    friend_id = int(data.get('friendId'))
    
    msg = Message.query.get(message_id)
    if msg and str(msg.sender_id) != str(user_id):
        msg.status = 'read'
        db.session.commit()
        room = f"chat_{min(int(user_id), int(friend_id))}_{max(int(user_id), int(friend_id))}"
        emit('message_status_update', {'messageId': str(message_id), 'status': 'read'}, room=room)
