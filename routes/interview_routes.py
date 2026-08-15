import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from services.resume_service import get_session, update_session
from services.question_service import QuestionService
from services.evaluation_service import EvaluationService
from services.resume_analysis_service import ResumeAnalysisService
from werkzeug.utils import secure_filename

interview_bp = Blueprint('interview', __name__)

question_svc = QuestionService()
eval_svc = EvaluationService()
resume_analysis_svc = ResumeAnalysisService()

@interview_bp.route('/set_difficulty', methods=['POST'])
def set_difficulty():
    """
    Sets the difficulty level, performs resume analysis, and generates questions in a single API call.
    """
    data = request.json
    session_id = data.get('session_id')
    difficulty_level = data.get('difficulty_level')
    
    if difficulty_level not in ['Easy', 'Medium', 'Hard', 'Mixed']:
        return jsonify({"error": "Invalid difficulty level. Must be Easy, Medium, Hard, or Mixed"}), 400
    
    session = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    # Set difficulty level
    session['difficulty_level'] = difficulty_level
    
    # Perform resume analysis
    resume_analysis = resume_analysis_svc.analyze_resume(session['resume_text'])
    if resume_analysis:
        session['resume_analysis'] = resume_analysis
    
    # Generate questions in the same call
    if not session['questions']:
        questions = question_svc.generate_questions(session['resume_text'], difficulty_level)
        if not questions:
            return jsonify({"error": "Failed to generate questions"}), 500
        session['questions'] = questions
    
    # Save updated session to persistent storage
    update_session(session_id, session)
    
    return jsonify({
        "status": "success",
        "difficulty_level": difficulty_level,
        "resume_analysis": resume_analysis,
        "questions": session['questions'],
        "total_questions": len(session['questions'])
    })

@interview_bp.route('/generate', methods=['POST'])
def generate_questions():
    data = request.json
    session_id = data.get('session_id')
    
    session = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    # Check if difficulty level is set
    if not session.get('difficulty_level'):
        return jsonify({"error": "Difficulty level not set. Please select difficulty first."}), 400
        
    if not session['questions']:
        difficulty_level = session['difficulty_level']
        questions = question_svc.generate_questions(session['resume_text'], difficulty_level)
        if not questions:
            return jsonify({"error": "Failed to generate questions"}), 500
        session['questions'] = questions
        update_session(session_id, session)
        
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
    update_session(session_id, session)
    
    return jsonify({"status": "success"})

@interview_bp.route('/next', methods=['POST'])
def next_question():
    data = request.json
    session_id = data.get('session_id')
    
    session = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    session['current_question_index'] += 1
    update_session(session_id, session)
    
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
    update_session(session_id, session)
    
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
