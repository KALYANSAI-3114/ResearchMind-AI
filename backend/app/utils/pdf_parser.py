"""
PDF Parsing Module
Extracts text and metadata from research papers
"""

import fitz  # PyMuPDF
import os
from pathlib import Path


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract all text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        Extracted text as string
    """
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        for page in doc:
            text += page.get_text()
        
        doc.close()
        return text
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")


def extract_metadata_from_pdf(pdf_path: str) -> dict:
    """
    Extract metadata from PDF (title, author, etc.)
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        Dictionary with metadata
    """
    try:
        doc = fitz.open(pdf_path)

        metadata = doc.metadata
        pages = len(doc)

        result = {
            "title": metadata.get("title", "Unknown"),
            "author": metadata.get("author", "Unknown"),
            "subject": metadata.get("subject", ""),
            "pages": pages,
        }

        doc.close()

        return result

    except Exception as e:
        raise Exception(f"Error extracting metadata from PDF: {str(e)}")

def extract_first_page(pdf_path: str) -> str:
    """
    Extract text from first page (usually contains abstract/title).
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        Text from first page
    """
    try:
        doc = fitz.open(pdf_path)
        first_page_text = doc[0].get_text()
        doc.close()
        return first_page_text
    except Exception as e:
        raise Exception(f"Error extracting first page: {str(e)}")


def save_uploaded_pdf(uploaded_file_path: str, save_dir: str = "data/uploaded_papers") -> str:
    """
    Save uploaded PDF to specified directory.
    
    Args:
        uploaded_file_path: Path to uploaded file
        save_dir: Directory to save PDF
    
    Returns:
        Path to saved file
    """
    os.makedirs(save_dir, exist_ok=True)
    filename = Path(uploaded_file_path).name
    save_path = os.path.join(save_dir, filename)
    
    return save_path
