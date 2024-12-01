from datetime import datetime
from app.extensions import db
from app.models.user import User  # Add this import

class Ad(db.Model):
    __tablename__ = 'ads'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    company_description = db.Column(db.Text)
    company_category = db.Column(db.String(255))
    processing_type = db.Column(db.String(50))
    custom_compliance = db.Column(db.Boolean, default=False)
    batch_count = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assets = db.relationship('AdAsset', backref='ad', lazy=True) 