# Speech transcription is now handled client-side using Web Speech API
# This service is kept for backward compatibility but no longer calls Gemini
class SpeechService:
    def __init__(self):
        pass

    def transcribe(self, audio_file_path):
        """
        DEPRECATED: Transcription is now handled client-side using Web Speech API.
        This method returns None as it should not be called.
        """
        print("WARNING: Server-side transcription is deprecated. Use client-side Web Speech API.")
        return None
