import os
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from config.config import Config

# Initialize App
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

from routes.resume_routes import resume_bp
from routes.interview_routes import interview_bp
app.register_blueprint(resume_bp, url_prefix='/api/resume')
app.register_blueprint(interview_bp, url_prefix='/api/interview')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/interview')
def interview():
    return render_template('interview.html')

@app.route('/report')
def report():
    # Report is now handled by resume_routes.py
    from flask import request, redirect
    session_id = request.args.get('session_id')
    if session_id:
        return redirect(f'/api/resume/report?session_id={session_id}')
    return redirect('/')

@app.route('/api/health')
def health_check():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
