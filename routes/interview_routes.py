import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from services.resume_service import get_session
from services.question_service import QuestionService
from services.evaluation_service import EvaluationService
from werkzeug.utils import secure_filename

interview_bp = Blueprint('interview', __name__)

question_svc = QuestionService()
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

@interview_bp.route('/submit_answer', methods=['POST'])
def submit_answer():
    """
    Stores the candidate's text answer without evaluation.
    Evaluation happens once after all 20 questions are completed.
    """
    data = request.json
    session_id = data.get('session_id')
    answer = data.get('answer')
    
    session = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    # Store the answer
    session['answers'].append(answer)
    
    return jsonify({"status": "success"})

@interview_bp.route('/next', methods=['POST'])
def next_question():
    data = request.json
    session_id = data.get('session_id')
    
    session = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    session['current_question_index'] += 1
    
    return jsonify({"status": "success"})

@interview_bp.route('/evaluate_batch', methods=['POST'])
def evaluate_batch():
    """
    Evaluates all 20 answers in a single API call after the interview is complete.
    """
    data = request.json
    session_id = data.get('session_id')
    
    session = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    # Check if we have all 20 answers
    if len(session['answers']) != len(session['questions']):
        return jsonify({"error": "Not all answers have been submitted"}), 400
    
    # Prepare question-answer pairs
    questions_and_answers = []
    for i, question in enumerate(session['questions']):
        questions_and_answers.append((question['question'], session['answers'][i]))
    
    # Call batch evaluation
    evaluation_result = eval_svc.evaluate_batch(questions_and_answers)
    if not evaluation_result:
        return jsonify({"error": "Failed to evaluate answers"}), 500
    
    # Store the batch evaluation results
    session['evaluations'] = evaluation_result
    
    return jsonify(evaluation_result)

@interview_bp.route('/report/<session_id>', methods=['GET'])
def get_report(session_id):
    session = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    evaluations = session.get('evaluations')
    if not evaluations or 'results' not in evaluations:
        return jsonify({"error": "No evaluations found"}), 400
    
    results = evaluations['results']
    total_score = sum(result.get('score', 0) for result in results)
    average_score = total_score / len(results) if results else 0
    
    return jsonify({
        "overall_score": int(average_score),
        "total_questions": len(session['questions']),
        "results": results
    })
