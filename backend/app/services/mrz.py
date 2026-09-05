def parse_mrz(mrz_lines: list) -> dict:
    """
    Parses MRZ lines to extract passport number, DOB, and expiry.
    For a TD3 Passport MRZ (2 lines of 44 chars).
    """
    if not mrz_lines or len(mrz_lines) < 2:
        return {"status": "error", "message": "Invalid MRZ format"}

    # Clean up any OCR artifacts (spaces)
    line1 = mrz_lines[0].replace(" ", "").upper()
    line2 = mrz_lines[1].replace(" ", "").upper()

    # Basic TD3 length check
    if len(line1) < 40 or len(line2) < 40:
        return {"status": "error", "message": "MRZ lines too short"}

    # Extract fields from Line 2
    # Format: PassportNo(9) CheckDigit(1) Nationality(3) DOB[YYMMDD](6) CheckDigit(1) Sex(1) Expiry[YYMMDD](6)
    try:
        passport_no = line2[0:9].replace("<", "")
        
        dob_raw = line2[13:19]  # YYMMDD
        # Convert YYMMDD to readable format (Naive approach for prototype)
        if len(dob_raw) == 6:
            year_prefix = "19" if int(dob_raw[:2]) > 30 else "20"
            dob = f"{dob_raw[4:6]}-{dob_raw[2:4]}-{year_prefix}{dob_raw[:2]}"
        else:
            dob = None

        expiry_raw = line2[21:27] # YYMMDD
        if len(expiry_raw) == 6:
            expiry = f"{expiry_raw[4:6]}-{expiry_raw[2:4]}-20{expiry_raw[:2]}"
        else:
            expiry = None

        return {
            "status": "success",
            "passport_number": passport_no,
            "dob": dob,
            "expiry": expiry
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def verify_mrz_consistency(ocr_data: dict, mrz_data: dict) -> dict:
    """
    Compares data extracted from text OCR with data parsed from the MRZ.
    """
    if mrz_data.get("status") != "success":
        return {"consistent": False, "reason": mrz_data.get("message")}
        
    mismatches = []
    
    # Check Passport Number
    if ocr_data.get("passport_number") and mrz_data.get("passport_number"):
        if ocr_data["passport_number"] != mrz_data["passport_number"]:
            mismatches.append(f"Passport No mismatch: OCR({ocr_data['passport_number']}) vs MRZ({mrz_data['passport_number']})")
            
    # Check DOB
    if ocr_data.get("dob") and mrz_data.get("dob"):
        # For prototype, assuming exact string match since we standardized format
        if ocr_data["dob"] != mrz_data["dob"]:
            mismatches.append(f"DOB mismatch: OCR({ocr_data['dob']}) vs MRZ({mrz_data['dob']})")
            
    # Check Expiry
    if ocr_data.get("expiry") and mrz_data.get("expiry"):
        if ocr_data["expiry"] != mrz_data["expiry"]:
            mismatches.append(f"Expiry mismatch: OCR({ocr_data['expiry']}) vs MRZ({mrz_data['expiry']})")

    if mismatches:
        return {
            "consistent": False,
            "status": "SUSPICIOUS",
            "mismatches": mismatches
        }
        
    return {
        "consistent": True,
        "status": "VALID",
        "mismatches": []
    }
