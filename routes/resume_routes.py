from flask import Blueprint, request, jsonify, current_app
from services.resume_service import process_resume_upload

resume_bp = Blueprint('resume', __name__)

@resume_bp.route('/upload', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({"message": "No resume file provided"}), 400
        
    file = request.files['resume']
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    
    result, status_code = process_resume_upload(file, upload_folder, allowed_extensions)
    
    if "error" in result:
        return jsonify({"message": result["error"]}), status_code
        
    return jsonify(result), status_code
