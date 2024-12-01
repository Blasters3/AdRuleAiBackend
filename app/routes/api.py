from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from app.services.s3_service import S3Service
from app.services.bedrock_service import BedrockService
from app.config import Config

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
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        print("File received:", file.filename)

        # Extract and upload zip contents
        files_data = s3_service.extract_zip_contents(file)
        
        # Find and parse the ad details text file
        ad_details = None
        images_data = []
        
        for filename, data in files_data.items():
            if filename.endswith('.txt'):
                # check if the file is not empty
                if data['content']:
                    ad_details = data['content'].decode('utf-8')
            elif filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                images_data.append(data['s3_url'])
        
        # if not ad_details:
        #     return jsonify({'error': 'No ad details file found in zip'}), 400
        
        ad_details = """
        This is a test ad details regarding no broker. It is a real state company that is selling a property.
        """

        # Analyze the ad
        analysis_result = bedrock_service.analyze_ad(
            ad_details=ad_details,
            images_data=images_data
        )
        
        print(analysis_result, "analysis result", type(analysis_result))

        return jsonify({
            'status': 'success',
            'analysis': analysis_result
        })

    except Exception as e:
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