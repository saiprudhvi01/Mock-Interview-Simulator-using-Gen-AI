import re
from pypdf import PdfReader

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a given PDF file using pure-Python pypdf.
    Returns the extracted string, or None if it fails.
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        
        # Clean unnecessary whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None
