from app import db
from datetime import datetime

class ImageData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    s3_path = db.Column(db.String(512), nullable=False)
    analysis_result = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            's3_path': self.s3_path,
            'analysis_result': self.analysis_result,
            'created_at': self.created_at.isoformat()
        } 