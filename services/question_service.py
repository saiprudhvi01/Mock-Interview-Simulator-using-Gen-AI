import requests
import json
import re
from flask import current_app

class QuestionService:
    def __init__(self):
        self.model = "gemini-3.5-flash"

    def generate_questions(self, resume_text, difficulty_level="Medium"):
        """
        Sends the resume text to the Gemini API to generate questions.
        Returns a list of structured questions based on difficulty level.
        """
        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key:
            print("WARNING: GEMINI_API_KEY not set. Returning mock questions.")
            return [{"id": 1, "question": "Mock question?", "category": "Technical", "difficulty": difficulty_level}]

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={api_key}"
        
        # Adjust prompt based on difficulty level
        difficulty_instruction = ""
        if difficulty_level == "Easy":
            difficulty_instruction = "Focus on fundamental concepts and basic questions. Avoid complex scenarios or advanced topics."
        elif difficulty_level == "Medium":
            difficulty_instruction = "Include a balanced mix of fundamental, intermediate, and some advanced questions. Include some scenario-based questions."
        elif difficulty_level == "Hard":
            difficulty_instruction = "Focus on advanced concepts, complex scenarios, system design, and in-depth technical questions. Challenge the candidate with difficult problems."
        elif difficulty_level == "Mixed":
            difficulty_instruction = "Include a comprehensive mix of easy, medium, and hard questions. Start with easier questions and progressively increase difficulty."
        
        prompt = f"""
        Analyze the following candidate resume carefully.
        Generate exactly 20 personalized interview questions based strictly on the information present in the resume.
        
        Selected difficulty level: {difficulty_level}
        {difficulty_instruction}
        
        Follow this EXACT sequence:
        - Questions 1-2: Ask 2 HR/general interview questions.
        - Questions 3-10: Ask 8 technical questions based on the resume, skills, projects, and the job role.
        - Questions 11-12: Ask 2 more HR/behavioral questions.
        - Questions 13-19: Ask 7 technical questions, including scenario-based questions appropriate for the {difficulty_level} difficulty level.
        - Question 20: Ask 1 final HR question, such as salary expectations, relocation, career goals, or why we should hire you.

        For technical questions, focus specifically on:
        - The technologies, frameworks, and tools mentioned in the resume
        - The candidate's actual projects and work experience
        - Skills and expertise demonstrated in their resume
        - Real-world scenarios relevant to their experience
        
        Make questions realistic and relevant to actual interviews for someone with this profile.
        Avoid generic questions unrelated to the candidate's specific background.
        
        Return ONLY a structured JSON array containing 20 objects. Do NOT wrap it in markdown block quotes (```json ... ```).
        Each object must have these exact keys:
        "id" (integer, 1 to 20),
        "question" (string),
        "category" (string - HR/Technical/Behavioral/Scenario),
        "difficulty" (string - Easy/Medium/Hard based on the {difficulty_level} level).
        
        Resume:
        {resume_text}
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
            
            # Clean up potential markdown formatting that Gemini sometimes adds
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
                
            questions = json.loads(content.strip())
            return questions
            
        except Exception as e:
            print(f"Error calling Gemini Question API: {e}")
            if 'response' in locals():
                print(f"Response: {response.text}")
            return None
