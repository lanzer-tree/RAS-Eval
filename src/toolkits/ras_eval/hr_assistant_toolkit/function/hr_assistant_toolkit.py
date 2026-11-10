import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional

INIT = False
DATA_PATH = "environment/reports/HRAssistant.json"
INIT_PATH = "environment/initial/HRAssistant_init.json"


class InvalidRequestException(Exception):
    pass


class NotFoundException(Exception):
    pass


def _ensure_work_env():
    #Ensure working environment file exists by copying from init if necessary.
    global INIT
    if not os.path.exists(INIT_PATH):
        raise InvalidRequestException(f"Init file not found: {INIT_PATH}")
    if not os.path.exists(os.path.dirname(DATA_PATH)):
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


def _normalize_candidate_id(candidate_id: str) -> str:
    normalized = candidate_id.strip().replace("-", "_")
    if normalized.startswith("cand_") and not normalized.startswith("candidate_"):
        normalized = "candidate_" + normalized[len("cand_"):]
    return normalized


def _find_candidate(candidate_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    normalized = _normalize_candidate_id(candidate_id)
    for candidate in data.get("candidates", []):
        if candidate.get("id") == normalized:
            return candidate
    raise NotFoundException(f"Candidate '{candidate_id}' not found.")


def _parse_datetime(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M")
    except ValueError:
        raise InvalidRequestException(
            "Datetime must use the format 'YYYY-MM-DD HH:MM'."
        )


def reset_hr_assistant_environment() -> Dict[str, Any]:
    """Reset the HR assistant working environment to the initial snapshot."""
    _ensure_work_env()
    global INIT
    shutil.copyfile(INIT_PATH, DATA_PATH)
    INIT = True
    return {"success": True}


def list_candidates(
    status: Optional[str] = None,
    min_score: Optional[float] = None,
    role_keyword: Optional[str] = None,
    name: Optional[str] = None,
    name_keyword: Optional[str] = None,
) -> Dict[str, Any]:
    """List candidates with optional filters on status, score, role, and name.
    
    Args:
        status (Optional[str]): Filter candidates by status (e.g., 'interviewed', 'hired').
        min_score (Optional[float]): Minimum score threshold for filtering candidates.
        role_keyword (Optional[str]): Keyword to filter candidates by job role.
        name (Optional[str]): Exact name to filter candidates.
        name_keyword (Optional[str]): Keyword to filter candidates by name.
    """
    data = _load_data()
    threshold: Optional[float] = None
    if min_score is not None:
        try:
            threshold = float(min_score)
        except (TypeError, ValueError):
            raise InvalidRequestException("min_score must be a number.")
    filtered: List[Dict[str, Any]] = []
    status_filter = status and status.lower() not in {"any", "", "none"}
    role_filter = role_keyword and role_keyword.lower() not in {"any", "", "none"}
    name_value = name or name_keyword
    name_filter = name_value.strip() if (name_value and name_value.strip()) else None
    for candidate in data.get("candidates", []):
        if status_filter and candidate.get("status", "").lower() != status.lower():
            continue
        if threshold is not None and candidate.get("score", 0) < threshold:
            continue
        if role_filter and role_keyword.lower() not in candidate.get("role", "").lower():
            continue
        if name_filter and name_filter.lower() not in candidate.get("name", "").lower():
            continue
        filtered.append(candidate)
    sorted_candidates = sorted(
        filtered, key=lambda item: item.get("score", 0), reverse=True
    )
    summarized = []
    for candidate in sorted_candidates:
        summarized.append(
            {
                "id": candidate["id"],
                "name": candidate["name"],
                "role": candidate.get("role"),
                "score": candidate.get("score"),
                "status": candidate.get("status"),
                "key_skills": candidate.get("skills", [])[:5],
                "experience_years": candidate.get("experience_years"),
            }
        )
    return {"candidates": summarized}


def evaluate_candidate(
    candidate_id: str,
    score: float,
    highlights: List[str],
    concerns: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Score a resume and capture highlights plus optional concerns.
    
    Args:
        candidate_id (str): Unique identifier of the candidate to evaluate.
        score (float): Numerical score between 0 and 5 for the candidate.
        highlights (List[str]): List of positive highlights from the resume.
        concerns (Optional[List[str]]): Optional list of concerns about the candidate.
    """
    if not highlights:
        raise InvalidRequestException("At least one highlight is required.")
    data = _load_data()
    candidate = _find_candidate(candidate_id, data)
    numeric_score = float(score)
    if numeric_score < 0 or numeric_score > 5:
        raise InvalidRequestException("Score must be between 0 and 5.")
    candidate["score"] = round(numeric_score, 2)
    timestamp = datetime.utcnow().isoformat()
    candidate.setdefault("score_history", []).append(
        {
            "score": candidate["score"],
            "highlights": highlights,
            "concerns": concerns or [],
            "evaluated_at": timestamp,
        }
    )
    candidate["feedback"] = {
        "highlights": highlights,
        "concerns": concerns or [],
        "evaluated_at": timestamp,
    }
    candidate.setdefault("notes", []).append(
        {
            "type": "evaluation",
            "timestamp": timestamp,
            "text": f"Score updated to {candidate['score']}.",
        }
    )
    _save_data(data)
    return {
        "candidate_id": candidate_id,
        "score": candidate["score"],
        "status": candidate.get("status"),
        "updated_at": timestamp,
    }


def summarize_resume(candidate_id: str) -> Dict[str, Any]:
    """Return the key resume summary for a specific candidate.
    
    Args:
        candidate_id (str): Unique identifier of the candidate to summarize.
    """
    data = _load_data()
    candidate = _find_candidate(candidate_id, data)
    return {
        "candidate_id": candidate_id,
        "name": candidate.get("name"),
        "role": candidate.get("role"),
        "status": candidate.get("status"),
        "score": candidate.get("score"),
        "summary": candidate.get("resume_summary"),
        "highlights": candidate.get("resume_highlights", []),
        "skills": candidate.get("skills", []),
        "experience_years": candidate.get("experience_years"),
    }


def send_candidate_message(candidate_id: str, channel: str, message: str) -> Dict[str, Any]:
    """Log a message sent to a candidate through the specified channel.
    
    Args:
        candidate_id (str): Unique identifier of the candidate.
        channel (str): Communication channel (email, slack, or linkedin).
        message (str): The message content to send to the candidate.
    """
    if not message.strip():
        raise InvalidRequestException("Message body cannot be empty.")
    data = _load_data()
    candidate = _find_candidate(candidate_id, data)
    allowed = {"email", "slack", "linkedin"}
    if channel.lower() not in allowed:
        raise InvalidRequestException(
            f"Channel '{channel}' is not supported."
        )
    payload = {
        "candidate_id": candidate_id,
        "candidate_name": candidate.get("name"),
        "channel": channel.lower(),
        "message": message,
        "sent_at": datetime.utcnow().isoformat(),
    }
    data.setdefault("messages", []).append(payload)
    _save_data(data)
    return {"success": True, "candidate_id": candidate_id}


def schedule_interview(
    candidate_id: str,
    interviewer: str,
    start_time: str,
    end_time: str,
    location: str,
    mode: str = "onsite",
) -> Dict[str, Any]:
    """Schedule an interview for a candidate and validate the timing.
    
    Args:
        candidate_id (str): Unique identifier of the candidate.
        interviewer (str): Name or identifier of the interviewer.
        start_time (str): Interview start time in 'YYYY-MM-DD HH:MM' format.
        end_time (str): Interview end time in 'YYYY-MM-DD HH:MM' format.
        location (str): Physical location of the interview.
        mode (str): Interview mode (onsite, virtual, or phone), defaults to 'onsite'.
    """
    if not interviewer or not location:
        raise InvalidRequestException("Interviewer and location are required.")
    new_start = _parse_datetime(start_time)
    new_end = _parse_datetime(end_time)
    if new_start >= new_end:
        raise InvalidRequestException("start_time must be before end_time.")
    data = _load_data()
    _find_candidate(candidate_id, data)
    for interview in data.get("interviews", []):
        if interview.get("candidate_id") != candidate_id:
            continue
        existing_start = _parse_datetime(interview["start_time"])
        existing_end = _parse_datetime(interview["end_time"])
        if not (new_end <= existing_start or new_start >= existing_end):
            raise InvalidRequestException(
                "Candidate already has an overlapping interview."
            )
    interview_id = f"interview-{len(data.get('interviews', [])) + 1:03d}"
    record = {
        "interview_id": interview_id,
        "candidate_id": candidate_id,
        "interviewer": interviewer,
        "start_time": start_time,
        "end_time": end_time,
        "location": location,
        "mode": mode,
        "scheduled_at": datetime.utcnow().isoformat(),
    }
    data.setdefault("interviews", []).append(record)
    _save_data(data)
    return record
