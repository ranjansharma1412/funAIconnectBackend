from flask import Blueprint, request, jsonify, current_app, send_from_directory
from app.extensions import db
from app.models.story import Story
from app.utils import save_image

bp = Blueprint('stories', __name__)

@bp.route('/', methods=['GET'])
def get_stories():
    user_id = request.args.get('user_id')
    
    # We'll fetch stories from the last 24 hours (simplified for now to just fetch all ordered by date)
    stories_query = Story.query.order_by(Story.created_at.desc())
    all_stories = stories_query.all()
    
    # Group by user handle
    grouped_stories = {}
    for story in all_stories:
        dict_story = story.to_dict(current_user_id=user_id)
        handle = dict_story['userHandle']
        if handle not in grouped_stories:
            grouped_stories[handle] = {
                'id': handle,
                'name': dict_story['userName'],
                'image': dict_story['userImage'],
                'isLive': True, # Hardcoded for now, could be based on time
                'stories': []
            }
        
        # Map internal story structure to frontend expected format
        grouped_stories[handle]['stories'].append({
            'id': f"story-{dict_story['id']}",
            # Use raw internal int ID for interactions like 'Liking' a story
            'raw_id': dict_story['id'],
            'url': dict_story['storyImage'],
            'type': 'image',
            'duration': 5000,
            'createdAt': dict_story['createdAt'],
            'likesCount': dict_story.get('likesCount', 0),
            'hasLiked': dict_story.get('hasLiked', False)
        })
        
    # Convert to list
    result_list = list(grouped_stories.values())
    
    # Prioritize logged_in_user if user_id is provided
    if user_id and str(user_id).isdigit():
        from app.models.user import User
        current_user = User.query.get(int(user_id))
        if current_user:
            current_handle = current_user.username
            
            # Find current user in list and move to front
            current_user_group = None
            for i, group in enumerate(result_list):
                if group['id'] == current_handle:
                    current_user_group = result_list.pop(i)
                    break
                    
            if current_user_group:
                result_list.insert(0, current_user_group)
    
    return jsonify({
        'stories': result_list,
        'has_next': False,
        'has_prev': False,
        'total': len(result_list),
        'pages': 1
    }), 200

@bp.route('', methods=['POST'])
def create_story():
    try:
        data = request.form
        file = request.files.get('postImage')  # From UI we'll send it interchangeably, frontend might send 'postImage' or 'storyImage'. We'll check 'storyImage' then 'postImage' for backward compatibility via the same generic form logic if needed, but let's just stick to 'postImage' key for file to keep frontend simple if they re-use logic. Let's use 'postImage' here to match front-end payload for now.
        
        user_name = data.get('userName')
        user_handle = data.get('userHandle')
        user_image = data.get('userImage')
        description = data.get('description')
        hashtags = data.get('hashtags')
        is_verified = data.get('isVerified', 'false').lower() == 'true'
        
        if not user_name or not user_handle:
            return jsonify({'error': 'userName and userHandle are required'}), 400

        # Fetch latest user details from DB based on user_handle
        from app.models.user import User
        user = User.query.filter_by(username=user_handle).first()
        if user:
            user_name = user.full_name or user.username
            user_image = user.user_image

        story_image_path = None
        if file:
            story_image_path = save_image(file)
            
        story = Story(
            user_name=user_name,
            user_handle=user_handle,
            user_image=user_image,
            description=description,
            hashtags=hashtags,
            is_verified=is_verified,
            story_image=story_image_path
        )
        
        db.session.add(story)
        db.session.commit()
        
        return jsonify(story.to_dict()), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:id>', methods=['DELETE'])
def delete_story(id):
    story = Story.query.get_or_404(id)
    db.session.delete(story)
    db.session.commit()
    return jsonify({'message': 'Story deleted successfully'})

# Story Like Routes

@bp.route('/<int:story_id>/like', methods=['POST'])
def toggle_like(story_id):
    try:
        from app.models.story_like import StoryLike
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
            
        user_id = data.get('userId')
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
            
        story = Story.query.get_or_404(story_id)
        
        # Check if already liked
        existing_like = StoryLike.query.filter_by(story_id=story_id, user_id=str(user_id)).first()
        
        if existing_like:
            # Unlike
            db.session.delete(existing_like)
            story.likes_count = max(0, (story.likes_count or 0) - 1)
            liked = False
        else:
            # Like
            new_like = StoryLike(story_id=story_id, user_id=str(user_id))
            db.session.add(new_like)
            story.likes_count = (story.likes_count or 0) + 1
            liked = True
            
        db.session.commit()
        
        return jsonify({
            'liked': liked, 
            'likes': story.likes_count,
            'message': 'Story liked' if liked else 'Story unliked'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:story_id>/likes', methods=['GET'])
def get_story_likes(story_id):
    from app.models.user import User
    from app.models.story_like import StoryLike
    try:
        story = Story.query.get_or_404(story_id)
        
        # Get all likes for this story
        likes = StoryLike.query.filter_by(story_id=story_id).order_by(StoryLike.created_at.desc()).all()
        
        users = []
        for like in likes:
            user_id_str = like.user_id
            if user_id_str and user_id_str.isdigit():
                user = User.query.get(int(user_id_str))
                if user:
                    users.append(user.to_dict())
                    
        return jsonify({
            'likes': users,
            'count': len(users)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Story Comment Routes

@bp.route('/<int:story_id>/comments', methods=['GET'])
def get_comments(story_id):
    from app.models.story_comment import StoryComment
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    pagination = StoryComment.query.filter_by(story_id=story_id).order_by(StoryComment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    comments = [comment.to_dict() for comment in pagination.items]

    return jsonify({
        'comments': comments,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev,
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page
    }), 200

@bp.route('/<int:story_id>/comments', methods=['POST'])
def create_comment(story_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
            
        content = data.get('content')
        user_id = data.get('userId')
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
            
        # Verify story exists
        story = Story.query.get_or_404(story_id)
        
        from app.models.story_comment import StoryComment
        comment = StoryComment(
            content=content,
            user_id=user_id,
            story_id=story_id
        )
        
        db.session.add(comment)
        db.session.commit()
        
        return jsonify(comment.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:story_id>/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(story_id, comment_id):
    from app.models.story_comment import StoryComment
    comment = StoryComment.query.get_or_404(comment_id)
    
    if comment.story_id != story_id:
        return jsonify({'error': 'Comment does not belong to this story'}), 400
    
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({'message': 'Comment deleted successfully'}), 200
