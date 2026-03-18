from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.models.chat import Conversation, Message
from app.models.user import User
from app.models.friend import Friend
from sqlalchemy import or_, and_
import os

bp = Blueprint('chat', __name__)

@bp.route('/conversations', methods=['GET'])
def get_conversations():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    user_id = int(user_id)
        
    # Get all conversations where the user is either user1 or user2
    conversations = Conversation.query.filter(
        or_(Conversation.user1_id == user_id, Conversation.user2_id == user_id)
    ).order_by(Conversation.updated_at.desc()).all()
    
    return jsonify({
        'conversations': [conv.to_dict() for conv in conversations]
    }), 200

@bp.route('/<int:friend_id>/messages', methods=['GET'])
def get_messages(friend_id):
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    user_id = int(user_id)
        
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Check if they are accepted friends
    friendship = Friend.query.filter(
        or_(
            and_(Friend.user_id == user_id, Friend.friend_id == friend_id),
            and_(Friend.user_id == friend_id, Friend.friend_id == user_id)
        ),
        Friend.status == 'accepted'
    ).first()
    
    if not friendship:
        return jsonify({'error': 'You are not friends with this user or request is pending'}), 403

    # Find conversation
    conversation = Conversation.query.filter(
        or_(
            and_(Conversation.user1_id == user_id, Conversation.user2_id == friend_id),
            and_(Conversation.user1_id == friend_id, Conversation.user2_id == user_id)
        )
    ).first()
    
    if not conversation:
        return jsonify({'messages': [], 'has_next': False, 'total': 0}), 200
        
    pagination = Message.query.filter_by(conversation_id=conversation.id)\
        .order_by(Message.created_at.asc())\
        .paginate(page=page, per_page=per_page, error_out=False)
        
    messages = [msg.to_dict() for msg in pagination.items]
    
    return jsonify({
        'messages': messages,
        'has_next': pagination.has_next,
        'total': pagination.total,
        'conversation_id': conversation.id
    }), 200

@bp.route('/messages/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    user_id = request.args.get('user_id')
    message = Message.query.get_or_404(message_id)
    
    if str(message.sender_id) != str(user_id):
        return jsonify({'error': 'Unauthorized to delete this message'}), 401
        
    message.is_deleted = True
    message.text = None
    message.media_url = None
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Message deleted successfully'}), 200

@bp.route('/upload', methods=['POST'])
def upload_media():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400
        
    from app.utils import save_image
    url = save_image(file)
    if not url:
        return jsonify({'error': 'Failed to upload media'}), 500
        
    return jsonify({
        'url': url,
        'message': 'Upload successful'
    }), 200

