import fitz  # PyMuPDF
import re

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a given PDF file.
    Returns the extracted string, or None if it fails.
    """
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text += page.get_text("text") + "\n"
        
        # Clean unnecessary whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None
