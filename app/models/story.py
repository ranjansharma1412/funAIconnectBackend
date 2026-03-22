from app.extensions import db
from datetime import datetime

class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), nullable=False)
    user_handle = db.Column(db.String(50), nullable=False)
    user_image = db.Column(db.String(255), nullable=True)  # URL or path for user avatar
    is_verified = db.Column(db.Boolean, default=False)
    story_image = db.Column(db.String(255), nullable=True)  # URL or path for story content image
    description = db.Column(db.Text, nullable=True)
    hashtags = db.Column(db.String(255), nullable=True)
    likes_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self, current_user_id=None):
        from app.models.user import User
        from app.models.story_like import StoryLike

        user = User.query.filter_by(username=self.user_handle).first()

        current_user_name = self.user_name
        current_user_image = self.user_image

        if user:
            current_user_name = user.full_name or user.username
            current_user_image = user.user_image or self.user_image

        has_liked = False
        if current_user_id:
            existing_like = StoryLike.query.filter_by(story_id=self.id, user_id=str(current_user_id)).first()
            has_liked = bool(existing_like)

        return {
            'id': self.id,
            'userName': current_user_name,
            'userHandle': self.user_handle,
            'userImage': current_user_image,
            'isVerified': self.is_verified,
            'storyImage': self.story_image,
            'description': self.description,
            'hashtags': self.hashtags,
            'likesCount': self.likes_count,
            'hasLiked': has_liked,
            'createdAt': self.created_at.isoformat() + 'Z'
        }
