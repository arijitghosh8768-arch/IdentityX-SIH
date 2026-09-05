import cv2
import numpy as np
import os
import base64

def perform_ela(image: np.ndarray, quality: int = 90) -> np.ndarray:
    """
    Performs Error Level Analysis (ELA) on an image array.
    Saves the image at a known quality, reloads it, and calculates the absolute difference.
    """
    # Temporarily encode to JPEG in memory
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    _, encoded_img = cv2.imencode('.jpg', image, encode_param)
    
    # Decode back
    compressed_img = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)
    
    # Calculate absolute difference
    diff = cv2.absdiff(image, compressed_img)
    
    # Scale differences to make them visible (ELA enhancement)
    # The max value will be scaled to 255
    max_val = np.max(diff)
    if max_val == 0:
        max_val = 1
    
    ela_image = (diff * (255.0 / max_val)).astype(np.uint8)
    return ela_image

def detect_tampering(document_bytes: bytes) -> dict:
    """
    Analyzes the document for potential tampering using ELA and basic image analysis.
    """
    try:
        nparr = np.frombuffer(document_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {"status": "error", "message": "Could not decode image for tampering analysis"}
            
        # 1. Error Level Analysis
        ela_img = perform_ela(img)
        
        # 2. Analyze ELA Variance
        gray_ela = cv2.cvtColor(ela_img, cv2.COLOR_BGR2GRAY)
        
        threshold = 50 # Intensity threshold
        _, thresh_img = cv2.threshold(gray_ela, threshold, 255, cv2.THRESH_BINARY)
        
        contours, _ = cv2.findContours(thresh_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        suspicious_regions = []
        total_suspicious_area = 0
        img_area = img.shape[0] * img.shape[1]
        
        # Draw on a copy of the original image
        heatmap_img = img.copy()
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Filter out tiny noise artifacts, focus on significant areas
            if area > (img_area * 0.01): 
                x, y, w, h = cv2.boundingRect(cnt)
                suspicious_regions.append({"x": x, "y": y, "w": w, "h": h, "area": area})
                total_suspicious_area += area
                
                # Draw thick red bounding box for frontend heatmap
                cv2.rectangle(heatmap_img, (x, y), (x+w, y+h), (0, 0, 255), 4)
                
        # Calculate Tampering Score
        suspicious_percentage = (total_suspicious_area / img_area) * 100
        tamper_score = min(100.0, suspicious_percentage * 5)
        
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
            "heatmap_image": base64_heatmap
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": "Failed during tampering detection",
            "details": str(e)
        }
