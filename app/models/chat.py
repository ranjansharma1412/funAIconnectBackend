from app.extensions import db
from datetime import datetime

class Conversation(db.Model):
    __tablename__ = 'conversation'
    
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships to easily access the User objects
    user1 = db.relationship('User', foreign_keys=[user1_id])
    user2 = db.relationship('User', foreign_keys=[user2_id])
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        latest_message = self.messages.order_by(Message.created_at.desc()).first()
        return {
            'id': self.id,
            'user1': self.user1.to_dict() if self.user1 else None,
            'user2': self.user2.to_dict() if self.user2 else None,
            'createdAt': self.created_at.isoformat(),
            'updatedAt': self.updated_at.isoformat(),
            'latestMessage': latest_message.to_dict() if latest_message else None
        }

class Message(db.Model):
    __tablename__ = 'message'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    text = db.Column(db.Text, nullable=True)
    media_url = db.Column(db.String(500), nullable=True)
    media_type = db.Column(db.String(50), nullable=True) # 'image', 'video', 'document'
    
    status = db.Column(db.String(20), default='sent') # 'sent', 'delivered', 'read', 'deleted'
    is_deleted = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        # Format time to HH:MM locally or leave as ISO for frontend to format
        return {
            'id': str(self.id),
            'conversationId': self.conversation_id,
            'senderId': self.sender_id,
            'text': self.text if not self.is_deleted else "This message was deleted.",
            'mediaUrl': self.media_url if not self.is_deleted else None,
            'mediaType': self.media_type,
            'status': self.status if not self.is_deleted else 'deleted',
            'isDeleted': self.is_deleted,
            'createdAt': self.created_at.isoformat(),
            'time': self.created_at.strftime('%H:%M')
        }
