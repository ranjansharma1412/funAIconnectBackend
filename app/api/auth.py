from flask import Blueprint, jsonify

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['POST'])
def login():
    return jsonify({'message': 'Login endpoint placeholder'})

@bp.route('/register', methods=['POST'])
def register():
    return jsonify({'message': 'Register endpoint placeholder'})
