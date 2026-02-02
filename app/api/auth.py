from flask import Blueprint, request, jsonify, current_app
import jwt
from datetime import datetime, timedelta
from functools import wraps

bp = Blueprint('auth', __name__)

# Simple in-memory user storage for demo purposes
# In production, use a proper database with hashed passwords
demo_users = {
    'demo@funai.com': {
        'password': 'demo123',
        'name': 'Demo User'
    }
}

def generate_token(email, name):
    """Generate JWT token for authenticated user"""
    payload = {
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
            request.current_user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
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
    user = demo_users.get(email)
    if not user or user['password'] != password:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Generate token
    token = generate_token(email, user['name'])
    
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': {
            'email': email,
            'name': user['name']
        }
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
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    # Check if user already exists
    if email in demo_users:
        return jsonify({'error': 'User already exists'}), 409
    
    # Create new user
    demo_users[email] = {
        'password': password,
        'name': name
    }
    
    # Generate token
    token = generate_token(email, name)
    
    return jsonify({
        'message': 'Registration successful',
        'token': token,
        'user': {
            'email': email,
            'name': name
        }
    }), 201

@bp.route('/verify', methods=['GET'])
@token_required
def verify_token():
    """Verify if token is valid"""
    return jsonify({
        'message': 'Token is valid',
        'user': request.current_user
    }), 200
