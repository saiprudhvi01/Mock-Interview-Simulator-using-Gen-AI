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
            response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=90)
            response.raise_for_status()
            
            data = response.json()
            content = data['candidates'][0]['content']['parts'][0]['text']
            
            print(f"Batch evaluation raw response length: {len(content)}")
            print(f"First 500 chars: {content[:500]}")
            
            # Clean up markdown JSON wrapper
            content = content.strip()
            
            # Remove markdown code blocks
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.rfind("```")
                if end > start:
                    content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.rfind("```")
                if end > start:
                    content = content[start:end].strip()
            
            # Try to find JSON object in the content
            if content.startswith("{"):
                # Find the matching closing brace
                brace_count = 0
                end_index = 0
                for i, char in enumerate(content):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_index = i + 1
                            break
                if end_index > 0:
                    content = content[:end_index]
            
            print(f"Batch evaluation cleaned content length: {len(content)}")
            
            evaluation = json.loads(content.strip())
            
            # Validate structure
            if 'results' not in evaluation:
                print("Error: Evaluation response missing 'results' key")
                return None
                
            if not isinstance(evaluation['results'], list):
                print("Error: 'results' is not a list")
                return None
                
            if len(evaluation['results']) != 20:
                print(f"Warning: Expected 20 results, got {len(evaluation['results'])}")
            
            # Validate each result has required fields
            required_keys = ['question_number', 'question', 'candidate_answer', 'suggested_answer', 'score', 'feedback']
            for r in evaluation['results']:
                if not all(k in r for k in required_keys):
                    print(f"Error: Result missing required fields: {r}")
                    return None
            
            return evaluation
            
        except json.JSONDecodeError as e:
            print(f"Batch evaluation JSON parsing error: {e}")
            print(f"Content that failed to parse: {content if 'content' in locals() else 'N/A'}")
            return None
        except Exception as e:
            print(f"Error calling Gemini Batch Evaluation API: {e}")
            if 'response' in locals():
                print(f"Response status: {response.status_code}")
                print(f"Response: {response.text[:1000]}")
            return None
