from datetime import datetime
from app.extensions import db

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(128), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    display_name = db.Column(db.String(120))
    photo_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'display_name': self.display_name,
            'photo_url': self.photo_url,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat()
        } 
    
    @classmethod
    def get_id_from_firebase_uid(cls, firebase_uid):
        """
        Get user ID from Firebase UID
        Args:
            firebase_uid (str): Firebase user ID
        Returns:
            int: User ID if found, None otherwise
        """
        user = cls.query.filter_by(firebase_uid=firebase_uid).first()
        return user.id if user else None