import os
import uuid
from werkzeug.utils import secure_filename
from utils.pdf_utils import extract_text_from_pdf

# In-memory store for MVP (session_id -> data)
# In production, use Redis or a Database
SESSIONS = {}

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
            SESSIONS[session_id] = {
                "resume_text": extracted_text,
                "questions": [],
                "current_question_index": 0,
                "answers": [],  # Stores text answers only
                "evaluations": None,  # Will store batch evaluation results after interview
                "difficulty_level": None,  # Will be set by user
                "resume_analysis": None  # Will store resume analysis results
            }
            
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
    return SESSIONS.get(session_id)
