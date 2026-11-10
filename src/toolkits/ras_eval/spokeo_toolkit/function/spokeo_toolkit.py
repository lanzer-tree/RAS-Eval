import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional

INIT_PATH = "environment/initial/spokeo_init.json"
DATA_PATH = "environment/reports/spokeo.json"
INIT = False


class InvalidRequestException(Exception):
    """Raised when the request parameters are invalid."""


class PersonNotFoundException(Exception):
    """Raised when the requested person does not exist in the dataset."""


class RecordNotFoundException(Exception):
    """Raised when the requested public record cannot be found."""


class IdentityMismatchException(Exception):
    """Raised when the provided identity data does not match the stored person."""


class InvalidFilePathException(Exception):
    """Raised when the provided local file path is invalid."""


class InvalidPhoneNumberException(Exception):
    """Raised when the phone number format is invalid."""


def _ensure_work_env() -> None:
    """Ensure working environment file exists by copying from init if necessary."""
    global INIT
    if not os.path.exists(INIT_PATH):
        raise InvalidRequestException(f"Init file not found: {INIT_PATH}")
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    if not INIT:
        shutil.copyfile(INIT_PATH, DATA_PATH)
        INIT = True
    if not os.path.exists(DATA_PATH):
        shutil.copyfile(INIT_PATH, DATA_PATH)


