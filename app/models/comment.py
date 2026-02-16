from app.extensions import db
from datetime import datetime

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('comments', lazy=True))
    post = db.relationship('Post', backref=db.backref('comments', lazy=True, cascade="all, delete-orphan"))

    def to_dict(self):
        # Handle user relationship safely
        user_name = ""
        user_handle = ""
        user_image = ""
        user_params = None
        
        if self.user:
            user_name = self.user.full_name or self.user.username
            user_handle = self.user.username
            user_image = self.user.user_image
            user_params = {
                'id': self.user.id,
                'name': user_name,
                'username': user_handle,
                'image': user_image
            }

        return {
            'id': self.id,
            'content': self.content,
            'userId': self.user_id,
            'postId': self.post_id,
            'userName': user_name,
            'userHandle': user_handle,
            'userImage': user_image,
            'userParams': user_params,
            'createdAt': self.created_at.isoformat()
        }
