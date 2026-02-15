from flask import Blueprint, request, jsonify, current_app
import jwt
from datetime import datetime, timedelta
from functools import wraps
from app.extensions import db
from app.models.user import User
from app.utils import save_image

bp = Blueprint('auth', __name__)

def generate_token(user_id, email, full_name, username):
    """Generate JWT token for authenticated user"""
    payload = {
        'id': user_id,
        'email': email,
        'name': full_name,
        'username': username,
        'exp': datetime.utcnow() + timedelta(days=1),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    return token

def token_required(f):
    """Decorator to protect routes that require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['id']) # Find user by ID in DB
            if not current_user:
                 return jsonify({'error': 'User not found'}), 401

            request.current_user = current_user
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

@bp.route('/login', methods=['POST'])
def login():
    """Login endpoint - returns JWT token"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    identifier = data.get('identifier') # email or username
    
    # Fallback to email if identifier is not provided (for backward compatibility)
    if not identifier:
        identifier = data.get('email')

    # Also fallback to username if identifier is not provided (for consistency)
    if not identifier:
        identifier = data.get('username')
        
    password = data.get('password')
    
    if not identifier or not password:
        return jsonify({'error': 'Identifier (email or username) and password are required'}), 400
    
    # Check credentials
    user = User.query.filter((User.email == identifier) | (User.username == identifier)).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Generate token
    token = generate_token(user.id, user.email, user.full_name, user.username)
    
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': user.to_dict()
    }), 200

@bp.route('/register', methods=['POST'])
def register():
    """Register endpoint - creates new user and returns JWT token"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name') or data.get('name', 'User')
    username = data.get('username')
    mobile = data.get('mobile') # Optional
    
    if not email or not password or not username:
        return jsonify({'error': 'Email, password and username are required'}), 400
    
    # Check if email already exists
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email is already registered'}), 409

    # Check if username already exists
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username is already taken'}), 409
    
    # Create new user
    new_user = User(email=email, full_name=full_name, username=username, mobile=mobile)
    new_user.set_password(password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500
    
    # Generate token
    token = generate_token(new_user.id, new_user.email, new_user.full_name, new_user.username)
    
    return jsonify({
        'message': 'Registration successful',
        'token': token,
        'user': new_user.to_dict()
    }), 201

@bp.route('/verify', methods=['GET'])
@token_required
def verify_token():
    """Verify if token is valid"""
    return jsonify({
        'message': 'Token is valid',
        'user': request.current_user.to_dict()
    }), 200

@bp.route('/profile', methods=['PUT'])
@token_required
def update_profile():
    """Update user profile: Full Name, Username, Mobile, Bio, DOB, Image and Email"""
    user = request.current_user
    
    # Handle multipart/form-data
    data = request.form
    file = request.files.get('userImage')

    email = data.get('email')
    full_name = data.get('full_name') or data.get('name')
    username = data.get('username')
    mobile = data.get('mobile')
    bio = data.get('bio')
    dob = data.get('dob')
    
    if email:
        return jsonify({'error': 'Email cannot be updated'}), 400

    if username:
        # Check if username is already taken by another user
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user.id:
            return jsonify({'error': 'Username already in use'}), 409
        user.username = username

    if full_name:
        user.full_name = full_name
        
    if mobile:
        user.mobile = mobile
        
    if bio:
        user.bio = bio
        
    if dob:
        user.dob = dob

    if file:
        image_url = save_image(file)
        if image_url:
            user.user_image = image_url

    try:
        db.session.commit()
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile'}), 500


@bp.route('/check-username', methods=['POST'])
def check_username():
    """Check if username is available"""
    data = request.get_json()
    username = data.get('username')
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'available': False, 'message': 'Username is already taken'}), 200
    
    return jsonify({'available': True, 'message': 'Username is available'}), 200

@bp.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """Change user password"""
    data = request.get_json()
    user = request.current_user
    
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({'error': 'Old and new passwords are required'}), 400
        
    if not user.check_password(old_password):
        return jsonify({'error': 'Invalid old password'}), 401
        
    user.set_password(new_password)
    
    try:
        db.session.commit()
        return jsonify({'message': 'Password updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update password'}), 500

@bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Generate reset token for forgot password"""
    data = request.get_json()
    email = data.get('email')
    
    if not email:
         return jsonify({'error': 'Email is required'}), 400
         
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    # Generate reset token (valid for 15 mins)
    payload = {
        'reset_id': user.id,
        'exp': datetime.utcnow() + timedelta(minutes=15),
        'iat': datetime.utcnow()
    }
    reset_token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    
    # Generate HTTP link that redirects to Custom Scheme
    # This ensures email clients (Gmail) don't block the link
    base_url = request.host_url.rstrip('/')
    reset_link = f"{base_url}/api/auth/reset-password-redirect/{reset_token}"
    
    return jsonify({
        'message': 'Reset token generated successfully',
        'reset_token': reset_token,
        'reset_link': reset_link
    }), 200

@bp.route('/reset-password-redirect/<token>', methods=['GET'])
def reset_password_redirect(token):
    """Serve HTML page to redirect to custom scheme"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Redirecting...</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script>
            window.onload = function() {{
                window.location.href = "funai://reset-password/{token}";
                
                // Fallback: If custom scheme fails (e.g. desktop), show message
                setTimeout(function() {{
                    document.getElementById('message').innerText = "If the app didn't open, please ensure FunAI Connect is installed.";
                }}, 2000);
            }};
        </script>
    </head>
    <body style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; font-family: sans-serif; background-color: #f5f5f5; text-align: center; padding: 20px;">
        <h2 style="color: #333;">Redirecting to FunAI Connect...</h2>
        <p id="message" style="color: #666; margin-bottom: 20px;">Please wait while we open the app.</p>
        <a href="funai://reset-password/{token}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">Open App Manually</a>
    </body>
    </html>
    """
    return html

@bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password using token"""
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')
    
    if not token or not new_password:
        return jsonify({'error': 'Token and new password are required'}), 400
        
    try:
        if token.startswith('Bearer '):
                token = token[7:]
                
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = data.get('reset_id')
        
        if not user_id:
             return jsonify({'error': 'Invalid reset token'}), 400
             
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({'message': 'Password reset successfully'}), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to reset password'}), 500
