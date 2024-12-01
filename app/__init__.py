from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.extensions import db, migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # CORS configuration
    CORS(app, 
        resources={r"/*": {
            "origins": ["http://127.0.0.1:5173", "http://localhost:5173"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "expose_headers": ["Content-Range", "X-Content-Range"]
        }}
    )
    
    # Configure your database URL here
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Import and register blueprints
    from app.routes.api import api
    from app.routes.auth import auth_bp
    
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    return app 