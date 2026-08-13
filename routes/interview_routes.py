import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from services.resume_service import get_session
from services.question_service import QuestionService
from services.speech_service import SpeechService
from services.evaluation_service import EvaluationService
from werkzeug.utils import secure_filename

interview_bp = Blueprint('interview', __name__)

question_svc = QuestionService()
speech_svc = SpeechService()
eval_svc = EvaluationService()

@interview_bp.route('/generate', methods=['POST'])
def generate_questions():
    data = request.json
    session_id = data.get('session_id')
    
    session = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    if not session['questions']:
        questions = question_svc.generate_questions(session['resume_text'])
        if not questions:
            return jsonify({"error": "Failed to generate questions"}), 500
        session['questions'] = questions
        
    return jsonify({"questions": session['questions'], "total": len(session['questions'])})

@interview_bp.route('/question/<session_id>', methods=['GET'])
def get_current_question(session_id):
    session = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    idx = session['current_question_index']
    if idx >= len(session['questions']):
        return jsonify({"status": "completed"})
        
    question = session['questions'][idx]
    return jsonify({
        "question": question,
        "current_index": idx + 1,
        "total": len(session['questions'])
    })

@interview_bp.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
        
    file = request.files['audio']
    filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    try:
        file.save(filepath)
        transcript = speech_svc.transcribe(filepath)
        if not transcript:
            return jsonify({"error": "Failed to transcribe audio"}), 500
            
        return jsonify({"transcript": transcript})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass

@interview_bp.route('/evaluate', methods=['POST'])
def evaluate_answer():
    data = request.json
    session_id = data.get('session_id')
    question_text = data.get('question')
    answer = data.get('answer')
    
    session = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    evaluation = eval_svc.evaluate_answer(session['resume_text'], question_text, answer)
    if not evaluation:
        return jsonify({"error": "Failed to evaluate answer"}), 500
        
    # Save the answer and evaluation for the final report
    session['answers'].append(answer)
    session['evaluations'].append(evaluation)
    
    return jsonify(evaluation)

@interview_bp.route('/next', methods=['POST'])
def next_question():
    data = request.json
    session_id = data.get('session_id')
    
    session = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    session['current_question_index'] += 1
    
    return jsonify({"status": "success"})

@interview_bp.route('/report/<session_id>', methods=['GET'])
def get_report(session_id):
    session = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    evaluations = session['evaluations']
    if not evaluations:
        return jsonify({"error": "No evaluations found"}), 400
        
    total_score = sum(ev.get('score', 0) for ev in evaluations)
    average_score = total_score / len(evaluations) if evaluations else 0
    
    return jsonify({
        "overall_score": int(average_score),
        "total_questions": len(session['questions']),
        "evaluations": evaluations
    })
