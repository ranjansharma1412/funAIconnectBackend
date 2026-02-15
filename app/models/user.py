from app.extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    user_image = db.Column(db.String(255), nullable=True) # Cloudinary URL
    mobile = db.Column(db.String(20), nullable=True)
    bio = db.Column(db.String(500), nullable=True)
    dob = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'fullName': self.full_name,
            'userImage': self.user_image,
            'mobile': self.mobile,
            'bio': self.bio,
            'dob': self.dob,
            'createdAt': self.created_at.isoformat()
        }
