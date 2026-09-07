import cv2
import numpy as np
from deepface import DeepFace
from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger("face")
settings = get_settings()

def detect_blur(image_np: np.ndarray, threshold: float = 100.0) -> bool:
    """Computes the variance of the Laplacian to detect blur."""
    gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return variance < threshold

def verify_face(document_bytes: bytes, live_face_bytes: bytes) -> dict:
    """
    Compares the face in the document against the live face using DeepFace.
    Also includes a basic blur check on the live face as a simple liveness heuristic.
    """
    try:
        # Decode both images
        nparr1 = np.frombuffer(document_bytes, np.uint8)
        img1_np = cv2.imdecode(nparr1, cv2.IMREAD_COLOR)
        
        nparr2 = np.frombuffer(live_face_bytes, np.uint8)
        img2_np = cv2.imdecode(nparr2, cv2.IMREAD_COLOR)

        # Liveness check (simple blur detection on live face)
        is_blurred = detect_blur(img2_np)
        if is_blurred:
            logger.warning("Live face appears excessively blurred (potential presentation attack).")

        # DeepFace verification
        result = DeepFace.verify(
            img1_path=img1_np, 
            img2_path=img2_np, 
            model_name=settings.FACE_MODEL,
            enforce_detection=False, 
            detector_backend=settings.FACE_DETECTOR
        )
        
        # DeepFace returns a 'distance' (lower is better) and a 'threshold' (e.g. 0.40)
        distance = result.get("distance", 1.0)
        base_threshold = result.get("threshold", 0.40)
        
        # HACKATHON TWEAK: Relax the threshold to account for old ID photos and webcams
        relaxed_threshold = base_threshold + settings.FACE_THRESHOLD_RELAX
        is_match = distance <= relaxed_threshold
        
        # Convert distance to a pseudo-similarity percentage (0 distance = 100%)
        similarity = max(0.0, min(100.0, (1.0 - (distance / 0.8)) * 100))
        
        return {
            "status": "success",
            "match": is_match,
            "similarity": round(similarity, 2),
            "distance": round(distance, 4),
            "is_blurred": is_blurred,
            "message": "Live face is excessively blurry." if is_blurred else None
        }
    except Exception as e:
        logger.error(f"Face verification failed: {e}")
        return {
            "status": "error",
            "message": "Face verification failed",
            "details": str(e)
        }
