from flask import Blueprint, request, jsonify, current_app, send_from_directory, url_for
from app.extensions import db
from app.models.post import Post
from app.models.like import Like
from app.utils import save_image
from app.utils import save_image
import os

bp = Blueprint('posts', __name__)

@bp.route('/', methods=['GET'])
def get_posts():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    user_id = request.args.get('user_id')
    
    posts_query = Post.query.order_by(Post.created_at.desc())
    posts_pagination = posts_query.paginate(page=page, per_page=per_page, error_out=False)
    
    posts = [post.to_dict(current_user_id=user_id) for post in posts_pagination.items]
    
    return jsonify({
        'posts': posts,
        'has_next': posts_pagination.has_next,
        'has_prev': posts_pagination.has_prev,
        'total': posts_pagination.total,
        'pages': posts_pagination.pages
    }), 200

@bp.route('/<int:id>', methods=['GET'])
def get_post(id):
    user_id = request.args.get('user_id')
    post = Post.query.get_or_404(id)
    return jsonify(post.to_dict(current_user_id=user_id))

@bp.route('', methods=['POST'])
def create_post():
    try:
        data = request.form
        file = request.files.get('postImage')
        
        user_name = data.get('userName')
        user_handle = data.get('userHandle')
        # userImage is strictly URL in this requirement or string
        user_image = data.get('userImage')
        description = data.get('description')
        hashtags = data.get('hashtags')
        is_verified = data.get('isVerified', 'false').lower() == 'true'
        likes = data.get('likes', 0, type=int)
        
        if not user_name or not user_handle:
            return jsonify({'error': 'userName and userHandle are required'}), 400

        # Fetch latest user details from DB based on user_handle
        from app.models.user import User
        user = User.query.filter_by(username=user_handle).first()
        if user:
            user_name = user.full_name or user.username
            user_image = user.user_image

        post_image_path = None
        if file:
            post_image_path = save_image(file)
            
        post = Post(
            user_name=user_name,
            user_handle=user_handle,
            user_image=user_image,
            description=description,
            hashtags=hashtags,
            is_verified=is_verified,
            post_image=post_image_path,
            likes=likes
        )
        
        db.session.add(post)
        db.session.commit()
        
        return jsonify(post.to_dict()), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:id>', methods=['DELETE'])
def delete_post(id):
    post = Post.query.get_or_404(id)
    
    # Optional: Delete image file if exists
    # if post.post_image:
    #     full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(post.post_image))
    #     if os.path.exists(full_path):
    #         os.remove(full_path)
    
    db.session.delete(post)
    db.session.commit()
    return jsonify({'message': 'Post deleted successfully'})

# Route to serve uploaded files
@bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

# Comment Routes

@bp.route('/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    from app.models.comment import Comment
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    pagination = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.desc()).paginate(
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

@bp.route('/<int:post_id>/comments', methods=['POST'])
def create_comment(post_id):
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
            
        # Verify post exists
        post = Post.query.get_or_404(post_id)
        
        from app.models.comment import Comment
        comment = Comment(
            content=content,
            user_id=user_id,
            post_id=post_id
        )
        
        db.session.add(comment)
        db.session.commit()
        
        return jsonify(comment.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:post_id>/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(post_id, comment_id):
    from app.models.comment import Comment
    comment = Comment.query.get_or_404(comment_id)
    
    if comment.post_id != post_id:
        return jsonify({'error': 'Comment does not belong to this post'}), 400
    
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({'message': 'Comment deleted successfully'}), 200

# Like Routes

@bp.route('/<int:post_id>/like', methods=['POST'])
def toggle_like(post_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
            
        user_id = data.get('userId')
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
            
        # Verify post exists
        post = Post.query.get_or_404(post_id)
        
        # Check if already liked
        existing_like = Like.query.filter_by(post_id=post_id, user_id=str(user_id)).first()
        
        if existing_like:
            # Unlike
            db.session.delete(existing_like)
            post.likes = max(0, post.likes - 1)
            liked = False
        else:
            # Like
            new_like = Like(post_id=post_id, user_id=str(user_id))
            db.session.add(new_like)
            post.likes += 1
            liked = True
            
        db.session.commit()
        
        return jsonify({
            'liked': liked, 
            'likes': post.likes,
            'message': 'Post liked' if liked else 'Post unliked'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

