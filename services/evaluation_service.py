import requests
import json
from flask import current_app

class EvaluationService:
    def __init__(self):
        self.model = "gemini-3.5-flash"

    def evaluate_answer(self, resume_text, question, answer):
        """
        Sends context and answer to Gemini API for evaluation.
        Returns a dict with score, rating, feedback, etc.
        """
        api_key = current_app.config.get('GEMINI_API_KEY')
        
        if not api_key:
            print("WARNING: GEMINI_API_KEY not set. Returning mock evaluation.")
            return {
                "score": 85,
                "rating": "Good",
                "feedback": "Mock Feedback.",
                "strengths": ["Mock Strength"],
                "improvements": ["Mock Improvement"],
                "suggested_answer": "Mock suggested answer"
            }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={api_key}"
        
        prompt = f"""
        Evaluate the candidate's answer against the interview question and the candidate's resume.
        
        Candidate Resume:
        {resume_text}
        
        Interview Question:
        {question}
        
        Candidate Answer:
        {answer}
        
        Return ONLY a structured JSON object. Do NOT wrap it in markdown block quotes (```json ... ```).
        It must contain exactly these keys:
        - "score" (integer from 0 to 100)
        - "rating" (string: Poor, Fair, Good, Excellent)
        - "feedback" (string: overall feedback)
        - "strengths" (array of strings)
        - "improvements" (array of strings)
        - "suggested_answer" (string: an improved answer consistent with the resume)
        """
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        try:
            response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            content = data['candidates'][0]['content']['parts'][0]['text']
            
            # Clean up markdown JSON wrapper
            content = content.strip()
            if content.startswith("```json"): content = content[7:]
            if content.startswith("```"): content = content[3:]
            if content.endswith("```"): content = content[:-3]
            
            evaluation = json.loads(content.strip())
            return evaluation
            
        except Exception as e:
            print(f"Error calling Gemini Evaluation API: {e}")
            if 'response' in locals():
                print(f"Response: {response.text}")
            return None
