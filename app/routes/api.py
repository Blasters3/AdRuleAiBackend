from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import json
from app import db
from app.models.ad import Ad
from app.models.ad_asset import AdAsset
from app.services.s3_service import S3Service
from app.services.bedrock_service import BedrockService
from app.config import Config
from app.models.user import User

api = Blueprint('api', __name__)
s3_service = S3Service()
bedrock_service = BedrockService()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@api.route('/')
def index():
    return jsonify({'message': 'Welcome to Airule AI API'})

@api.route('/analyze-ad', methods=['POST'])
def analyze_ad():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        # Get form data
        data = request.form.get('data')
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        data = json.loads(data)
        user_uid = data.get('userId')
        user_id = User.get_id_from_firebase_uid(user_uid) if user_uid else None
        
        # Create new ad record
        ad = Ad(
            company_name=data.get('companyName'),
            company_description=data.get('companyDescription'),
            company_category=data.get('companyCategory'),
            processing_type=data.get('processingType'),
            custom_compliance=data.get('customCompliance'),
            batch_count=data.get('batchCount'),
            user_id=user_id
        )
        db.session.add(ad)
        db.session.flush()  # Get the ad ID without committing
        
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file'}), 400
        
        # Extract and upload zip contents
        files_data = s3_service.extract_zip_contents(file)
        
        # Process files and create asset records
        ad_details = None
        images_data = []
        
        for filename, data in files_data.items():
            asset_type = 'text' if filename.endswith('.txt') else 'image'
            
            asset = AdAsset(
                ad_id=ad.id,
                type=asset_type,
                s3_url=data['s3_url'],
                status='processing'
            )
            db.session.add(asset)
            
            if asset_type == 'text' and data['content']:
                ad_details = data['content'].decode('utf-8')
            elif asset_type == 'image':
                images_data.append(data['s3_url'])
        
        # Use test data if no ad details found
        if not ad_details:
            ad_details = """
            This is a test ad details regarding no broker. It is a real state company that is selling a property.
            """
        
        # Analyze the ad
        analysis_result = bedrock_service.analyze_ad(
            ad_details=ad_details,
            images_data=images_data
        )
        
        # Update assets with analysis results
        for asset in ad.assets:
            if asset.type == 'text':
                asset.ad_details = analysis_result.get('ad_details')
                asset.text_analysis = analysis_result.get('analysis', {}).get('text_analysis')
            elif asset.type == 'image':
                asset.image_analysis = analysis_result.get('analysis', {}).get('image_analysis')
            
            asset.compliance = analysis_result.get('compliance')
            asset.overall_status = analysis_result.get('overall_status')
            asset.status = 'processed'
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'ad_id': ad.id,
            'analysis': analysis_result
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/fix-ad', methods=['POST'])
def fix_ad():
    try:
        data = request.json
        if not data or 'original_analysis' not in data or 'ad_content' not in data:
            return jsonify({'error': 'Missing required data'}), 400

        fixed_ad = bedrock_service.fix_ad(
            original_analysis=data['original_analysis'],
            ad_content=data['ad_content']
        )

        return jsonify({
            'status': 'success',
            'fixed_ad': fixed_ad
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500 