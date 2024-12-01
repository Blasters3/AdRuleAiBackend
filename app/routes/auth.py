from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.user import User
from datetime import datetime
import firebase_admin
from firebase_admin import auth, credentials
from flask_cors import cross_origin

auth_bp = Blueprint('auth', __name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate('adruleaiadminsdk.json')
firebase_admin.initialize_app(cred)

@auth_bp.route('/register', methods=['POST', 'OPTIONS'])
@cross_origin(origins=['http://127.0.0.1:5173', 'http://localhost:5173'], 
             methods=['POST', 'OPTIONS'],
             allow_headers=['Content-Type', 'Authorization'],
             supports_credentials=True)
def register_user():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        # Get the ID token from the request
        id_token = request.json.get('idToken')
        if not id_token:
            return jsonify({'error': 'No ID token provided'}), 400
        
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(id_token)
        firebase_uid = decoded_token['uid']
        
        # Check if user already exists
        user = User.query.filter_by(firebase_uid=firebase_uid).first()
        
        if user:
            # Update last login time
            user.last_login = datetime.utcnow()
        else:
            # Create new user
            user = User(
                firebase_uid=firebase_uid,
                email=decoded_token.get('email'),
                display_name=decoded_token.get('name'),
                photo_url=decoded_token.get('picture')
            )
            db.session.add(user)
            
        db.session.commit()
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 