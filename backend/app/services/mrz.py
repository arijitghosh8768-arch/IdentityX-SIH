from datetime import datetime


def check_digit(value: str) -> str:
    weights = [7, 3, 1]
    total = 0

    for i, char in enumerate(value):
        if char == "<":
            v = 0
        elif char.isdigit():
            v = int(char)
        elif char.isalpha():
            v = ord(char) - ord("A") + 10
        else:
            v = 0

        total += v * weights[i % 3]

    return str(total % 10)


def _date_from_mrz(value: str) -> str | None:
    if not value.isdigit() or len(value) != 6:
        return None
    year = int(value[:2])
    year += 1900 if year > 30 else 2000
    try:
        return datetime.strptime(f"{year}{value[2:]}", "%Y%m%d").strftime("%d-%m-%Y")
    except ValueError:
        return None


def _name_fields(value: str) -> dict:
    parts = value.split("<<", 1)
    surname = parts[0].replace("<", " ").strip()
    given_names = parts[1].replace("<", " ").strip() if len(parts) > 1 else ""
    return {
        "surname": surname or None,
        "given_names": given_names or None,
        "name": " ".join(part for part in (given_names, surname) if part) or None,
    }


def _parse_two_line_mrz(line1: str, line2: str) -> dict:
    """Parse TD3/MRV-A (44 columns) and TD2/MRV-B (36 columns)."""
    name_start = 5
    name_fields = _name_fields(line1[name_start:])
    number_raw = line2[0:9]
    dob_raw = line2[13:19]
    expiry_raw = line2[21:27]
    return {
        **name_fields,
        "document_number": number_raw.replace("<", ""),
        "nationality": line2[10:13],
        "sex": None if line2[20] == "<" else line2[20],
        "dob": _date_from_mrz(dob_raw),
        "expiry": _date_from_mrz(expiry_raw),
        "issuing_country": line1[2:5],
        "checks": {
            "document_number": check_digit(number_raw) == line2[9],
            "dob": check_digit(dob_raw) == line2[19],
            "expiry": check_digit(expiry_raw) == line2[27],
        },
    }


def _parse_three_line_mrz(lines: list[str]) -> dict:
    """Parse TD1 cards such as many national IDs and driving licences."""
    line1, line2, line3 = lines
    number_raw = line1[5:14]
    dob_raw = line2[0:6]
    expiry_raw = line2[8:14]
    return {
        **_name_fields(line3),
        "document_number": number_raw.replace("<", ""),
        "nationality": line2[15:18],
        "sex": None if line2[7] == "<" else line2[7],
        "dob": _date_from_mrz(dob_raw),
        "expiry": _date_from_mrz(expiry_raw),
        "issuing_country": line1[2:5],
        "checks": {
            "document_number": check_digit(number_raw) == line1[14],
            "dob": check_digit(dob_raw) == line2[6],
            "expiry": check_digit(expiry_raw) == line2[14],
        },
    }


def parse_mrz(mrz_lines: list, document_type: str = "passport") -> dict:
    """Parse standard TD1, TD2, TD3, and visa MRZ layouts."""
    if not mrz_lines:
        return {"status": "not_applicable", "message": "No MRZ detected"}

    lines = [line.replace(" ", "").upper() for line in mrz_lines]
    try:
        if len(lines) >= 3 and all(28 <= len(line) <= 30 for line in lines[:3]):
            parsed = _parse_three_line_mrz([line.ljust(30, "<") for line in lines[:3]])
        elif len(lines) >= 2 and 34 <= len(lines[0]) <= 44 and len(lines[1]) == len(lines[0]):
            target_length = 44 if len(lines[0]) >= 40 else 36
            padded_lines = [line.ljust(target_length, "<") for line in lines[:2]]
            parsed = _parse_two_line_mrz(padded_lines[0], padded_lines[1])
        else:
            return {"status": "error", "message": "Unsupported MRZ format"}

        number_field = {
            "passport": "passport_number",
            "visa": "visa_number",
            "national_id": "id_number",
            "driving_license": "license_number",
            "permit": "permit_number",
        }.get(document_type, "document_number")
        parsed[number_field] = parsed.pop("document_number")
        parsed["mrz_valid"] = all(parsed["checks"].values())
        parsed["status"] = "success"
        return parsed
    except (IndexError, ValueError) as error:
        return {"status": "error", "message": str(error)}


def normalize_date(date_str):
    if not date_str:
        return None

    for fmt in (
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%Y/%m/%d"
    ):
        try:
            return datetime.strptime(
                date_str.strip(),
                fmt
            ).date()
        except ValueError:
            continue

    return None


def verify_mrz_consistency(
    ocr_data: dict,
    mrz_data: dict,
    document_type: str = "passport"
) -> dict:

    if mrz_data.get("status") == "not_applicable":
        return {
            "consistent": True,
            "status": "NOT_APPLICABLE",
            "mismatches": []
        }

    if mrz_data.get("status") != "success":
        return {
            "consistent": False,
            "status": "ERROR",
            "reason": mrz_data.get("message")
        }

    mismatches = []

    number_field = {
        "passport": "passport_number",
        "visa": "visa_number",
        "national_id": "id_number",
        "driving_license": "license_number",
        "permit": "permit_number",
    }.get(document_type, "document_number")

    if ocr_data.get(number_field) and mrz_data.get(number_field):
        if ocr_data[number_field].strip().upper() != mrz_data[number_field].strip().upper():
            mismatches.append(
                f"Document number mismatch: OCR({ocr_data[number_field]}) "
                f"vs MRZ({mrz_data[number_field]})"
            )

    # DOB
    ocr_dob = normalize_date(
        ocr_data.get("dob")
    )
    mrz_dob = normalize_date(
        mrz_data.get("dob")
    )

    if ocr_dob and mrz_dob and ocr_dob != mrz_dob:
        mismatches.append(
            f"DOB mismatch: "
            f"OCR({ocr_data['dob']}) "
            f"vs MRZ({mrz_data['dob']})"
        )

    # Expiry
    ocr_expiry = normalize_date(
        ocr_data.get("expiry")
    )
    mrz_expiry = normalize_date(
        mrz_data.get("expiry")
    )

    if (
        ocr_expiry
        and mrz_expiry
        and ocr_expiry != mrz_expiry
    ):
        mismatches.append(
            f"Expiry mismatch: "
            f"OCR({ocr_data['expiry']}) "
            f"vs MRZ({mrz_data['expiry']})"
        )

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