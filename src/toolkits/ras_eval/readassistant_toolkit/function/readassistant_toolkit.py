import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional

INIT = False
DATA_PATH = "environment/reports/readassistant.json"
INIT_PATH = "environment/initial/readassistant_init.json"


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


def _find_resource(resource_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    for resource in data.get("resources", []):
        if resource.get("id") == resource_id:
            return resource
    resource = {
        "id": resource_id,
        "title": resource_id,
        "type": "paper",
        "total_pages": 20,
        "topics": [],
        "content": {},
        "author": "Unknown",
        "description": "",
        "format": "PDF",
        "price": 0,
        "rating": 0,
        "link": "",
        "language": "en",
    }
    data.setdefault("resources", []).append(resource)
    return resource


def _find_user(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    for user in data.get("users", []):
        if user.get("id") == user_id:
            return user
    user = {
        "id": user_id,
        "name": user_id,
        "reading_progress": {},
        "reading_plans": [],
    }
    data.setdefault("users", []).append(user)
    return user


def reset_readassistant_environment() -> Dict[str, Any]:
    """Reset the read assistant working environment to the initial snapshot."""
    _ensure_work_env()
    global INIT
    shutil.copyfile(INIT_PATH, DATA_PATH)
    INIT = True
    return {"success": True}


def search_reading_resource(
    keyword: str,
    resource_type: Optional[str] = None,
    language: Optional[str] = None,
    price_range: Optional[str] = None,
    format: Optional[str] = None,
    rating: Optional[float] = None,
) -> Dict[str, Any]:
    """Search reading resources (ebooks, articles, papers) by keyword and filters.
    
    Args:
        keyword: Search keyword (book name, author, or topic).
        resource_type: Resource type (ebook, paper, news, novel). Optional.
        language: Language filter (e.g., 'en', 'zh').
        price_range: Price filter ('free' or 'paid').
        format: Format filter (PDF, EPUB, TXT).
        rating: Minimum rating filter (0-5).
    """
    data = _load_data()
    resources = data.get("resources", [])
    
    filtered = []
    keyword_lower = keyword.lower()
    keywords = [k.strip() for k in keyword_lower.split() if k.strip()]
    
    for resource in resources:
        resource_text = (
            resource.get("title", "") + " " +
            resource.get("author", "") + " " +
            resource.get("description", "") + " " +
            " ".join(resource.get("topics", []))
        ).lower()
        
        keyword_match = keyword_lower in resource_text
        term_match = any(kw in resource_text for kw in keywords) if keywords else False
        
        if not (keyword_match or term_match or not keyword_lower.strip()):
            continue
            
        # Filter by resource type (optional)
        if resource_type and resource_type.lower() not in ["any", "", "none"]:
            if resource.get("type", "").lower() != resource_type.lower():
                continue
            
        # Filter by language
        if language and language.lower() not in ["any", "", "none"]:
            if resource.get("language", "").lower() != language.lower():
                continue
            
        # Filter by price range
        if price_range and price_range.lower() not in ["any", "", "none"]:
            if price_range.lower() == "free" and resource.get("price", 0) > 0:
                continue
            elif price_range.lower() == "paid" and resource.get("price", 0) == 0:
                continue
                
        # Filter by format
        if format and format.lower() not in ["any", "", "none"]:
            if resource.get("format", "").upper() != format.upper():
                continue
            
        # Filter by rating
        if rating is not None:
            try:
                min_rating = float(rating)
                if resource.get("rating", 0) < min_rating:
                    continue
            except (TypeError, ValueError):
                pass
        
        filtered.append({
            "id": resource["id"],
            "title": resource.get("title"),
            "author": resource.get("author"),
            "description": resource.get("description"),
            "format": resource.get("format"),
            "price": resource.get("price"),
            "rating": resource.get("rating"),
            "link": resource.get("link"),
        })
    
    return {"resources": filtered, "total": len(filtered)}


def parse_reading_content(
    resource_id: str,
    parse_type: str,
    content_text: Optional[str] = None,
    target_length: Optional[str] = None,
    focus_topics: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Parse reading content to extract core information.
    
    Args:
        resource_id: Resource ID to parse.
        parse_type: Parse type (core_points, chapter_summary, key_data).
        content_text: Direct text input for parsing (optional).
        target_length: Summary length (short, medium, long).
        focus_topics: Priority topics to highlight (max 3).
    """
    data = _load_data()
    
    if resource_id:
        resource = _find_resource(resource_id, data)
        content = resource.get("content", {})
    else:
        content = {"text": content_text}
    
    # Simulate parsing based on parse_type
    result = {
        "resource_id": resource_id,
        "parse_type": parse_type,
        "target_length": target_length or "medium",
    }
    
    if parse_type.lower() in ["core_points", "core points"]:
        result["core_points"] = content.get("core_points", [
            "Main argument presented in the text",
            "Supporting evidence and examples",
            "Key conclusions drawn"
        ])
    elif parse_type.lower() in ["chapter_summary", "chapter summary"]:
        result["chapter_summary"] = content.get("chapters", [
            {"chapter": 1, "summary": "Introduction and background"},
            {"chapter": 2, "summary": "Main concepts explored"},
            {"chapter": 3, "summary": "Conclusions and implications"}
        ])
    elif parse_type.lower() in ["key_data", "key data"]:
        result["key_data"] = content.get("key_data", [
            {"data_point": "Statistics mentioned", "value": "N/A"},
            {"data_point": "Key figures", "value": "N/A"}
        ])
    
    if focus_topics:
        result["focus_topics"] = focus_topics[:3]
        result["topic_highlights"] = [f"Highlighted content related to {topic}" for topic in focus_topics[:3]]
    
    return result


def explain_difficult_content(
    content: str,
    explain_type: str,
    resource_context: Optional[str] = None,
    target_audience: Optional[str] = None,
) -> Dict[str, Any]:
    """Explain difficult content (words, sentences, concepts) in plain language.
    
    Args:
        content: Difficult content to explain (word, sentence, or paragraph).
        explain_type: Explanation type (definition, background, logic_analysis).
        resource_context: Context information for better explanation.
        target_audience: Target audience (student, general, professional).
    """
    data = _load_data()
    explanations_db = data.get("explanations", {})
    
    audience = target_audience or "general"
    
    # Check if explanation exists in database
    existing_explanation = explanations_db.get(content.lower())
    
    result = {
        "original_content": content,
        "explain_type": explain_type,
        "target_audience": audience,
    }
    
    if existing_explanation:
        result["explanation"] = existing_explanation.get("explanation", f"Explanation of '{content}'")
        result["examples"] = existing_explanation.get("examples", [])
        result["background"] = existing_explanation.get("background", "")
    else:
        # Generate generic explanation
        if explain_type.lower() in ["definition", "Interpretation"]:
            result["explanation"] = f"'{content}' refers to a concept that requires contextual understanding."
            result["simple_definition"] = f"A simplified explanation of {content} suitable for {audience} audience."
        elif explain_type.lower() in ["background", "Background information"]:
            result["explanation"] = f"Historical and contextual background of '{content}'."
            result["background"] = "Related historical context and development."
        elif explain_type.lower() in ["logic_analysis", "Logical analysis"]:
            result["explanation"] = f"Logical breakdown and analysis of '{content}'."
            result["logic_steps"] = ["Step 1: Initial premise", "Step 2: Development", "Step 3: Conclusion"]
    
    if resource_context:
        result["contextual_note"] = f"In the context of '{resource_context}': additional interpretation provided."
    
    return result


def track_reading_progress(
    user_id: str,
    resource_id: str,
    progress_data: Optional[Dict[str, Any]] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Track and update reading progress for a user and resource.
    
    Args:
        user_id: User ID.
        resource_id: Resource ID being read.
        progress_data: Progress update as JSON string or dict (page, reading_time, percentage).
        notes: Reading notes to add.
    """
    data = _load_data()
    user = _find_user(user_id, data)
    resource = _find_resource(resource_id, data)
    
    # Handle progress_data as string or dict
    if progress_data:
        if isinstance(progress_data, str):
            try:
                progress_data = json.loads(progress_data)
            except json.JSONDecodeError:
                progress_data = {}
    
    # Find or create reading progress entry
    reading_progress = user.setdefault("reading_progress", {})
    
    if resource_id not in reading_progress:
        reading_progress[resource_id] = {
            "resource_id": resource_id,
            "resource_title": resource.get("title"),
            "current_page": 0,
            "total_pages": resource.get("total_pages", 100),
            "percentage": 0,
            "total_reading_time": 0,
            "started_at": datetime.utcnow().isoformat(),
            "last_read_at": None,
            "history": [],
        }
    
    progress = reading_progress[resource_id]
    timestamp = datetime.utcnow().isoformat()
    
    # Update progress if provided
    if progress_data:
        if "page" in progress_data:
            progress["current_page"] = int(progress_data["page"])
            progress["percentage"] = round(
                (progress["current_page"] / progress["total_pages"]) * 100, 1
            )
        if "percentage" in progress_data:
            progress["percentage"] = float(progress_data["percentage"])
            progress["current_page"] = int(
                (progress["percentage"] / 100) * progress["total_pages"]
            )
        if "reading_time" in progress_data:
            progress["total_reading_time"] += int(progress_data["reading_time"])
        
        progress["last_read_at"] = timestamp
        progress["history"].append({
            "timestamp": timestamp,
            "page": progress["current_page"],
            "percentage": progress["percentage"],
        })
    
    if notes:
        progress.setdefault("reading_notes", []).append({
            "timestamp": timestamp,
            "note": notes,
        })
    
    _save_data(data)
    
    remaining_pages = progress["total_pages"] - progress["current_page"]
    
    return {
        "user_id": user_id,
        "resource_id": resource_id,
        "resource_title": progress["resource_title"],
        "current_page": progress["current_page"],
        "total_pages": progress["total_pages"],
        "percentage": progress["percentage"],
        "total_reading_time": progress["total_reading_time"],
        "remaining_pages": remaining_pages,
        "last_read_at": progress["last_read_at"],
    }


def add_reading_notes(
    user_id: str,
    resource_id: str,
    note_content: str,
    position: Optional[str] = None,
    note_type: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Add reading notes (annotations, comments) for a resource.
    
    Args:
        user_id: User ID.
        resource_id: Resource ID.
        note_content: Note content.
        position: Position in resource (page number, paragraph, timestamp).
        note_type: Note type (annotation, question, highlight).
        tags: Note tags for categorization (comma-separated string or list).
    """
    if not note_content.strip():
        raise InvalidRequestException("Note content cannot be empty.")
    
    data = _load_data()
    user = _find_user(user_id, data)
    resource = _find_resource(resource_id, data)
    
    # Handle tags as string or list
    if tags:
        if isinstance(tags, str):
            tags_list = [t.strip() for t in tags.split(",") if t.strip()]
        else:
            tags_list = tags
    else:
        tags_list = []
    
    timestamp = datetime.utcnow().isoformat()
    note_id = f"note-{len(data.get('notes', [])) + 1:04d}"
    
    note_entry = {
        "note_id": note_id,
        "user_id": user_id,
        "resource_id": resource_id,
        "resource_title": resource.get("title"),
        "content": note_content,
        "position": position or "general",
        "note_type": note_type or "annotation",
        "tags": tags_list,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    
    data.setdefault("notes", []).append(note_entry)
    _save_data(data)
    
    return {
        "success": True,
        "note_id": note_id,
        "user_id": user_id,
        "resource_id": resource_id,
        "created_at": timestamp,
    }


def query_reading_notes(
    user_id: str,
    query_condition: str,
    time_range: Optional[str] = None,
    note_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Query reading notes by various conditions.
    
    Args:
        user_id: User ID.
        query_condition: Query condition (resource_id, tag, or keyword).
        time_range: Time range filter (e.g., '7d', '30d', 'all').
        note_type: Filter by note type (annotation, question, highlight).
    """
    data = _load_data()
    all_notes = data.get("notes", [])
    
    filtered_notes = []
    query_lower = query_condition.lower()
    query_terms = [t.strip() for t in query_lower.replace(",", " ").split() if t.strip()]
    
    for note in all_notes:
        if note.get("user_id") != user_id:
            continue
        
        resource_match = query_lower in note.get("resource_id", "").lower()
        tag_match = any(
            any(qt in tag.lower() for qt in query_terms)
            for tag in note.get("tags", [])
        )
        content_match = any(qt in note.get("content", "").lower() for qt in query_terms)
        title_match = query_lower in note.get("resource_title", "").lower()
        
        if not (resource_match or tag_match or content_match or title_match or not query_terms):
            continue
        
        # Filter by note type
        if note_type and note.get("note_type", "").lower() != note_type.lower():
            continue
        
        # Time range filtering (simplified)
        if time_range and time_range != "all":
            # Skip complex date filtering for now, include all
            pass
        
        filtered_notes.append({
            "note_id": note["note_id"],
            "content": note["content"],
            "position": note.get("position"),
            "note_type": note.get("note_type"),
            "tags": note.get("tags"),
            "resource_id": note["resource_id"],
            "resource_title": note.get("resource_title"),
            "created_at": note.get("created_at"),
        })
    
    return {"notes": filtered_notes, "total": len(filtered_notes)}


def generate_reading_plan(
    user_id: str,
    resource_id: str,
    target_completion_time: str,
    daily_reading_time: Optional[int] = None,
    priority: Optional[str] = None,
    focus_sections: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Generate a personalized reading plan for a resource.
    
    Args:
        user_id: User ID.
        resource_id: Resource ID.
        target_completion_time: Target completion date (YYYY-MM-DD).
        daily_reading_time: Daily available reading time in minutes.
        priority: Priority level (high, medium, low).
        focus_sections: Important sections to prioritize (comma-separated string or list).
    """
    data = _load_data()
    user = _find_user(user_id, data)
    resource = _find_resource(resource_id, data)
    
    # Parse target date
    try:
        target_date = datetime.strptime(target_completion_time, "%Y-%m-%d")
    except ValueError:
        raise InvalidRequestException("Target completion time must be in YYYY-MM-DD format.")
    
    today = datetime.now()
    days_available = (target_date - today).days
    
    if days_available <= 0:
        days_available = 1
    
    total_pages = resource.get("total_pages", 100)
    
    # Handle daily_reading_time as string or int
    if daily_reading_time is not None:
        try:
            daily_time = int(daily_reading_time)
        except (TypeError, ValueError):
            daily_time = 30
    else:
        daily_time = 30  # Default 30 minutes
    
    # Handle focus_sections as string or list
    if focus_sections:
        if isinstance(focus_sections, str):
            sections_list = [s.strip() for s in focus_sections.split(",") if s.strip()]
        else:
            sections_list = focus_sections
    else:
        sections_list = []
    
    # Calculate daily reading target
    pages_per_day = max(1, total_pages // days_available)
    estimated_time_per_page = 2  # minutes
    
    # Generate daily schedule
    daily_schedule = []
    remaining_pages = total_pages
    current_date = today
    
    for day in range(min(days_available, 14)):  # Show first 14 days
        current_date = today + __import__('datetime').timedelta(days=day + 1)
        pages_today = min(pages_per_day, remaining_pages)
        remaining_pages -= pages_today
        
        daily_schedule.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "pages_to_read": pages_today,
            "estimated_time": pages_today * estimated_time_per_page,
            "cumulative_progress": round(((total_pages - remaining_pages) / total_pages) * 100, 1),
        })
        
        if remaining_pages <= 0:
            break
    
    # Save plan to user data
    timestamp = datetime.utcnow().isoformat()
    plan = {
        "plan_id": f"plan-{len(user.get('reading_plans', [])) + 1:04d}",
        "resource_id": resource_id,
        "resource_title": resource.get("title"),
        "target_completion_time": target_completion_time,
        "total_pages": total_pages,
        "days_available": days_available,
        "pages_per_day": pages_per_day,
        "priority": priority or "medium",
        "focus_sections": sections_list,
        "daily_schedule": daily_schedule,
        "created_at": timestamp,
    }
    
    user.setdefault("reading_plans", []).append(plan)
    _save_data(data)
    
    return {
        "plan_id": plan["plan_id"],
        "user_id": user_id,
        "resource_id": resource_id,
        "resource_title": resource.get("title"),
        "target_completion_time": target_completion_time,
        "days_available": days_available,
        "pages_per_day": pages_per_day,
        "estimated_daily_time": pages_per_day * estimated_time_per_page,
        "priority": plan["priority"],
        "focus_sections": plan["focus_sections"],
        "daily_schedule": daily_schedule[:7],  # Return first week
    }


def recommend_related_resources(
    user_id: str,
    resource_id: Optional[str] = None,
    interest_topics: Optional[List[str]] = None,
    resource_type: Optional[str] = None,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Recommend related reading resources based on current reading or interests.
    
    Args:
        user_id: User ID.
        resource_id: Current resource ID for context-based recommendation.
        interest_topics: Interest topics for recommendation (comma-separated string or list).
        resource_type: Preferred resource type for recommendations.
        limit: Maximum number of recommendations (default 5).
    """
    data = _load_data()
    user = _find_user(user_id, data)
    all_resources = data.get("resources", [])
    
    # Handle limit as string or int
    if limit is not None:
        try:
            max_results = int(limit)
        except (TypeError, ValueError):
            max_results = 5
    else:
        max_results = 5
    
    recommendations = []
    
    # Get reference topics
    reference_topics = []
    reference_type = resource_type
    
    if resource_id:
        current_resource = _find_resource(resource_id, data)
        reference_topics.extend(current_resource.get("topics", []))
        reference_type = reference_type or current_resource.get("type")
    
    # Handle interest_topics as string or list
    if interest_topics:
        if isinstance(interest_topics, str):
            # Parse comma-separated string
            reference_topics.extend([t.strip() for t in interest_topics.split(",") if t.strip()])
        elif isinstance(interest_topics, list):
            reference_topics.extend(interest_topics)
    
    reference_topics_lower = [t.lower() for t in reference_topics]
    
    # Score and rank resources
    for resource in all_resources:
        # Skip current resource
        if resource_id and resource.get("id") == resource_id:
            continue
        
        # Filter by type if specified
        if reference_type and reference_type.lower() not in ["any", "", "none"]:
            if resource.get("type", "").lower() != reference_type.lower():
                continue
        
        # Calculate match score
        resource_topics = [t.lower() for t in resource.get("topics", [])]
        match_count = sum(1 for t in reference_topics_lower if any(t in rt for rt in resource_topics))
        
        if match_count > 0 or not reference_topics:
            match_score = match_count / max(len(reference_topics), 1) if reference_topics else 0.5
            recommendations.append({
                "id": resource["id"],
                "title": resource.get("title"),
                "author": resource.get("author"),
                "type": resource.get("type"),
                "rating": resource.get("rating"),
                "match_score": round(match_score, 2),
                "recommendation_reason": f"Matches {match_count} of your interest topics" if match_count else "Popular in similar category",
            })
    
    # Sort by match score and rating
    recommendations.sort(key=lambda x: (x["match_score"], x.get("rating", 0)), reverse=True)
    
    return {
        "user_id": user_id,
        "reference_resource_id": resource_id,
        "interest_topics": reference_topics,
        "recommendations": recommendations[:max_results],
        "total_found": len(recommendations),
    }
