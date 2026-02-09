from app.extensions import db
from app.models.post import Post
from run import app

with app.app_context():
    try:
        num_deleted = db.session.query(Post).delete()
        db.session.commit()
        print(f"Successfully deleted {num_deleted} posts.")
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting posts: {e}")
