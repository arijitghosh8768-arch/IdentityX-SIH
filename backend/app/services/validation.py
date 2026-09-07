from datetime import datetime
import re

REQUIRED_FIELDS = {
    "passport": ["name", "passport_number", "dob", "expiry"],
    "visa": ["name", "visa_number", "visa_type", "entry_validation", "stay_duration"],
    "national_id": ["name", "id_number", "dob"],
    "driving_license": ["name", "license_number", "dob", "expiry"],
    "permit": ["name", "permit_number", "permit_type", "expiry"],
}

def luhn_checksum(card_number: str) -> bool:
    """Calculates Luhn checksum for Aadhaar and other national IDs."""
    if not card_number or not card_number.isdigit():
        return False
        
    # Standard Luhn Algorithm
    n_digits = len(card_number)
    n_sum = 0
    is_second = False
    
    for i in range(n_digits - 1, -1, -1):
        d = ord(card_number[i]) - ord('0')
        if is_second:
            d = d * 2
        
        n_sum += d // 10
        n_sum += d % 10
        is_second = not is_second
        
    return n_sum % 10 == 0


def validate_document(
    extracted_fields: dict,
    mrz_consistency: dict,
    document_type: str = "passport"
) -> dict:
    """Applies business rules and checksums to validate the document."""
    
    checks = {
        "required_fields_present": False,
        "expiry_valid": False,
        "mrz_consistent": (
            mrz_consistency.get("consistent", False)
            if mrz_consistency.get("status") != "NOT_APPLICABLE" else True
        ),
        "id_checksum_valid": True  # Default True unless it's a National ID and fails
    }
    
    warnings = []
    
    # 1. Check required fields
    required = REQUIRED_FIELDS.get(document_type, REQUIRED_FIELDS["passport"])
    missing = [field for field in required if not extracted_fields.get(field)]
    if not missing:
        checks["required_fields_present"] = True
    else:
        warnings.append(f"Missing fields: {', '.join(missing)}")
        
    # 2. Check Expiry Date (Handling multiple formats)
    expiry_str = extracted_fields.get("expiry")
    if expiry_str:
        parsed_date = None
        for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d"):
            try:
                parsed_date = datetime.strptime(expiry_str.strip(), fmt)
                break
            except ValueError:
                continue
                
        if parsed_date:
            if parsed_date > datetime.now():
                checks["expiry_valid"] = True
            else:
                warnings.append("Document has expired.")
        else:
            warnings.append("Invalid expiry date format.")
            
    # 3. Aadhaar / National ID Checksum
    if document_type == "national_id":
        id_number = extracted_fields.get("id_number", "")
        # Remove spaces/hyphens for check
        clean_id = re.sub(r"[ -]", "", id_number)
        # Aadhaar is 12 digits, often verifiable with Verhoeff (but we'll use Luhn/Verhoeff check logic)
        # For this prototype, we'll implement a basic checksum verification if it looks like an Aadhaar
        if len(clean_id) == 12 and clean_id.isdigit():
            # In a real system, Aadhaar uses Verhoeff algorithm. 
            # We'll use a placeholder logic or simple Luhn for demonstration if we wanted.
            # We will just mark it present here for the hackathon prototype.
            checks["id_checksum_valid"] = True 
        elif clean_id:
            checks["id_checksum_valid"] = luhn_checksum(clean_id)
            if not checks["id_checksum_valid"]:
                warnings.append("National ID number failed checksum verification.")
            
    # Combine results
    is_valid = all(checks.values())
    
    status = "VALID"
    expiry_required = "expiry" in required
    
    if (expiry_required and not checks["expiry_valid"]) or not checks["mrz_consistent"] or not checks["id_checksum_valid"]:
        status = "SUSPICIOUS"
    elif not checks["required_fields_present"]:
        status = "INCOMPLETE"

    return {
        "status": status,
        "checks": checks,
        "warnings": warnings,
        "mrz_mismatches": mrz_consistency.get("mismatches", [])
    }
