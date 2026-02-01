from flask import Blueprint, jsonify

bp = Blueprint('main', __name__)

@bp.route('/health')
def health_check():
    return jsonify({'status': 'ok', 'message': 'FunAIConnectBackend is running'})

@bp.route('/')
def index():
    return jsonify({'message': 'Welcome to FunAI Connect API'})
