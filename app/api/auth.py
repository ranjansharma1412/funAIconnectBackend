from flask import Blueprint, request, jsonify, current_app
import jwt
from datetime import datetime, timedelta
from functools import wraps
from app.extensions import db
from app.models.user import User
from app.utils import save_image

bp = Blueprint('auth', __name__)

def generate_token(user_id, email, name):
    """Generate JWT token for authenticated user"""
    payload = {
        'id': user_id,
        'email': email,
        'name': name,
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
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    # Check credentials
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Generate token
    token = generate_token(user.id, user.email, user.name)
    
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
    name = data.get('name', 'User')
    mobile = data.get('mobile') # Optional
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    # Check if user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'User already exists'}), 409
    
    # Create new user
    new_user = User(email=email, name=name, mobile=mobile)
    new_user.set_password(password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500
    
    # Generate token
    token = generate_token(new_user.id, new_user.email, new_user.name)
    
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
    """Update user profile: Name, Mobile, Bio, DOB, Image and Email"""
    user = request.current_user
    
    # Handle multipart/form-data
    data = request.form
    file = request.files.get('userImage')

    email = data.get('email')
    name = data.get('name')
    mobile = data.get('mobile')
    bio = data.get('bio')
    dob = data.get('dob')
    
    if email:
         # Check if email is already taken by another user
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user.id:
            return jsonify({'error': 'Email already in use'}), 409
        user.email = email

    if name:
        user.name = name
        
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
