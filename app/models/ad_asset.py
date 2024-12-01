from datetime import datetime
from app import db
import json

class AdAsset(db.Model):
    __tablename__ = 'ad_assets'
    
    id = db.Column(db.Integer, primary_key=True)
    ad_id = db.Column(db.Integer, db.ForeignKey('ads.id'), nullable=False)
    type = db.Column(db.String(50))  # 'image', 'text', etc.
    s3_url = db.Column(db.String(512))
    status = db.Column(db.String(50), default='processing')  # processing, processed, error
    
    # Analysis data columns (stored as JSON strings)
    _ad_details = db.Column('ad_details', db.Text)
    _image_analysis = db.Column('image_analysis', db.Text)
    _text_analysis = db.Column('text_analysis', db.Text)
    _compliance = db.Column('compliance', db.Text)
    _overall_status = db.Column('overall_status', db.Text)
    _complaince_score_with_facebook = db.Column('complaince_score_with_facebook', db.Float)
    _complaince_score_with_instagram = db.Column('complaince_score_with_instagram', db.Float)
    _complaince_score_with_youtube = db.Column('complaince_score_with_youtube', db.Float)
    _complaince_text_summary_with_facebook = db.Column('complaince_text_summary_with_facebook', db.Text)
    _complaince_text_summary_with_instagram = db.Column('complaince_text_summary_with_instagram', db.Text)
    _complaince_text_summary_with_youtube = db.Column('complaince_text_summary_with_youtube', db.Text)
    
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Property getters and setters for JSON fields
    @property
    def ad_details(self):
        return json.loads(self._ad_details) if self._ad_details else None

    @ad_details.setter
    def ad_details(self, value):
        self._ad_details = json.dumps(value) if value else None

    @property
    def image_analysis(self):
        return json.loads(self._image_analysis) if self._image_analysis else None

    @image_analysis.setter
    def image_analysis(self, value):
        self._image_analysis = json.dumps(value) if value else None

    @property
    def text_analysis(self):
        return json.loads(self._text_analysis) if self._text_analysis else None

    @text_analysis.setter
    def text_analysis(self, value):
        self._text_analysis = json.dumps(value) if value else None

    @property
    def compliance(self):
        return json.loads(self._compliance) if self._compliance else None

    @compliance.setter
    def compliance(self, value):
        self._compliance = json.dumps(value) if value else None

    @property
    def overall_status(self):
        return json.loads(self._overall_status) if self._overall_status else None

    @overall_status.setter
    def overall_status(self, value):
        self._overall_status = json.dumps(value) if value else None 