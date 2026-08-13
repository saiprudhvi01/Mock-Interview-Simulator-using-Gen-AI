import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')
    
    # API Configurations
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Upload Configurations
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 16 MB limit
    ALLOWED_EXTENSIONS = {'pdf'}
