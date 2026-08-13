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
    return render_template('report.html')

from routes.interview_routes import transcribe_audio
app.add_url_rule('/api/transcribe', 'transcribe_audio', transcribe_audio, methods=['POST'])

@app.route('/api/health')
def health_check():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
