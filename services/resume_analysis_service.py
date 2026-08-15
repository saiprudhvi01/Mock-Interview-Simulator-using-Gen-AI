import requests
import json
from flask import current_app

class ResumeAnalysisService:
    def __init__(self):
        self.model = "gemini-3.5-flash-lite"

    def analyze_resume(self, resume_text):
        """
        Analyzes the resume and provides comprehensive feedback.
        Returns a dict with score, ATS assessment, strengths, improvements, etc.
        """
        api_key = current_app.config.get('GEMINI_API_KEY')
        
        if not api_key:
            print("WARNING: GEMINI_API_KEY not set. Returning mock resume analysis.")
            return {
                "score": 75,
                "ats_score": 70,
                "readability": "Good",
                "strengths": ["Clear structure", "Relevant skills listed"],
                "improvements": ["Add more quantifiable achievements", "Include keywords"],
                "missing_skills": ["Cloud computing", "DevOps tools"],
                "project_improvements": ["Add more technical details", "Include outcomes"],
                "recommendations": ["Add metrics to achievements", "Include certifications", "Improve formatting"]
            }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={api_key}"
        
        prompt = f"""
        Analyze the following resume comprehensively. Provide a detailed assessment covering:
        
        1. Overall resume score (0-100)
        2. ATS/readability assessment (score 0-100 and brief assessment)
        3. Key strengths (3-5 bullet points)
        4. Areas to improve (3-5 bullet points)
        5. Missing or weak skills that should be added
        6. Project/experience improvements (specific suggestions)
        7. Specific recommendations to increase the resume score (actionable items)
        
        Resume:
        {resume_text}
        
        Return ONLY a structured JSON object. Do NOT wrap it in markdown block quotes (```json ... ```).
        It must contain exactly these keys:
        - "score" (integer from 0 to 100)
        - "ats_score" (integer from 0 to 100)
        - "readability" (string: Poor, Fair, Good, Excellent)
        - "strengths" (array of 3-5 strings)
        - "improvements" (array of 3-5 strings)
        - "missing_skills" (array of strings)
        - "project_improvements" (array of 3-5 strings)
        - "recommendations" (array of 5-7 actionable strings)
        
        Be specific and actionable in your recommendations.
        """
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "maxOutputTokens": 4000,
                "temperature": 0.3
            }
        }

        try:
            response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            content = data['candidates'][0]['content']['parts'][0]['text']
            
            print(f"Resume analysis raw response length: {len(content)}")
            
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
            
            print(f"Resume analysis cleaned content length: {len(content)}")
            
            analysis = json.loads(content.strip())
            
            # Validate structure
            required_keys = ['score', 'ats_score', 'readability', 'strengths', 'improvements', 'missing_skills', 'project_improvements', 'recommendations']
            for key in required_keys:
                if key not in analysis:
                    print(f"Warning: Missing key in resume analysis: {key}")
                    analysis[key] = [] if key in ['strengths', 'improvements', 'missing_skills', 'project_improvements', 'recommendations'] else 0
            
            return analysis
            
        except json.JSONDecodeError as e:
            print(f"Resume analysis JSON parsing error: {e}")
            print(f"Content that failed to parse: {content if 'content' in locals() else 'N/A'}")
            return None
        except Exception as e:
            print(f"Error calling Gemini Resume Analysis API: {e}")
            if 'response' in locals():
                print(f"Response status: {response.status_code}")
                print(f"Response: {response.text[:1000]}")
            return None
