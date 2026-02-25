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
        dict_story = story.to_dict()
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
            'url': dict_story['storyImage'],
            'type': 'image',
            'duration': 5000,
            'createdAt': dict_story['createdAt']
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
