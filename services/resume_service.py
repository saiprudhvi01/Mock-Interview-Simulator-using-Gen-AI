import os
import uuid
import json
from werkzeug.utils import secure_filename
from utils.pdf_utils import extract_text_from_pdf
from flask import current_app

# Persistent session storage using SQLite
def get_session_db():
    """Get or create the session database connection"""
    if not hasattr(current_app, '_session_db'):
        import sqlite3
        db_path = os.path.join(current_app.root_path, 'sessions.db')
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # Create table if not exists
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        current_app._session_db = conn
    return current_app._session_db

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def process_resume_upload(file, upload_folder, allowed_extensions):
    if file.filename == '':
        return {"error": "No selected file"}, 400
        
    if file and allowed_file(file.filename, allowed_extensions):
        filename = secure_filename(file.filename)
        
        # We append a uuid to make it unique and prevent overwrites
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(upload_folder, unique_filename)
        
        try:
            file.save(filepath)
            
            # Extract text
            extracted_text = extract_text_from_pdf(filepath)
            
            if not extracted_text:
                return {"error": "Could not extract text from the PDF"}, 400
            
            # Create session
            session_id = str(uuid.uuid4())
            session_data = {
                "resume_text": extracted_text,
                "questions": [],
                "current_question_index": 0,
                "answers": [],  # Stores text answers only
                "evaluations": None,  # Will store batch evaluation results after interview
                "difficulty_level": None,  # Will be set by user
                "resume_analysis": None  # Will store resume analysis results
            }
            
            # Save to persistent storage
            db = get_session_db()
            db.execute(
                'INSERT INTO sessions (session_id, data) VALUES (?, ?)',
                (session_id, json.dumps(session_data))
            )
            db.commit()
            
            return {"session_id": session_id, "message": "Resume uploaded successfully"}, 200
            
        except Exception as e:
            return {"error": str(e)}, 500
        finally:
            # Clean up the temporary file
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
    
    return {"error": "Invalid file type. Only PDF is allowed."}, 400

def get_session(session_id):
    """Get session from persistent storage"""
    try:
        db = get_session_db()
        cursor = db.execute('SELECT data FROM sessions WHERE session_id = ?', (session_id,))
        row = cursor.fetchone()
        if row:
            return json.loads(row['data'])
        return None
    except Exception as e:
        print(f"Error getting session: {e}")
        return None

def update_session(session_id, session_data):
    """Update session in persistent storage"""
    try:
        db = get_session_db()
        db.execute(
            'UPDATE sessions SET data = ? WHERE session_id = ?',
            (json.dumps(session_data), session_id)
        )
        db.commit()
    except Exception as e:
        print(f"Error updating session: {e}")

def delete_session(session_id):
    """Delete session from persistent storage"""
    try:
        db = get_session_db()
        db.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
        db.commit()
    except Exception as e:
        print(f"Error deleting session: {e}")

def cleanup_old_sessions(hours=24):
    """Delete sessions older than specified hours"""
    try:
        db = get_session_db()
        db.execute(
            'DELETE FROM sessions WHERE created_at < datetime("now", ?)',
            (f'-{hours} hours',)
        )
        deleted = db.rowcount
        db.commit()
        print(f"Cleaned up {deleted} old sessions (older than {hours} hours)")
        return deleted
    except Exception as e:
        print(f"Error cleaning up old sessions: {e}")
        return 0
