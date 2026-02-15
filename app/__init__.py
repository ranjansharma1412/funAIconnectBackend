from flask import Flask
from config import Config
from app.extensions import db, migrate, cors

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    # Register Blueprints
    from app.api.main import bp as main_bp
    app.register_blueprint(main_bp, url_prefix='/api')

    from app.api.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from app.api.posts import bp as posts_bp
    app.register_blueprint(posts_bp, url_prefix='/api/posts')

    from app.api.image import bp as image_bp
    app.register_blueprint(image_bp, url_prefix='/api/image')

    return app
