from app.extensions import db
from datetime import datetime

class StoryLike(db.Model):
    __tablename__ = 'story_likes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False) # Maps to User.username or User.id, depending on auth
    story_id = db.Column(db.Integer, db.ForeignKey('story.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Ensure a user can only like a particular story once
    __table_args__ = (
        db.UniqueConstraint('user_id', 'story_id', name='unique_user_story_like'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'story_id': self.story_id,
            'created_at': self.created_at.isoformat()
        }
