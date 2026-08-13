import requests
import base64
from flask import current_app

class SpeechService:
    def __init__(self):
        self.model = "gemini-3.5-flash"

    def transcribe(self, audio_file_path):
        """
        Sends the audio file to the Gemini API as inline data to transcribe.
        """
        api_key = current_app.config.get('GEMINI_API_KEY')
        
        if not api_key:
            print("WARNING: GEMINI_API_KEY not set. Returning mock transcript.")
            return "Mock transcript"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={api_key}"
        
        try:
            # Read the file and encode to base64
            with open(audio_file_path, 'rb') as f:
                audio_data = f.read()
            
            base64_audio = base64.b64encode(audio_data).decode('utf-8')
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": "Transcribe this audio strictly. Output ONLY the transcribed text without any other comments or formatting."},
                            {
                                "inlineData": {
                                    "mimeType": "audio/webm",
                                    "data": base64_audio
                                }
                            }
                        ]
                    }
                ]
            }

            response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            transcript = data['candidates'][0]['content']['parts'][0]['text']
            return transcript.strip()
                
        except Exception as e:
            print(f"Error calling Gemini Speech API: {e}")
            if 'response' in locals():
                print(f"Response: {response.text}")
            return None
