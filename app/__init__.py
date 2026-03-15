from flask import Flask
from config import Config
from app.extensions import db, migrate, cors, socketio

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    socketio.init_app(app)

    # Register socket events
    import app.chat_sockets as chat_sockets

    # Register Blueprints
    from app.api.main import bp as main_bp
    app.register_blueprint(main_bp, url_prefix='/api')

    from app.api.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from app.api.posts import bp as posts_bp
    app.register_blueprint(posts_bp, url_prefix='/api/posts')

    from app.api.image import bp as image_bp
    app.register_blueprint(image_bp, url_prefix='/api/image')

    from app.api.friends import bp as friends_bp
    app.register_blueprint(friends_bp, url_prefix='/api/friends')

    from app.api.stories import bp as stories_bp
    app.register_blueprint(stories_bp, url_prefix='/api/stories')

    from app.api.chat import bp as chat_bp
    app.register_blueprint(chat_bp, url_prefix='/api/chat')

    return app