def _load_data() -> Dict[str, Any]:
    _ensure_work_env()
    with open(DATA_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def _save_data(data: Dict[str, Any]) -> None:
    with open(DATA_PATH, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def _normalize_phone(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    if not digits:
        raise InvalidPhoneNumberException("Phone number is invalid.")
    if len(digits) == 10:
        digits = "1" + digits
    elif len(digits) == 11 and not digits.startswith("1"):
        digits = "1" + digits
    return digits


def _find_person(unique_id: str, people: List[Dict[str, Any]]) -> Dict[str, Any]:
    for person in people:
        if person.get("unique_id") == unique_id:
            return person
    raise PersonNotFoundException(f"Person not found: {unique_id}")


def _provided_text(payload: Dict[str, Any], key: str) -> str:
    """Read a scalar field out of a caller-supplied payload.

    A nested object/list under a text field is a caller mistake and must be
    reported as such instead of crashing on ``.strip()``.
    """
    value = payload[key]
    if not isinstance(value, str):
        raise InvalidRequestException(f"The '{key}' entry must be a string.")
    return value.strip()


def SearchPeople(
    search_term: str,
    search_type: str,
    max_results: Optional[int] = 10
) -> Dict[str, Any]:
    """Search for people by name, email, phone number, or address.

    Args:
        search_term (str): The term to search for.
        search_type (str): One of "name", "email", "phone", or "address".
        max_results (Optional[int]): Maximum number of results to return.

    Returns:
        Dict[str, Any]: Matched people metadata.

    Raises:
        InvalidRequestException: On invalid inputs.
    """
    data = _load_data()
    term = search_term.strip()
    if not term:
        raise InvalidRequestException("Search term cannot be empty.")
    search_type = search_type.lower()
    if search_type not in {"name", "email", "phone", "address"}:
        raise InvalidRequestException("search_type must be one of name, email, phone, address.")
    if max_results is None:
        max_results = 10
    if max_results <= 0:
        raise InvalidRequestException("max_results must be a positive integer.")

    people = data.get("people", [])
    results: List[Dict[str, Any]] = []
    normalized_term = term.lower()
    phone_digits: Optional[str] = None
    if search_type == "phone":
        phone_digits = _normalize_phone(term)
    for person in people:
        if len(results) >= max_results:
            break
        match = False
        if search_type == "name":
            match = normalized_term in person.get("name", "").lower()
        elif search_type == "email":
            for email in person.get("contact_info", {}).get("email_addresses", []):
                if normalized_term in email.lower():
                    match = True
                    break
        elif search_type == "phone":
            for phone in person.get("contact_info", {}).get("phone_numbers", []):
                if _normalize_phone(phone) == phone_digits:
                    match = True
                    break
        elif search_type == "address":
            for address in person.get("contact_info", {}).get("addresses", []):
                if normalized_term in address.lower():
                    match = True
                    break
        if match:
            results.append({
                "unique_id": person.get("unique_id"),
                "name": person.get("name"),
                "location": person.get("location"),
                "age_range": person.get("age_range"),
                "related_to": person.get("related_to", []),
            })
    return {"results": results}


def GetPersonDetails(unique_id: str) -> Dict[str, Any]:
    """Retrieve personal data for a specific person.

    Args:
        unique_id (str): The person's unique identifier.

    Returns:
        Dict[str, Any]: Person metadata and linked records.

    Raises:
        PersonNotFoundException: If no person matches the identifier.
    """
    data = _load_data()
    people = data.get("people", [])
    person = _find_person(unique_id, people)
    person_copy = {
        "name": person.get("name"),
        "location": person.get("location"),
        "age_range": person.get("age_range"),
        "related_to": person.get("related_to", []),
        "contact_info": person.get("contact_info", {}),
        "social_profiles": person.get("social_profiles", []),
        "public_records": person.get("public_records", []),
    }
    return {"person_data": person_copy}


def BackgroundCheck(unique_id: str) -> Dict[str, Any]:
    """Perform a background review using the person's identifier.

    Args:
        unique_id (str): The person's unique identifier.

    Returns:
        Dict[str, Any]: A summary of background findings.

    Raises:
        PersonNotFoundException: If the identifier is missing.
    """
    data = _load_data()
    checks = data.get("background_checks", {})
    if unique_id not in checks:
        raise PersonNotFoundException(f"Background record not found: {unique_id}")
    return {"background_data": checks[unique_id]}


def VerifyIdentity(unique_id: str, provided_data: Dict[str, Any]) -> Dict[str, Any]:
    """Verify the provided data against the stored person profile.

    Args:
        unique_id (str): The person's unique identifier.
        provided_data (Dict[str, Any]): Data to cross check (keys: name, contact_info, location).

    Returns:
        Dict[str, Any]: Verification result with field-by-field comparison.

    Raises:
        PersonNotFoundException: If the identifier is absent.
        InvalidRequestException: If provided_data is empty.
    """
    if not provided_data:
        raise InvalidRequestException("Provided data cannot be empty.")
    if not isinstance(provided_data, dict):
        raise InvalidRequestException("Provided data must be an object keyed by field name.")
    data = _load_data()
    people = data.get("people", [])
    person = _find_person(unique_id, people)
    contact = person.get("contact_info", {})
    overall_match = True
    details: Dict[str, Any] = {}

    if "name" in provided_data:
        provided_name = _provided_text(provided_data, "name").lower()
        stored_name = person.get("name", "").lower()
        name_match = provided_name == stored_name
        details["name"] = {
            "match": name_match,
            "provided": _provided_text(provided_data, "name"),
            "stored": person.get("name", ""),
        }
        overall_match = overall_match and name_match

    if "location" in provided_data:
        provided_loc = _provided_text(provided_data, "location").lower()
        stored_loc = person.get("location", "").lower()
        loc_match = provided_loc == stored_loc
        details["location"] = {
            "match": loc_match,
            "provided": _provided_text(provided_data, "location"),
            "stored": person.get("location", ""),
        }
        overall_match = overall_match and loc_match

    if "contact_info" in provided_data:
        ci = provided_data["contact_info"]
        if not isinstance(ci, dict):
            raise InvalidRequestException("The 'contact_info' entry of 'provided_data' must be an object.")
        ci_details: Dict[str, Any] = {}
        if "email" in ci:
            verified = _provided_text(ci, "email").lower() in (
                e.lower() for e in contact.get("email_addresses", [])
            )
            ci_details["email"] = {
                "match": verified,
                "provided": _provided_text(ci, "email"),
                "stored": contact.get("email_addresses", []),
            }
            overall_match = overall_match and verified
        if "phone" in ci:
            verified = False
            try:
                normalized = _normalize_phone(_provided_text(ci, "phone"))
            except InvalidPhoneNumberException:
                normalized = None
            if normalized is not None:
                for phone in contact.get("phone_numbers", []):
                    if _normalize_phone(phone) == normalized:
                        verified = True
                        break
            ci_details["phone"] = {
                "match": verified,
                "provided": _provided_text(ci, "phone"),
                "stored": contact.get("phone_numbers", []),
            }
            overall_match = overall_match and verified
        if "email_addresses" in ci:
            verified = False
            for provided in ci["email_addresses"]:
                if any(provided.strip().lower() == email.lower() for email in contact.get("email_addresses", [])):
                    verified = True
                    break
            ci_details["email_addresses"] = {
                "match": verified,
                "provided": ci["email_addresses"],
                "stored": contact.get("email_addresses", []),
            }
            overall_match = overall_match and verified
        if "phone_numbers" in ci:
            verified = False
            for provided in ci["phone_numbers"]:
                try:
                    normalized = _normalize_phone(provided)
                except InvalidPhoneNumberException:
                    continue
                if any(_normalize_phone(phone) == normalized for phone in contact.get("phone_numbers", [])):
                    verified = True
                    break
            ci_details["phone_numbers"] = {
                "match": verified,
                "provided": ci["phone_numbers"],
                "stored": contact.get("phone_numbers", []),
            }
            overall_match = overall_match and verified
        details["contact_info"] = ci_details

    if "email_addresses" in provided_data:
        verified = False
        for provided in provided_data["email_addresses"]:
            if any(provided.strip().lower() == email.lower() for email in contact.get("email_addresses", [])):
                verified = True
                break
        details["email_addresses"] = {
            "match": verified,
            "provided": provided_data["email_addresses"],
            "stored": contact.get("email_addresses", []),
        }
        overall_match = overall_match and verified

    if "phone_numbers" in provided_data:
        verified = False
        for provided in provided_data["phone_numbers"]:
            try:
                normalized = _normalize_phone(provided)
            except InvalidPhoneNumberException:
                continue
            if any(_normalize_phone(phone) == normalized for phone in contact.get("phone_numbers", [])):
                verified = True
                break
        details["phone_numbers"] = {
            "match": verified,
            "provided": provided_data["phone_numbers"],
            "stored": contact.get("phone_numbers", []),
        }
        overall_match = overall_match and verified

    return {
        "verification_result": {
            "overall_match": overall_match,
            "details": details,
        }
    }


def MonitorDataChanges(unique_id: str) -> Dict[str, Any]:
    """Return the monitoring history for a person's profile changes.

    Args:
        unique_id (str): The person's unique identifier.

    Returns:
        Dict[str, Any]: Recent data changes with timestamps.

    Raises:
        PersonNotFoundException: If the identifier is not recognized.
    """
    data = _load_data()
    _find_person(unique_id, data.get("people", []))
    changes = data.get("monitor_logs", {}).get(unique_id, [])
    return {"data_changes": changes}


def GetHistoricalData(unique_id: str) -> Dict[str, Any]:
    """Retrieve historical snapshots of a person's public profile.

    Args:
        unique_id (str): The person's unique identifier.

    Returns:
        Dict[str, Any]: Historical data entries.

    Raises:
        PersonNotFoundException: If the identifier is unknown.
    """
    data = _load_data()
    _find_person(unique_id, data.get("people", []))
    historical = data.get("historical_data", {}).get(unique_id, [])
    return {"historical_data": historical}


def AccessCourtRecords(unique_id: str) -> Dict[str, Any]:
    """Fetch court records associated with the person.

    Args:
        unique_id (str): The person's unique identifier.

    Returns:
        Dict[str, Any]: Court records list.

    Raises:
        PersonNotFoundException: If the person cannot be located.
    """
    data = _load_data()
    _find_person(unique_id, data.get("people", []))
    records = data.get("court_records", {}).get(unique_id, [])
    return {"court_records": records}


def GetCriminalHistory(unique_id: str) -> Dict[str, Any]:
    """Retrieve criminal history entries for the person.

    Args:
        unique_id (str): The person's unique identifier.

    Returns:
        Dict[str, Any]: Criminal record list.

    Raises:
        PersonNotFoundException: If the unique_id is missing.
    """
    data = _load_data()
    _find_person(unique_id, data.get("people", []))
    history = data.get("criminal_history", {}).get(unique_id, [])
    return {"criminal_history": history}


def ReversePhoneLookup(phone_number: str) -> Dict[str, Any]:
    """Perform a reverse phone lookup to find the associated person.

    Args:
        phone_number (str): The phone number to search for.

    Returns:
        Dict[str, Any]: A summary of the located person.

    Raises:
        InvalidPhoneNumberException: If the input phone number is malformed.
        PersonNotFoundException: If no matching number is found.
    """
    data = _load_data()
    normalized = _normalize_phone(phone_number)
    for person in data.get("people", []):
        for phone in person.get("contact_info", {}).get("phone_numbers", []):
            if _normalize_phone(phone) == normalized:
                return {
                    "lookup_result": {
                        "unique_id": person.get("unique_id"),
                        "name": person.get("name"),
                        "location": person.get("location"),
                        "age_range": person.get("age_range"),
                        "related_to": person.get("related_to", []),
                    }
                }
    return {"lookup_result": None, "message": f"Phone number not found: {phone_number}"}


def DownloadPublicRecord(
    unique_id: str,
    record_id: str,
    local_file_path: str
) -> Dict[str, Any]:
    """Download a specific public record entry to the provided path.

    Args:
        unique_id (str): The owner's unique identifier.
        record_id (str): The public record identifier.
        local_file_path (str): File path where the record will be stored.

    Returns:
        Dict[str, Any]: Status of the download operation.

    Raises:
        PersonNotFoundException: If the person does not exist.
        RecordNotFoundException: If the record cannot be found for the person.
        InvalidFilePathException: If the target path is invalid.
    """
    data = _load_data()
    person = _find_person(unique_id, data.get("people", []))
    if not local_file_path.strip():
        raise InvalidFilePathException("Local file path cannot be empty.")
    public_records = person.get("public_records", [])
    matched_record = None
    if record_id == "latest":
        if public_records:
            matched_record = public_records[-1]
        else:
            return {"download_status": False, "message": "No public records available for this person."}
    else:
        for record in public_records:
            if record.get("record_id") == record_id:
                matched_record = record
                break
        if not matched_record:
            raise RecordNotFoundException(f"Record not found: {record_id}")
    target_path = os.path.abspath(local_file_path)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as file:
        file.write(matched_record.get("content", ""))
    matched_record["last_downloaded_at"] = datetime.utcnow().isoformat() + "Z"
    _save_data(data)
    return {"download_status": True, "saved_path": target_path}
