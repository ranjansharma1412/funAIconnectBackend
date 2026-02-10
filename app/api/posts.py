from flask import Blueprint, request, jsonify, current_app, send_from_directory, url_for
from app.extensions import db
from app.models.post import Post
from app.utils import save_image
import os

bp = Blueprint('posts', __name__)

@bp.route('/', methods=['GET'])
def get_posts():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    posts_query = Post.query.order_by(Post.created_at.desc())
    posts_pagination = posts_query.paginate(page=page, per_page=per_page, error_out=False)
    
    posts = [post.to_dict() for post in posts_pagination.items]
    
    return jsonify({
        'posts': posts,
        'has_next': posts_pagination.has_next,
        'has_prev': posts_pagination.has_prev,
        'total': posts_pagination.total,
        'pages': posts_pagination.pages
    }), 200

@bp.route('/<int:id>', methods=['GET'])
def get_post(id):
    post = Post.query.get_or_404(id)
    return jsonify(post.to_dict())

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
