from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.friend import Friend
from app.models.user import User

bp = Blueprint('friends', __name__)

@bp.route('/request', methods=['POST'])
def send_request():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
            
        user_id = data.get('userId')
        friend_id = data.get('friendId')
        
        if not user_id or not friend_id:
            return jsonify({'error': 'userId and friendId are required'}), 400
            
        if user_id == friend_id:
            return jsonify({'error': 'Cannot send a friend request to yourself'}), 400
            
        # Check if users exist
        user = User.query.get(user_id)
        friend_user = User.query.get(friend_id)
        if not user or not friend_user:
            return jsonify({'error': 'User or Friend not found'}), 404
            
        # Check if request already exists (either direction)
        existing_request = Friend.query.filter(
            ((Friend.user_id == user_id) & (Friend.friend_id == friend_id)) |
            ((Friend.user_id == friend_id) & (Friend.friend_id == user_id))
        ).first()

        if existing_request:
            if existing_request.status == 'accepted':
                return jsonify({'error': 'Already friends'}), 400
            else:
                return jsonify({'error': 'Friend request already exists'}), 400

        # Create new pending request
        friend_request = Friend(user_id=user_id, friend_id=friend_id, status='pending')
        db.session.add(friend_request)
        db.session.commit()
        
        return jsonify(friend_request.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/requests', methods=['GET'])
def get_requests():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
         return jsonify({'error': 'user_id is required'}), 400
         
    # Fetch pending requests received by the user
    pending_requests = Friend.query.filter_by(friend_id=user_id, status='pending').all()
    
    return jsonify({
        'requests': [req.to_dict() for req in pending_requests]
    }), 200

@bp.route('/accept', methods=['POST'])
def accept_request():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
            
        user_id = data.get('userId')
        request_id = data.get('requestId')
        
        if not user_id or not request_id:
            return jsonify({'error': 'userId and requestId are required'}), 400
            
        friend_request = Friend.query.get(request_id)
        if not friend_request:
            return jsonify({'error': 'Friend request not found'}), 404
            
        # Verify the user accepting is the receiver
        if str(friend_request.friend_id) != str(user_id):
            return jsonify({'error': 'Not authorized to accept this request'}), 403
            
        if friend_request.status == 'accepted':
            return jsonify({'error': 'Request already accepted'}), 400
            
        friend_request.status = 'accepted'
        
        # Create reciprocal relationship for easier querying
        reciprocal = Friend(user_id=friend_request.friend_id, friend_id=friend_request.user_id, status='accepted')
        db.session.add(reciprocal)
        
        db.session.commit()
        
        return jsonify({'message': 'Friend request accepted', 'friendship': friend_request.to_dict()}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/suggestions', methods=['GET'])
def get_suggestions():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
        
    try:
        # Get users who are NOT the current user
        # And NOT already friends (or pending) with the current user
        
        # 1. Get IDs of users involved in any friendship (pending or accepted) with current user
        existing_connections = Friend.query.filter(
            (Friend.user_id == user_id) | (Friend.friend_id == user_id)
        ).all()
        
        connected_user_ids = set()
        for conn in existing_connections:
            if str(conn.user_id) != str(user_id):
                connected_user_ids.add(conn.user_id)
            if str(conn.friend_id) != str(user_id):
                connected_user_ids.add(conn.friend_id)
                
        # 2. Query users not in connected_user_ids and not the user themselves
        suggestions_query = User.query.filter(User.id != user_id)
        if connected_user_ids:
            suggestions_query = suggestions_query.filter(~User.id.in_(connected_user_ids))
            
        suggestions = suggestions_query.limit(20).all()
        
        return jsonify({
            'suggestions': [user.to_dict() for user in suggestions]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/', methods=['GET'])
def get_friends():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
        
    try:
        # Get all accepted friendships for the user
        accepted_friendships = Friend.query.filter(
            ((Friend.user_id == user_id) | (Friend.friend_id == user_id)) &
            (Friend.status == 'accepted')
        ).all()
        
        friends_list = []
        for friendship in accepted_friendships:
            # Add the other user's details
            if str(friendship.user_id) != str(user_id) and friendship.user:
                friends_list.append(friendship.user.to_dict())
            elif str(friendship.friend_id) != str(user_id) and friendship.friend:
                friends_list.append(friendship.friend.to_dict())
                
        # Deduplicate list by id
        unique_friends = {f['id']: f for f in friends_list}.values()
        
        return jsonify({
            'friends': list(unique_friends)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
