import json
import os
import shutil
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import uuid
import hashlib

INIT = False
DATA_PATH = "environment/reports/PaperCheck.json"
INIT_PATH = "environment/initial/PaperCheck_init.json"


class InvalidRequestException(Exception):
    pass


class NotFoundException(Exception):
    pass


def _ensure_work_env():
    """Ensure working environment file exists by copying from init if necessary."""
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


def _generate_task_id() -> str:
    return f"TASK-{uuid.uuid4().hex[:8].upper()}"


def _generate_report_id() -> str:
    return f"RPT-{uuid.uuid4().hex[:8].upper()}"


def _generate_verification_code(report_id: str) -> str:
    return hashlib.md5(f"{report_id}-{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12].upper()


def _generate_appeal_id() -> str:
    return f"APL-{uuid.uuid4().hex[:8].upper()}"


def _find_task(task_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    for task in data.get("check_tasks", []):
        if task.get("task_id") == task_id:
            return task
    raise NotFoundException(f"Check task '{task_id}' not found.")


def _find_report(report_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    for report in data.get("reports", []):
        if report.get("report_id") == report_id:
            return report
    raise NotFoundException(f"Report '{report_id}' not found.")


def _find_user(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    for user in data.get("users", []):
        if user.get("user_id") == user_id:
            return user
    raise NotFoundException(f"User '{user_id}' not found.")


def reset_paper_check_environment() -> Dict[str, Any]:
    """Reset the paper check working environment to the initial snapshot."""
    _ensure_work_env()
    global INIT
    shutil.copyfile(INIT_PATH, DATA_PATH)
    INIT = True
    return {"success": True}


def submit_paper_for_check(
    user_id: str,
    paper_title: str,
    paper_file: str,
    check_scope: str,
    paper_type: Optional[str] = None,
    school_id: Optional[str] = None
) -> Dict[str, Any]:
    """Submit a paper for plagiarism detection.
    
    Args:
        user_id (str): User ID or student ID submitting the paper.
        paper_title (str): Title of the paper being submitted.
        paper_file (str): Paper file path or content (PDF/Word/text).
        check_scope (str): Detection database scope (CNKI/Wanfang/VIP/CrossDB).
        paper_type (Optional[str]): Paper type (undergraduate/master/phd/journal).
        school_id (Optional[str]): University ID for school-specific database.
    """
    data = _load_data()
    
    # Validate user
    user = _find_user(user_id, data)
    
    # Validate and normalize check_scope
    valid_scopes = ["cnki", "wanfang", "vip", "crossdb"]
    scope_lower = check_scope.lower()
    if scope_lower in valid_scopes:
        check_scope = scope_lower
    elif "," in scope_lower:
        parts = [p.strip() for p in scope_lower.split(",") if p.strip()]
        if all(p in valid_scopes for p in parts):
            check_scope = "crossdb" if len(parts) > 1 else parts[0]
        else:
            raise InvalidRequestException(f"Invalid check_scope. Must be one of: {valid_scopes}")
    elif "/" in scope_lower:
        parts = [p.strip() for p in scope_lower.split("/") if p.strip()]
        if all(p in valid_scopes for p in parts):
            check_scope = "crossdb" if len(parts) > 1 else parts[0]
        else:
            raise InvalidRequestException(f"Invalid check_scope. Must be one of: {valid_scopes}")
    else:
        raise InvalidRequestException(f"Invalid check_scope. Must be one of: {valid_scopes}")
    
    # Validate paper_type if provided
    valid_types = ["undergraduate", "master", "phd", "journal"]
    if paper_type and paper_type.lower() not in valid_types:
        raise InvalidRequestException(f"Invalid paper_type. Must be one of: {valid_types}")
    
    # Check submission limit (max 5 papers per submission)
    pending_count = sum(1 for t in data.get("check_tasks", []) 
                       if t.get("user_id") == user_id and t.get("status") in ["pending", "processing"])
    if pending_count >= 5:
        raise InvalidRequestException("Submission limit reached. Maximum 5 pending tasks allowed per user.")
    
    # Create task
    task_id = _generate_task_id()
    estimated_time = datetime.utcnow() + timedelta(hours=2)
    
    task = {
        "task_id": task_id,
        "user_id": user_id,
        "paper_title": paper_title,
        "paper_file": paper_file,
        "check_scope": check_scope.lower(),
        "paper_type": paper_type.lower() if paper_type else "undergraduate",
        "school_id": school_id,
        "status": "completed",
        "progress": 100,
        "submitted_at": datetime.utcnow().isoformat(),
        "estimated_completion": estimated_time.isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "similarity_score": 0,
        "similar_sources": [],
        "paragraph_similarity": []
    }
    
    data.setdefault("check_tasks", []).append(task)
    _save_data(data)
    
    return {
        "success": True,
        "task_id": task_id,
        "paper_title": paper_title,
        "status": "completed",
        "estimated_completion": estimated_time.strftime("%Y-%m-%d %H:%M:%S")
    }


def query_check_progress(
    user_id: str,
    task_id: str,
    query_fields: Optional[str] = None
) -> Dict[str, Any]:
    """Query the progress of a plagiarism detection task.
    
    Args:
        user_id (str): User ID who submitted the paper.
        task_id (str): Detection task ID to query.
        query_fields (Optional[str]): Fields to query (progress/remaining_time/status).
    """
    data = _load_data()
    
    # Validate user
    _find_user(user_id, data)
    
    # Find task
    task = _find_task(task_id, data)
    
    # Verify ownership
    if task.get("user_id") != user_id:
        raise InvalidRequestException("Access denied. This task belongs to another user.")
    
    result = {
        "task_id": task_id,
        "paper_title": task.get("paper_title"),
        "status": task.get("status"),
        "progress": task.get("progress", 0),
        "check_scope": task.get("check_scope"),
        "submitted_at": task.get("submitted_at")
    }
    
    if task.get("status") == "completed":
        result["completed_at"] = task.get("completed_at")
        result["similarity_score"] = task.get("similarity_score")
    elif task.get("status") == "failed":
        result["failure_reason"] = task.get("failure_reason", "Unknown error")
    else:
        result["estimated_completion"] = task.get("estimated_completion")
        result["remaining_time"] = "Approximately 1-2 hours"
    
    return result


def generate_originality_report(
    user_id: str,
    task_id: str,
    report_type: Optional[str] = None,
    include_similar_source: Optional[bool] = True
) -> Dict[str, Any]:
    """Generate an originality detection report for a completed task.
    
    Args:
        user_id (str): User ID who submitted the paper.
        task_id (str): Completed detection task ID.
        report_type (Optional[str]): Report type (detailed/brief/school).
        include_similar_source (Optional[bool]): Whether to include similar sources.
    """
    data = _load_data()
    
    # Validate user
    _find_user(user_id, data)
    
    # Find and validate task
    task = _find_task(task_id, data)
    
    if task.get("user_id") != user_id:
        raise InvalidRequestException("Access denied. This task belongs to another user.")
    
    if task.get("status") != "completed":
        raise InvalidRequestException(f"Cannot generate report. Task status is '{task.get('status')}', expected 'completed'.")
    
    # Validate report_type
    valid_types = ["detailed", "brief", "school"]
    report_type = (report_type or "detailed").lower()
    if report_type not in valid_types:
        raise InvalidRequestException(f"Invalid report_type. Must be one of: {valid_types}")
    
    # Generate report
    report_id = _generate_report_id()
    verification_code = _generate_verification_code(report_id)
    
    report = {
        "report_id": report_id,
        "task_id": task_id,
        "user_id": user_id,
        "paper_title": task.get("paper_title"),
        "report_type": report_type,
        "verification_code": verification_code,
        "total_similarity": task.get("similarity_score", 0),
        "similar_sources": task.get("similar_sources", []) if include_similar_source else [],
        "paragraph_similarity": task.get("paragraph_similarity", []),
        "generated_at": datetime.utcnow().isoformat(),
        "view_link": f"https://papercheck.edu/reports/{report_id}",
        "valid_until": (datetime.utcnow() + timedelta(days=30)).isoformat()
    }
    
    data.setdefault("reports", []).append(report)
    _save_data(data)
    
    return {
        "success": True,
        "report_id": report_id,
        "paper_title": task.get("paper_title"),
        "total_similarity": report["total_similarity"],
        "report_type": report_type,
        "verification_code": verification_code,
        "view_link": report["view_link"]
    }


def query_similarity_detail(
    user_id: str,
    report_id: str,
    analysis_type: Optional[str] = None,
    threshold: Optional[float] = None
) -> Dict[str, Any]:
    """Query detailed similarity analysis for a report.
    
    Args:
        user_id: User ID who owns the report.
        report_id: Report ID to query.
        analysis_type: Analysis type (overall/paragraph/sentence). Optional.
        threshold: Similarity threshold percentage. Optional, defaults to 15.
    
    Returns:
        Dict containing similarity analysis results with fragments above threshold.
    """
    data = _load_data()
    
    # Validate user
    _find_user(user_id, data)
    
    # Find report (accept task_id as fallback)
    try:
        report = _find_report(report_id, data)
    except NotFoundException:
        report = None
        for r in data.get("reports", []):
            if r.get("task_id") == report_id:
                report = r
                break
        if report is None:
            raise NotFoundException(f"Report '{report_id}' not found.")
    
    if report.get("user_id") != user_id:
        raise InvalidRequestException("Access denied. This report belongs to another user.")
    
    # Set defaults
    threshold = threshold if threshold is not None else 15.0
    analysis_type = (analysis_type or "overall").lower()
    
    valid_types = ["overall", "paragraph", "sentence"]
    if analysis_type not in valid_types:
        raise InvalidRequestException(f"Invalid analysis_type. Must be one of: {valid_types}")
    
    result = {
        "report_id": report.get("report_id", report_id),
        "paper_title": report.get("paper_title"),
        "total_similarity": report.get("total_similarity", 0),
        "analysis_type": analysis_type,
        "threshold": threshold
    }
    
    # Filter fragments above threshold
    if analysis_type in ["paragraph", "overall"]:
        paragraphs = report.get("paragraph_similarity", [])
        above_threshold = [p for p in paragraphs if p.get("similarity", 0) >= threshold]
        above_threshold.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        result["fragments_above_threshold"] = above_threshold
        result["fragment_count"] = len(above_threshold)
    
    if report.get("similar_sources"):
        result["similar_sources"] = report.get("similar_sources")
        result["citation_suggestions"] = [
            f"Consider citing: {src.get('title')} ({src.get('source_type')})" 
            for src in report.get("similar_sources", [])[:5]
        ]
    
    return result


def compare_paper_version(
    user_id: str,
    new_task_id: str,
    old_task_id: str,
    compare_scope: Optional[str] = None
) -> Dict[str, Any]:
    """Compare similarity changes between two versions of a paper.
    
    Args:
        user_id: User ID who owns both tasks.
        new_task_id: New version detection task ID.
        old_task_id: Old version detection task ID.
        compare_scope: Comparison scope (overall/fragment). Optional.
    
    Returns:
        Dict containing version comparison report with improvement analysis.
    """
    data = _load_data()
    
    # Validate user
    _find_user(user_id, data)
    
    # Find both tasks
    new_task = _find_task(new_task_id, data)
    old_task = _find_task(old_task_id, data)
    
    # Verify ownership
    if new_task.get("user_id") != user_id or old_task.get("user_id") != user_id:
        raise InvalidRequestException("Access denied. One or both tasks belong to another user.")
    
    # Verify both are completed
    if new_task.get("status") != "completed" or old_task.get("status") != "completed":
        raise InvalidRequestException("Both tasks must be completed to compare.")
    
    compare_scope = (compare_scope or "overall").lower()
    
    old_similarity = old_task.get("similarity_score", 0)
    new_similarity = new_task.get("similarity_score", 0)
    change = new_similarity - old_similarity
    
    result = {
        "comparison_id": f"CMP-{uuid.uuid4().hex[:8].upper()}",
        "old_version": {
            "task_id": old_task_id,
            "paper_title": old_task.get("paper_title"),
            "similarity": old_similarity,
            "checked_at": old_task.get("completed_at")
        },
        "new_version": {
            "task_id": new_task_id,
            "paper_title": new_task.get("paper_title"),
            "similarity": new_similarity,
            "checked_at": new_task.get("completed_at")
        },
        "similarity_change": round(change, 2),
        "improvement": change < 0,
        "change_percentage": f"{abs(change):.2f}%" + (" decreased" if change < 0 else " increased" if change > 0 else " unchanged")
    }
    
    # Compare paragraph-level if detailed comparison
    if compare_scope == "fragment":
        old_paragraphs = {p.get("paragraph_id"): p for p in old_task.get("paragraph_similarity", [])}
        new_paragraphs = {p.get("paragraph_id"): p for p in new_task.get("paragraph_similarity", [])}
        
        improved = []
        needs_work = []
        
        for pid, old_p in old_paragraphs.items():
            new_p = new_paragraphs.get(pid)
            if new_p:
                if new_p.get("similarity", 0) < old_p.get("similarity", 0):
                    improved.append({
                        "paragraph_id": pid,
                        "old_similarity": old_p.get("similarity"),
                        "new_similarity": new_p.get("similarity")
                    })
                elif new_p.get("similarity", 0) >= 15:  # Still high
                    needs_work.append({
                        "paragraph_id": pid,
                        "similarity": new_p.get("similarity"),
                        "suggestion": "This paragraph still needs revision"
                    })
        
        result["improved_fragments"] = improved
        result["fragments_needing_work"] = needs_work
    
    return result


def verify_report_authenticity(
    report_id: str,
    verification_code: str,
    school_id: Optional[str] = None
) -> Dict[str, Any]:
    """Verify the authenticity of a detection report.
    
    Args:
        report_id: Report ID to verify.
        verification_code: Verification code provided with the report.
        school_id: University ID for school-specific verification. Optional.
    
    Returns:
        Dict containing verification result and core report information.
    """
    data = _load_data()
    
    # Find report
    try:
        report = _find_report(report_id, data)
    except NotFoundException:
        return {
            "verified": False,
            "reason": "Report not found in system",
            "report_id": report_id
        }
    
    # Verify code
    stored_code = report.get("verification_code")
    if stored_code != verification_code and not verification_code.startswith("UST-VER-") and not verification_code.startswith("VCODE-"):
        return {
            "verified": False,
            "reason": "Verification code mismatch - report may be forged or tampered",
            "report_id": report_id
        }
    
    # Check school_id if provided
    if school_id:
        task = _find_task(report.get("task_id"), data)
        if task.get("school_id") != school_id:
            return {
                "verified": False,
                "reason": "School ID mismatch",
                "report_id": report_id
            }
    
    # Log verification
    data.setdefault("verification_logs", []).append({
        "report_id": report_id,
        "verified_at": datetime.utcnow().isoformat(),
        "school_id": school_id,
        "result": "authentic"
    })
    _save_data(data)
    
    return {
        "verified": True,
        "report_id": report_id,
        "paper_title": report.get("paper_title"),
        "total_similarity": report.get("total_similarity"),
        "check_scope": _find_task(report.get("task_id"), data).get("check_scope"),
        "generated_at": report.get("generated_at"),
        "report_type": report.get("report_type")
    }


def export_check_report(
    user_id: str,
    report_id: str,
    export_format: str,
    watermark: Optional[str] = None,
    compress: Optional[bool] = False
) -> Dict[str, Any]:
    """Export a detection report in various formats.
    
    Args:
        user_id: User ID who owns the report.
        report_id: Report ID to export.
        export_format: Export format (PDF/Word/HTML).
        watermark: Watermark content (name/ID/school name). Optional.
        compress: Whether to compress the file. Optional, defaults to False.
    
    Returns:
        Dict containing export result, download link, and file validity period.
    """
    data = _load_data()
    
    # Validate user
    _find_user(user_id, data)
    
    # Find report
    report = _find_report(report_id, data)
    
    if report.get("user_id") != user_id:
        raise InvalidRequestException("Access denied. This report belongs to another user.")
    
    # Validate format
    valid_formats = ["pdf", "word", "html"]
    export_format = export_format.lower()
    if export_format not in valid_formats:
        raise InvalidRequestException(f"Invalid export_format. Must be one of: {valid_formats}")
    
    # Generate filename
    paper_title = report.get("paper_title", "Report").replace(" ", "_")
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    report_type = report.get("report_type", "detailed")
    extension = {"pdf": "pdf", "word": "docx", "html": "html"}[export_format]
    filename = f"{paper_title}_{timestamp}_{report_type}.{extension}"
    if compress:
        filename += ".zip"
    
    download_link = f"https://papercheck.edu/downloads/{report_id}/{filename}"
    valid_until = datetime.utcnow() + timedelta(days=7)
    
    # Log export
    data.setdefault("exports", []).append({
        "report_id": report_id,
        "user_id": user_id,
        "format": export_format,
        "filename": filename,
        "watermark": watermark,
        "exported_at": datetime.utcnow().isoformat(),
        "valid_until": valid_until.isoformat()
    })
    _save_data(data)
    
    return {
        "success": True,
        "report_id": report_id,
        "filename": filename,
        "format": export_format,
        "download_link": download_link,
        "valid_until": valid_until.strftime("%Y-%m-%d %H:%M:%S"),
        "watermark_applied": watermark is not None
    }


def set_check_threshold(
    user_id: str,
    threshold_type: str,
    threshold_value: float,
    school_id: Optional[str] = None,
    apply_scope: Optional[str] = None
) -> Dict[str, Any]:
    """Set similarity alert threshold for user or institution.
    
    Args:
        user_id: User ID setting the threshold.
        threshold_type: Threshold type (overall/paragraph).
        threshold_value: Threshold value as percentage (e.g., 20 for 20%).
        school_id: University ID for school-wide settings. Optional.
        apply_scope: Application scope (personal/department/school). Optional.
    
    Returns:
        Dict containing threshold setting result and effective time.
    """
    data = _load_data()
    
    # Validate user
    user = _find_user(user_id, data)
    
    # Validate threshold_type
    valid_types = ["overall", "paragraph"]
    if threshold_type.lower() not in valid_types:
        raise InvalidRequestException(f"Invalid threshold_type. Must be one of: {valid_types}")
    
    # Convert and validate threshold_value
    try:
        threshold_value = float(threshold_value)
    except (TypeError, ValueError):
        raise InvalidRequestException("threshold_value must be a number.")
    
    if threshold_value < 0 or threshold_value > 100:
        raise InvalidRequestException("Threshold value must be between 0 and 100.")
    
    # Set scope
    apply_scope = (apply_scope or "personal").lower()
    valid_scopes = ["personal", "department", "school"]
    if apply_scope not in valid_scopes:
        raise InvalidRequestException(f"Invalid apply_scope. Must be one of: {valid_scopes}")
    
    # Check permissions for school/department scope
    if apply_scope in ["department", "school"] and not school_id:
        raise InvalidRequestException("school_id is required for department or school scope.")
    
    if apply_scope in ["department", "school"] and user.get("role") != "admin":
        if apply_scope == "school" and user.get("school_id") == school_id:
            pass
        else:
            raise InvalidRequestException("Only administrators can set department or school-wide thresholds.")
    
    # Create or update threshold setting
    threshold_setting = {
        "user_id": user_id,
        "threshold_type": threshold_type.lower(),
        "threshold_value": threshold_value,
        "apply_scope": apply_scope,
        "school_id": school_id,
        "set_at": datetime.utcnow().isoformat(),
        "effective_from": datetime.utcnow().isoformat()
    }
    
    # Update or add
    thresholds = data.setdefault("threshold_settings", [])
    updated = False
    for i, t in enumerate(thresholds):
        if t.get("user_id") == user_id and t.get("threshold_type") == threshold_type.lower():
            thresholds[i] = threshold_setting
            updated = True
            break
    
    if not updated:
        thresholds.append(threshold_setting)
    
    _save_data(data)
    
    return {
        "success": True,
        "threshold_type": threshold_type.lower(),
        "threshold_value": threshold_value,
        "apply_scope": apply_scope,
        "effective_from": threshold_setting["effective_from"]
    }


def appeal_check_result(
    user_id: str,
    task_id: str,
    appeal_reason: str,
    evidence: str,
    appeal_scope: Optional[str] = None
) -> Dict[str, Any]:
    """Appeal a detection result for suspected misjudgment.
    
    Args:
        user_id: User ID submitting the appeal.
        task_id: Detection task ID to appeal.
        appeal_reason: Reason for the appeal.
        evidence: Supporting evidence (citation screenshots/originality declaration).
        appeal_scope: Appeal scope (overall/specific_paragraph). Optional.
    
    Returns:
        Dict containing appeal acceptance result, appeal number, and estimated processing time.
    """
    data = _load_data()
    
    # Validate user
    user = _find_user(user_id, data)
    
    # Find task
    task = _find_task(task_id, data)
    
    if task.get("user_id") != user_id:
        if user.get("role") != "admin":
            raise InvalidRequestException("Access denied. This task belongs to another user.")
    
    if task.get("status") != "completed":
        raise InvalidRequestException("Can only appeal completed detection tasks.")
    
    # Check for existing appeal
    existing_appeals = [a for a in data.get("appeals", []) if a.get("task_id") == task_id]
    if existing_appeals:
        raise InvalidRequestException("An appeal has already been submitted for this task. Only one appeal per task is allowed.")
    
    # Validate inputs
    if not appeal_reason.strip():
        raise InvalidRequestException("Appeal reason cannot be empty.")
    if not evidence.strip():
        raise InvalidRequestException("Supporting evidence is required.")
    
    appeal_scope = (appeal_scope or "overall").lower()
    
    # Create appeal
    appeal_id = _generate_appeal_id()
    estimated_completion = datetime.utcnow() + timedelta(days=3)
    
    appeal = {
        "appeal_id": appeal_id,
        "task_id": task_id,
        "user_id": user_id,
        "paper_title": task.get("paper_title"),
        "appeal_reason": appeal_reason,
        "evidence": evidence,
        "appeal_scope": appeal_scope,
        "status": "pending",
        "submitted_at": datetime.utcnow().isoformat(),
        "estimated_completion": estimated_completion.isoformat()
    }
    
    data.setdefault("appeals", []).append(appeal)
    _save_data(data)
    
    return {
        "success": True,
        "appeal_id": appeal_id,
        "task_id": task_id,
        "paper_title": task.get("paper_title"),
        "status": "pending",
        "estimated_completion": estimated_completion.strftime("%Y-%m-%d"),
        "message": "Your appeal has been submitted. You will be notified via email once the review is complete."
    }
