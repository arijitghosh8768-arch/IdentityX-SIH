import cv2
import numpy as np
import base64
import re
from PIL import Image
from PIL.ExifTags import TAGS
import io

def perform_ela(image: np.ndarray, quality: int = 90) -> np.ndarray:
    """Performs Error Level Analysis (ELA) on an image array."""
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    _, encoded_img = cv2.imencode('.jpg', image, encode_param)
    compressed_img = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)
    diff = cv2.absdiff(image, compressed_img)
    max_val = np.max(diff)
    if max_val == 0:
        max_val = 1
    ela_image = (diff * (255.0 / max_val)).astype(np.uint8)
    return ela_image

def extract_metadata(document_bytes: bytes) -> dict:
    """Extracts EXIF metadata and checks for photo editing software signatures."""
    metadata = {}
    suspicious_software = ["photoshop", "gimp", "lightroom", "pixelmator", "snapseed"]
    is_edited = False
    software_found = None
    
    try:
        # Load with PIL to read EXIF
        img = Image.open(io.BytesIO(document_bytes))
        exif = img.getexif()
        
        if exif:
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                metadata[tag] = str(value)
                
                # Check Software tag
                if tag == "Software" and isinstance(value, str):
                    val_lower = value.lower()
                    for sw in suspicious_software:
                        if sw in val_lower:
                            is_edited = True
                            software_found = value
                            break
                            
    except Exception as e:
        # Some images like PNGs might not have EXIF, or parsing fails
        pass
        
    return {
        "metadata_present": len(metadata) > 0,
        "is_edited": is_edited,
        "editing_software": software_found
    }


def detect_tampering(document_bytes: bytes) -> dict:
    """Analyzes the document for potential tampering using ELA and metadata."""
    try:
        # 1. Metadata Analysis
        meta_analysis = extract_metadata(document_bytes)
        
        # 2. ELA Image Analysis
        nparr = np.frombuffer(document_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {"status": "error", "message": "Could not decode image for tampering analysis"}
            
        ela_img = perform_ela(img)
        gray_ela = cv2.cvtColor(ela_img, cv2.COLOR_BGR2GRAY)
        
        threshold = 50 # Intensity threshold
        _, thresh_img = cv2.threshold(gray_ela, threshold, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        suspicious_regions = []
        total_suspicious_area = 0
        img_area = img.shape[0] * img.shape[1]
        
        heatmap_img = img.copy()
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > (img_area * 0.01): 
                x, y, w, h = cv2.boundingRect(cnt)
                suspicious_regions.append({"x": x, "y": y, "w": w, "h": h, "area": area})
                total_suspicious_area += area
                cv2.rectangle(heatmap_img, (x, y), (x+w, y+h), (0, 0, 255), 4)
                
        # Calculate Base Tampering Score
        suspicious_percentage = (total_suspicious_area / img_area) * 100
        tamper_score = min(100.0, suspicious_percentage * 5)
        
        # Boost score if editing software was found in EXIF
        if meta_analysis["is_edited"]:
            tamper_score = min(100.0, tamper_score + 40.0)
            
        is_tampered = tamper_score > 30.0
        
        base64_heatmap = None
        if is_tampered:
            _, buffer = cv2.imencode('.jpg', heatmap_img)
            base64_heatmap = "data:image/jpeg;base64," + base64.b64encode(buffer).decode('utf-8')
            
        return {
            "status": "success",
            "is_tampered": is_tampered,
            "tamper_score": round(tamper_score, 2),
            "suspicious_regions_count": len(suspicious_regions),
            "heatmap_image": base64_heatmap,
            "metadata_edited": meta_analysis["is_edited"],
            "software_signature": meta_analysis["editing_software"]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": "Failed during tampering detection",
            "details": str(e)
        }
