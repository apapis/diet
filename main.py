import os
from abc import ABC, abstractmethod
from pathlib import Path
import PyPDF2
from dotenv import load_dotenv
from langfuse.decorators import observe
from langfuse import Langfuse
from langfuse.openai import openai
import uuid

load_dotenv()

langfuse = Langfuse(
    public_key=os.getenv('LANGFUSE_PUBLIC_KEY'),
    secret_key=os.getenv('LANGFUSE_SECRET_KEY')
)

openai._langfuse = langfuse

class FileReader(ABC):
    @abstractmethod
    def read(self, file_path: str) -> str:
        pass

class PDFReader(FileReader):
    @observe(name="read_pdf_file")
    def read(self, file_path: str) -> str:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            return " ".join(page.extract_text() for page in pdf_reader.pages)

class SessionManager:
    def __init__(self):
        self.session_id = str(uuid.uuid4())

class FileValidator:
    @staticmethod
    def validate_pdf(file_path: str) -> bool:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Plik nie istnieje: {file_path}")
        if not file_path.lower().endswith('.pdf'):
            raise ValueError("Plik musi być w formacie PDF")
        return True

class DietAnalyzer:
    def __init__(self):
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.session_manager = SessionManager()
        self.pdf_reader = PDFReader()
    
    @observe(name="analyze_pdf_content")
    def analyze_pdf(self, pdf_path: str) -> str:
        try:
            FileValidator.validate_pdf(pdf_path)
            return self.pdf_reader.read(pdf_path)
            
        except Exception as e:
            print(f"Błąd podczas wczytywania PDF: {str(e)}")
            return None

def main():
    try:
        analyzer = DietAnalyzer()
        pdf_path = input("Podaj ścieżkę do pliku PDF z dietą: ")
        
        text_content = analyzer.analyze_pdf(pdf_path)
        
        if text_content:
            print("\nZawartość PDF (pierwsze 500 znaków):")
            print(text_content[:500] + "...")
        else:
            print("Nie udało się wczytać pliku PDF.")
    finally:
        if hasattr(openai, '_langfuse') and openai._langfuse:
            openai._langfuse.flush()

if __name__ == "__main__":
    main()