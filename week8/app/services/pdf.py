"""PDF service for extracting metadata from papers."""

import pdfplumber
import os
import re
from typing import Optional


class PDFService:
    def extract_metadata(self, pdf_path: str) -> Optional[dict]:
        """Extract metadata from PDF."""
        if not os.path.exists(pdf_path):
            return None

        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Get first page text for title/abstract
                if pdf.pages:
                    first_page = pdf.pages[0]
                    text = first_page.extract_text() or ""

                    # Extract title (usually first few lines)
                    lines = text.split("\n")[:5]
                    title = " ".join([l.strip() for l in lines if l.strip()])[:500]

                    return {
                        "title": title,
                        "abstract": None,  # PDF doesn't always have structured abstract
                    }
        except Exception as e:
            print(f"Error extracting metadata from {pdf_path}: {e}")

        return None

    def extract_full_text(self, pdf_path: str) -> Optional[str]:
        """Extract full text from PDF for LLM context."""
        if not os.path.exists(pdf_path):
            return None
        try:
            with pdfplumber.open(pdf_path) as pdf:
                parts = []
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        parts.append(t)
                return "\n".join(parts).strip() or None
        except Exception as e:
            print(f"Error extracting full text from {pdf_path}: {e}")
        return None
