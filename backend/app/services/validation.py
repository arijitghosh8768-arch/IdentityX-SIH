from datetime import datetime

def validate_document(extracted_fields: dict, mrz_consistency: dict) -> dict:
    """
    Applies business rules to validate the document.
    """
    checks = {
        "required_fields_present": False,
        "expiry_valid": False,
        "mrz_consistent": mrz_consistency.get("consistent", False)
    }
    
    warnings = []
    
    # 1. Check required fields
    required = ["name", "passport_number", "dob", "expiry"]
    missing = [field for field in required if not extracted_fields.get(field)]
    if not missing:
        checks["required_fields_present"] = True
    else:
        warnings.append(f"Missing fields: {', '.join(missing)}")
        
    # 2. Check Expiry Date
    expiry_str = extracted_fields.get("expiry")
    if expiry_str:
        try:
            # Assuming DD-MM-YYYY format from our OCR/MRZ parser
            expiry_date = datetime.strptime(expiry_str, "%d-%m-%Y")
            if expiry_date > datetime.now():
                checks["expiry_valid"] = True
            else:
                warnings.append("Document has expired.")
        except ValueError:
            warnings.append("Invalid expiry date format.")
            
    # Combine results
    is_valid = all(checks.values())
    
    status = "VALID"
    if not checks["expiry_valid"] or not checks["mrz_consistent"]:
        status = "SUSPICIOUS"
    elif not checks["required_fields_present"]:
        status = "INCOMPLETE"

    return {
        "status": status,
        "checks": checks,
        "warnings": warnings,
        "mrz_mismatches": mrz_consistency.get("mismatches", [])
    }
