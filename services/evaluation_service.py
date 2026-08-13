import requests
import json
from flask import current_app

class EvaluationService:
    def __init__(self):
        # Using flash-lite for evaluation to save API credits
        self.model = "gemini-3.5-flash-lite"

    def evaluate_batch(self, questions_and_answers):
        """
        Evaluates all 20 questions and answers in a single API call.
        Returns a dict with results array containing evaluations for each question.
        """
        api_key = current_app.config.get('GEMINI_API_KEY')
        
        if not api_key:
            print("WARNING: GEMINI_API_KEY not set. Returning mock batch evaluation.")
            # Return mock evaluations for all questions
            results = []
            for i, (question, answer) in enumerate(questions_and_answers, 1):
                results.append({
                    "question_number": i,
                    "question": question,
                    "candidate_answer": answer,
                    "suggested_answer": "Mock suggested answer",
                    "score": 85,
                    "feedback": "Mock feedback."
                })
            return {"results": results}

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={api_key}"
        
        # Build the prompt with all questions and answers
        qa_pairs_text = ""
        for i, (question, answer) in enumerate(questions_and_answers, 1):
            qa_pairs_text += f"\nQuestion {i}:\n{question}\nCandidate Answer:\n{answer}\n"
        
        prompt = f"""
        Evaluate the following 20 interview questions and candidate answers.
        
        {qa_pairs_text}
        
        Return ONLY a structured JSON object. Do NOT wrap it in markdown block quotes (```json ... ```).
        It must contain exactly these keys:
        - "results" (array of 20 objects)
        
        Each result object must have these exact keys:
        - "question_number" (integer, 1 to 20)
        - "question" (string: the original question)
        - "candidate_answer" (string: the candidate's answer)
        - "suggested_answer" (string: a concise improved answer, max 2-3 sentences)
        - "score" (integer from 0 to 100)
        - "feedback" (string: short feedback, max 1-2 sentences)
        
        Keep suggested answers and feedback concise. Do not generate long explanations.
        """
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "maxOutputTokens": 8000,
                "temperature": 0.3
            }
        }

        try:
            response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=60)
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
            print(f"Error calling Gemini Batch Evaluation API: {e}")
            if 'response' in locals():
                print(f"Response: {response.text}")
            return None
