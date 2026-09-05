import cv2
import numpy as np
from deepface import DeepFace

def verify_face(document_bytes: bytes, live_face_bytes: bytes) -> dict:
    """
    Compares the face in the document against the live face using DeepFace.
    """
    try:
        # Decode both images
        nparr1 = np.frombuffer(document_bytes, np.uint8)
        img1_np = cv2.imdecode(nparr1, cv2.IMREAD_COLOR)
        
        nparr2 = np.frombuffer(live_face_bytes, np.uint8)
        img2_np = cv2.imdecode(nparr2, cv2.IMREAD_COLOR)

        # Using mtcnn: much better at finding small faces in documents
        result = DeepFace.verify(
            img1_path=img1_np, 
            img2_path=img2_np, 
            model_name="VGG-Face",
            enforce_detection=False, 
            detector_backend="mtcnn" 
        )
        
        # DeepFace returns a 'distance' (lower is better) and a 'threshold' (e.g. 0.40)
        distance = result.get("distance", 1.0)
        base_threshold = result.get("threshold", 0.40)
        
        # HACKATHON TWEAK: Relax the threshold by 0.15 to account for old ID photos and webcams
        relaxed_threshold = base_threshold + 0.15
        is_match = distance <= relaxed_threshold
        
        # Convert distance to a pseudo-similarity percentage (0 distance = 100%)
        similarity = max(0.0, min(100.0, (1.0 - (distance / 0.8)) * 100))
        
        return {
            "status": "success",
            "match": is_match,
            "similarity": round(similarity, 2),
            "distance": round(distance, 4)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "Face verification failed",
            "details": str(e)
        }
