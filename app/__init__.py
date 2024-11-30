from flask import Flask
from app.routes.api import api
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Register blueprints
    app.register_blueprint(api, url_prefix='/api')
    
    return app 