from flask import Blueprint, request, jsonify, current_app, render_template
from services.resume_service import process_resume_upload, get_session

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

@resume_bp.route('/report', methods=['GET'])
def report_page():
    from flask import request
    session_id = request.args.get('session_id')
    
    if not session_id:
        return "Session ID required", 400
    
    # Get the report data by calling the internal function
    from services.resume_service import get_session
    session = get_session(session_id)
    
    if not session:
        return "Session not found", 404
        
    evaluations = session.get('evaluations')
    if not evaluations or 'results' not in evaluations:
        return "No evaluations found. Please complete the interview first.", 400
    
    results = evaluations['results']
    total_score = sum(result.get('score', 0) for result in results)
    average_score = total_score / len(results) if results else 0
    
    report_data = {
        "overall_score": int(average_score),
        "total_questions": len(session['questions']),
        "results": results
    }
    
    return render_template('report.html', report=report_data)
