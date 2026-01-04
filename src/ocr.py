import io

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

# Windows explicit path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text_from_image(image: Image.Image) -> str:
    return pytesseract.image_to_string(image)


def extract_text_from_pdf(pdf_file) -> str:
    """
    High-precision PDF text extraction:
    1. Try structured text
    2. Fallback to OCR with higher DPI
    """
    text = ""
    pdf = fitz.open(stream=pdf_file.read(), filetype="pdf")

    for page in pdf:
        page_text = page.get_text("text").strip()

        if len(page_text) > 100:
            text += page_text + "\n"
        else:
            # OCR fallback (high precision)
            pix = page.get_pixmap(dpi=400)
            img = Image.open(io.BytesIO(pix.tobytes()))
            text += (
                pytesseract.image_to_string(
                    img, config="--psm 6 -c preserve_interword_spaces=1"
                )
                + "\n"
            )

    return text
