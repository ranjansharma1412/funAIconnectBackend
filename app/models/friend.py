from app.extensions import db
from datetime import datetime

class Friend(db.Model):
    __tablename__ = 'friend'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending') # 'pending', 'accepted'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships are handled on the User model side or queried directly
    # We define relationships in the Friend model to easily access the User objects
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('sent_friend_requests', lazy='dynamic'))
    friend = db.relationship('User', foreign_keys=[friend_id], backref=db.backref('received_friend_requests', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'friendId': self.friend_id,
            'status': self.status,
            'createdAt': self.created_at.isoformat(),
            'user': self.user.to_dict() if self.user else None,
            'friend_user': self.friend.to_dict() if self.friend else None
        }
