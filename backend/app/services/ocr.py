import cv2
import numpy as np
import easyocr
import re

# Lazy load to prevent blocking server startup
reader = None

def process_document_ocr(image_bytes: bytes) -> dict:
    """
    Processes a document image to extract text and MRZ data.
    """
    global reader
    if reader is None:
        reader = easyocr.Reader(['en'], gpu=False)
        
    # Convert bytes to numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    # Decode image
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
         return {"error": "Could not decode image."}

    # Extract text using EasyOCR
    # detail=0 returns just the text, detail=1 returns bounding boxes and confidence
    results = reader.readtext(img, detail=0)
    
    # Simple extraction logic (Prototype level)
    # In a real app, we'd use bounding boxes to find specific fields (Name, DOB, etc.)
    full_text = " ".join(results)
    
    parsed_data = parse_passport_text(results)
    
    # Extract MRZ (Usually found at the bottom, containing < characters)
    mrz_lines = [line for line in results if '<' in line and len(line) > 10]
    
    return {
        "raw_text_segments": results,
        "extracted_fields": parsed_data,
        "mrz_lines": mrz_lines,
        "status": "success" if results else "failed"
    }

def parse_passport_text(text_lines: list) -> dict:
    """
    A naive parser to extract fields from the OCR text lines.
    """
    data = {
        "name": None,
        "passport_number": None,
        "dob": None,
        "expiry": None,
        "nationality": None
    }
    
    # Basic Regex patterns
    date_pattern = re.compile(r'\d{2}[-/]\d{2}[-/]\d{4}')
    passport_no_pattern = re.compile(r'^[A-Z0-9]{7,9}$')
    
    dates_found = []
    
    for line in text_lines:
        line_clean = line.strip().upper()
        
        # Look for dates
        dates = date_pattern.findall(line_clean)
        if dates:
            dates_found.extend(dates)
            
        # Look for Passport Number (heuristics)
        # Often a mix of letters and numbers, 7-9 chars long
        if passport_no_pattern.match(line_clean) and not data["passport_number"]:
            data["passport_number"] = line_clean
            
    # If we found multiple dates, we can guess DOB vs Expiry by sorting
    if len(dates_found) >= 2:
        # Simplistic approach: older date is DOB, newer is Expiry
        # Needs proper date parsing for real use
        dates_found.sort(key=lambda x: x[-4:]) # sort by year
        data["dob"] = dates_found[0]
        data["expiry"] = dates_found[-1]

    return data
