from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import json, requests
from app import db
from app.models.ad import Ad
from app.models.ad_asset import AdAsset
from app.services.s3_service import S3Service
from app.services.bedrock_service import BedrockService
from app.config import Config
from app.models.user import User
from datetime import datetime
import io
import zipfile

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
        
        # Add image previews to the analysis result
        for asset in ad.assets:
            if asset.type == 'image':
                image_url = asset.s3_url
                # Add image preview URL to the analysis result
                if 'images' not in analysis_result:
                    analysis_result['images'] = []
                analysis_result['images'].append({
                    'url': image_url,
                    'issues': asset.image_analysis.get('concerns', []) if asset.image_analysis else [],
                    'compliance_score': asset.overall_status.get('confidence_score', 0) if asset.overall_status else 0
                })
        
        return jsonify({
            'status': 'success',
            'ad_id': ad.id,
            'analysis': analysis_result
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@api.route('/analyze-batch', methods=['POST'])
def analyze_batch():
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
        
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file'}), 400

        # Extract all folders from the zip
        batch_folders = s3_service.extract_batch_zip_contents(file)
        
        # Prepare batch data
        batch_data = []
        job_name = f"batch-{int(datetime.utcnow().timestamp())}"
        
        # Process each folder and prepare data
        for folder_name, files_data in batch_folders.items():
            try:
                # Create new ad record for each folder
                ad = Ad(
                    company_name=data.get('companyName'),
                    company_description=data.get('companyDescription'),
                    company_category=data.get('companyCategory'),
                    processing_type=data.get('processingType'),
                    custom_compliance=data.get('customCompliance'),
                    batch_count=data.get('batchCount'),
                    user_id=user_id,
                    batch_folder=folder_name
                )
                db.session.add(ad)
                db.session.flush()

                # Process files
                ad_details = None
                images_data = []
                
                for filename, file_data in files_data.items():
                    asset_type = 'text' if filename.endswith('.txt') else 'image'
                    
                    asset = AdAsset(
                        ad_id=ad.id,
                        type=asset_type,
                        s3_url=file_data['s3_url'],
                        status='processing'
                    )
                    db.session.add(asset)
                    
                    if asset_type == 'text' and file_data['content']:
                        ad_details = file_data['content'].decode('utf-8')
                    elif asset_type == 'image':
                        images_data.append(file_data['s3_url'])

                batch_data.append({
                    'folder': folder_name,
                    'ad_id': ad.id,
                    'ad_details': ad_details or f"Test ad details for {folder_name}",
                    'images_data': images_data
                })
                
            except Exception as folder_error:
                print(f"Error processing folder {folder_name}: {str(folder_error)}")
                continue
        
        # Create batch job
        job_arn = bedrock_service.create_batch_job(batch_data, job_name)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'job_arn': job_arn,
            'job_name': job_name
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

@api.route('/batch-status/<job_arn>', methods=['GET'])
def get_batch_status(job_arn):
    try:
        status = bedrock_service.get_batch_job_status(job_arn)
        return jsonify({
            'status': 'success',
            'job_status': status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/batch-results/<job_name>', methods=['GET'])
def get_batch_results(job_name):
    try:
        results = bedrock_service.get_batch_results(job_name)
        return jsonify({
            'status': 'success',
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/download-report/<int:ad_id>', methods=['GET'])
def download_report(ad_id):
    try:
        ad = Ad.query.get(ad_id)
        if not ad:
            return jsonify({'error': 'Ad not found'}), 404

        # Create report data
        report_data = {
            'ad_details': {
                'company_name': ad.company_name,
                'company_description': ad.company_description,
                'company_category': ad.company_category,
                'processing_type': ad.processing_type,
                'created_at': ad.created_at.isoformat()
            },
            'assets': []
        }

        for asset in ad.assets:
            asset_data = {
                'type': asset.type,
                'status': asset.status,
                'compliance': asset.compliance,
                'overall_status': asset.overall_status,
                'text_analysis': asset.text_analysis,
                'image_analysis': asset.image_analysis
            }
            report_data['assets'].append(asset_data)

        # Create PDF or JSON report
        memory_file = io.BytesIO()
        json.dump(report_data, memory_file, indent=2)
        memory_file.seek(0)

        return send_file(
            memory_file,
            mimetype='application/json',
            as_attachment=True,
            download_name=f'ad_analysis_report_{ad_id}.json'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/download-files/<int:ad_id>', methods=['GET'])
def download_files(ad_id):
    try:
        ad = Ad.query.get(ad_id)
        if not ad:
            return jsonify({'error': 'Ad not found'}), 404

        # Create a ZIP file containing all assets
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            # Add report
            report_data = {
                'analysis': {
                    'ad_details': ad.assets[0].ad_details if ad.assets else None,
                    'compliance': ad.assets[0].compliance if ad.assets else None,
                    'overall_status': ad.assets[0].overall_status if ad.assets else None
                }
            }
            zf.writestr('report.json', json.dumps(report_data, indent=2))

            # Add asset files
            for asset in ad.assets:
                if asset.s3_url:
                    file_content = s3_service.download_file(asset.s3_url)
                    filename = asset.s3_url.split('/')[-1]
                    zf.writestr(filename, file_content)

        memory_file.seek(0)
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'ad_analysis_files_{ad_id}.zip'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500 