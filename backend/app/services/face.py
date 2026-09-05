import cv2
import numpy as np
from deepface import DeepFace

def verify_face(document_bytes: bytes, live_face_bytes: bytes) -> dict:
    """
    Compares the face found in the document image with the live face image.
    Uses DeepFace for face detection and 1:1 verification.
    """
    try:
        # Convert bytes to numpy arrays for OpenCV
        doc_nparr = np.frombuffer(document_bytes, np.uint8)
        live_nparr = np.frombuffer(live_face_bytes, np.uint8)
        
        doc_img = cv2.imdecode(doc_nparr, cv2.IMREAD_COLOR)
        live_img = cv2.imdecode(live_nparr, cv2.IMREAD_COLOR)
        
        if doc_img is None or live_img is None:
            return {"status": "error", "message": "Failed to decode one or both images"}

        # DeepFace verify automatically detects faces in the provided images
        # We use a lightweight model (VGG-Face) for fast hackathon demo performance
        result = DeepFace.verify(
            img1_path=doc_img,
            img2_path=live_img,
            model_name="VGG-Face", 
            enforce_detection=True # Fails if no face found in either image
        )
        
        # result is a dict with: verified, distance, threshold, model, similarity_metric, etc.
        # We can calculate a confidence percentage
        distance = result.get("distance", 1.0)
        threshold = result.get("threshold", 0.40)
        
        # Basic similarity calculation (heuristic for UI display)
        # If distance == 0, similarity is 100%. If distance == threshold, similarity is ~70%
        similarity = max(0, 100 - (distance / threshold * 30)) if result["verified"] else max(0, 70 - (distance * 50))
        
        return {
            "status": "success",
            "match": result.get("verified", False),
            "similarity": round(similarity, 2),
            "distance": round(distance, 4)
        }
        
    except ValueError as e:
        # Usually triggered when enforce_detection=True and no face is found
        return {
            "status": "error",
            "message": "Face not detected in one or both images.",
            "details": str(e)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "An unexpected error occurred during face verification.",
            "details": str(e)
        }
