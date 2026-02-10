from app.extensions import db
from datetime import datetime

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), nullable=False)
    user_handle = db.Column(db.String(50), nullable=False)
    user_image = db.Column(db.String(255), nullable=True)  # URL or path for user avatar
    is_verified = db.Column(db.Boolean, default=False)
    post_image = db.Column(db.String(255), nullable=True)  # URL or path for post content image
    description = db.Column(db.Text, nullable=True)
    hashtags = db.Column(db.String(255), nullable=True)
    likes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'userName': self.user_name,
            'userHandle': self.user_handle,
            'userImage': self.user_image,
            'isVerified': self.is_verified,
            'postImage': self.post_image,
            'description': self.description,
            'hashtags': self.hashtags,
            'likes': self.likes,
            'createdAt': self.created_at.isoformat()
        }
