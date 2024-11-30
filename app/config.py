import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
    S3_BUCKET = os.getenv('S3_BUCKET')
    
    # Bedrock settings
    BEDROCK_MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    
    # File settings
    ALLOWED_EXTENSIONS = {'zip'}
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size