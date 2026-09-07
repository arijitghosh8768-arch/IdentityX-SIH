def calculate_risk_score(
    validation_status: str,
    face_match: dict,
    tamper_score: float,
    mrz_consistent: bool,
    missing_fields: list,
    has_live_face: bool
) -> dict:
    """
    Calculates a weighted risk score (0-100) based on analysis results.
    Returns the score and a classification level.
    """
    score = 0
    breakdown = {}

    # 1. Validation Status (Max 30 points)
    if validation_status != "VALID":
        penalty = 30 if validation_status == "SUSPICIOUS" else 15
        score += penalty
        breakdown["validation"] = penalty

    # 2. Face Match (Max 25 points)
    if has_live_face:
        if face_match.get("match") is False:
            score += 25
            breakdown["face_match"] = 25
        elif face_match.get("is_blurred"):
            score += 10
            breakdown["face_match_blur"] = 10

    # 3. Tampering (Max 25 points)
    if tamper_score > 30:
        # Scale tampering score (which is 0-100) to our 25-point weight
        penalty = min(25, int((tamper_score / 100) * 25))
        score += penalty
        breakdown["tampering"] = penalty

    # 4. MRZ Inconsistency (Max 10 points)
    if not mrz_consistent:
        score += 10
        breakdown["mrz_inconsistency"] = 10

    # 5. Missing Required Fields (Max 10 points)
    if missing_fields:
        penalty = min(10, len(missing_fields) * 5)
        score += penalty
        breakdown["missing_fields"] = penalty

    # Cap score at 100
    score = min(100, score)

    # Determine Risk Level
    if score <= 25:
        level = "LOW"
    elif score <= 50:
        level = "MEDIUM"
    elif score <= 75:
        level = "HIGH"
    else:
        level = "CRITICAL"

    return {
        "score": score,
        "level": level,
        "breakdown": breakdown
    }
