import datetime
import json
import os
import re
import shutil
from typing import Any, Dict, List, Optional

INIT_PATH = 'environment/initial/TeachAid_init.json'
DATA_PATH = 'environment/reports/TeachAid.json'
INIT = False


class InvalidRequestException(Exception):
    pass


class NotFoundException(Exception):
    pass


class PermissionDeniedException(Exception):
    pass


class DuplicateEntryException(Exception):
    pass


def _ensure_work_env() -> None:
    """Ensure working environment file exists by copying from init if necessary."""
    global INIT
    if not os.path.exists(INIT_PATH):
        raise InvalidRequestException(f'Init file not found: {INIT_PATH}')
    if not os.path.exists(os.path.dirname(DATA_PATH)):
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    if not INIT:
        shutil.copyfile(INIT_PATH, DATA_PATH)
        INIT = True
    if not os.path.exists(DATA_PATH):
        shutil.copyfile(INIT_PATH, DATA_PATH)


def _load_data() -> Dict[str, Any]:
    """Load data from the working environment file."""
    _ensure_work_env()
    with open(DATA_PATH, 'r', encoding='utf-8') as file:
        return json.load(file)


def _save_data(data: Dict[str, Any]) -> None:
    """Save data to the working environment file."""
    with open(DATA_PATH, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def _generate_id(prefix: str, existing_ids: List[str]) -> str:
    """Generate a unique ID with the given prefix."""
    max_num = 0
    for existing_id in existing_ids:
        if existing_id.startswith(prefix):
            try:
                num = int(existing_id[len(prefix):])
                max_num = max(max_num, num)
            except ValueError:
                continue
    return f"{prefix}{max_num + 1:04d}"


def _normalize_text(value: str) -> str:
    """Normalize an identifier for case-insensitive, symbol-free matching."""
    return re.sub(r"[^0-9a-z]", "", value.lower())


def _find_teacher(data: Dict[str, Any], teacher_id: str) -> Dict[str, Any]:
    """Find a teacher by ID."""
    for teacher in data.get('teachers', []):
        if teacher.get('teacher_id') == teacher_id:
            return teacher
    raise NotFoundException(f'Teacher not found: {teacher_id}')


def _find_course(data: Dict[str, Any], course_id: str) -> Dict[str, Any]:
    """Find a course by ID."""
    for course in data.get('courses', []):
        if course.get('course_id') == course_id:
            return course
    raise NotFoundException(f'Course not found: {course_id}')


def _find_assignment(data: Dict[str, Any], assignment_id: str) -> Dict[str, Any]:
    """Find an assignment by ID."""
    for assignment in data.get('assignments', []):
        if assignment.get('assignment_id') == assignment_id:
            return assignment
    raise NotFoundException(f'Assignment not found: {assignment_id}')


def _verify_teacher_course_permission(data: Dict[str, Any], teacher_id: str, course_id: str) -> None:
    """Verify that a teacher has permission to manage a course."""
    course = _find_course(data, course_id)
    if course.get('teacher_id') != teacher_id:
        raise PermissionDeniedException(f'Teacher {teacher_id} does not have permission for course {course_id}')


def manage_course(
    teacher_id: str,
    operation_type: str,
    course_id: Optional[str] = None,
    course_data: Optional[Dict[str, Any]] = None,
    query_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create, update, or query course information.

    Args:
        teacher_id (str): The unique identifier of the teacher.
        operation_type (str): The type of operation to perform. Must be one of 'create', 'update', or 'query'.
        course_id (str, optional): The unique identifier of the course. Required for 'update' and 'query' operations.
        course_data (dict, optional): Course information including name, subject, hours, and objectives. Required for 'create' and 'update' operations.
        query_fields (list, optional): Specific fields to return in query results.

    Returns:
        dict: A dictionary containing operation results and course information.
    """
    data = _load_data()
    operation_type = operation_type.lower()
    
    if course_data is not None and not isinstance(course_data, dict):
        raise InvalidRequestException('course_data must be an object with the course fields.')
    if operation_type == 'create':
        if not course_data:
            raise InvalidRequestException('course_data is required for creating a course.')
        _find_teacher(data, teacher_id)
        existing_ids = [c.get('course_id', '') for c in data.get('courses', [])]
        new_course_id = course_id if course_id else _generate_id('CRS-', existing_ids)
        new_course = {
            'course_id': new_course_id,
            'teacher_id': teacher_id,
            'name': course_data.get('name', 'Untitled Course'),
            'subject': course_data.get('subject', ''),
            'hours': course_data.get('hours', 0),
            'objectives': course_data.get('objectives', ''),
            'grade': course_data.get('grade', ''),
            'students': [],
            'resources': [],
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        data.setdefault('courses', []).append(new_course)
        _save_data(data)
        return {'success': True, 'course_id': new_course_id, 'message': f'Course {new_course_id} created successfully.'}
    
    elif operation_type == 'update':
        if not course_id:
            raise InvalidRequestException('course_id is required for updating a course.')
        if not course_data:
            raise InvalidRequestException('course_data is required for updating a course.')
        _verify_teacher_course_permission(data, teacher_id, course_id)
        course = _find_course(data, course_id)
        for key, value in course_data.items():
            if key not in ['course_id', 'teacher_id', 'created_at']:
                course[key] = value
        course['updated_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        _save_data(data)
        return {'success': True, 'course_id': course_id, 'message': f'Course {course_id} updated successfully.'}
    
    elif operation_type == 'query':
        if course_id:
            course = _find_course(data, course_id)
            if query_fields:
                result = {field: course.get(field) for field in query_fields if field in course}
            else:
                result = course.copy()
            return {'success': True, 'course': result}
        else:
            # Query all courses for this teacher
            teacher_courses = [c for c in data.get('courses', []) if c.get('teacher_id') == teacher_id]
            if query_fields:
                teacher_courses = [{field: c.get(field) for field in query_fields if field in c} for c in teacher_courses]
            return {'success': True, 'courses': teacher_courses, 'count': len(teacher_courses)}
    
    else:
        raise InvalidRequestException(f"Invalid operation_type: {operation_type}. Must be 'create', 'update', or 'query'.")


def batch_import_students(
    teacher_id: str,
    course_id: str,
    student_list: List[Dict[str, Any]],
    override_duplicate: bool = False
) -> Dict[str, Any]:
    """
    Batch import students into a course.

    Args:
        teacher_id (str): The unique identifier of the teacher.
        course_id (str): The unique identifier of the course.
        student_list (list): A list of student dictionaries containing student_id, name, class_name, and contact.
        override_duplicate (bool, optional): Whether to override duplicate entries. Default is False (skip).

    Returns:
        dict: A dictionary containing import results with success count, failure count, and failure details.
    """
    data = _load_data()
    _verify_teacher_course_permission(data, teacher_id, course_id)
    course = _find_course(data, course_id)
    
    if not isinstance(student_list, list) or not all(isinstance(student, dict) for student in student_list):
        raise InvalidRequestException('student_list must be a list of student objects.')
    existing_student_ids = {s.get('student_id') for s in course.get('students', [])}
    success_count = 0
    failure_count = 0
    failure_details = []
    
    for student in student_list:
        student_id = student.get('student_id')
        if not student_id:
            failure_count += 1
            failure_details.append({'student': student, 'reason': 'Missing student_id'})
            continue
        
        if not student.get('name'):
            failure_count += 1
            failure_details.append({'student_id': student_id, 'reason': 'Missing name'})
            continue
        
        if student_id in existing_student_ids:
            if override_duplicate:
                # Remove existing and add new
                course['students'] = [s for s in course.get('students', []) if s.get('student_id') != student_id]
                existing_student_ids.discard(student_id)
            else:
                failure_count += 1
                failure_details.append({'student_id': student_id, 'reason': 'Duplicate student_id (skipped)'})
                continue
        
        new_student = {
            'student_id': student_id,
            'name': student.get('name'),
            'class_name': student.get('class_name', ''),
            'contact': student.get('contact', ''),
            'imported_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        course.setdefault('students', []).append(new_student)
        existing_student_ids.add(student_id)
        success_count += 1
    
    _save_data(data)
    return {
        'success': True,
        'success_count': success_count,
        'failure_count': failure_count,
        'failure_details': failure_details,
        'total_students': len(course.get('students', []))
    }


def manage_course_resources(
    teacher_id: str,
    course_id: str,
    operation_type: str,
    resource_list: Optional[List[Dict[str, Any]]] = None,
    resource_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload, query, or delete course resources.

    Args:
        teacher_id (str): The unique identifier of the teacher.
        course_id (str): The unique identifier of the course.
        operation_type (str): The type of operation to perform. Must be 'upload', 'query', or 'delete'.
        resource_list (list, optional): A list of resource dictionaries containing filename, type, url, and description. Required for 'upload'.
        resource_id (str, optional): The unique identifier of the resource. Required for 'delete'.

    Returns:
        dict: A dictionary containing operation results and resource information.
    """
    data = _load_data()
    _verify_teacher_course_permission(data, teacher_id, course_id)
    course = _find_course(data, course_id)
    operation_type = operation_type.lower()
    
    if operation_type == 'upload':
        if not resource_list:
            raise InvalidRequestException('resource_list is required for uploading resources.')
        
        existing_ids = [r.get('resource_id', '') for r in course.get('resources', [])]
        uploaded = []
        for resource in resource_list:
            resource_id = _generate_id('RES-', existing_ids)
            existing_ids.append(resource_id)
            new_resource = {
                'resource_id': resource_id,
                'filename': resource.get('filename', 'untitled'),
                'type': resource.get('type', 'other'),
                'url': resource.get('url', ''),
                'description': resource.get('description', ''),
                'uploaded_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            course.setdefault('resources', []).append(new_resource)
            uploaded.append(resource_id)
        
        _save_data(data)
        return {'success': True, 'uploaded_resources': uploaded, 'message': f'{len(uploaded)} resource(s) uploaded.'}
    
    elif operation_type == 'query':
        resources = course.get('resources', [])
        return {'success': True, 'resources': resources, 'count': len(resources)}
    
    elif operation_type == 'delete':
        if not resource_id:
            raise InvalidRequestException('resource_id is required for deleting a resource.')
        
        original_count = len(course.get('resources', []))
        course['resources'] = [r for r in course.get('resources', []) if r.get('resource_id') != resource_id]
        
        if len(course.get('resources', [])) == original_count:
            raise NotFoundException(f'Resource not found: {resource_id}')
        
        # Log deletion
        data.setdefault('operation_logs', []).append({
            'action': 'delete_resource',
            'resource_id': resource_id,
            'course_id': course_id,
            'teacher_id': teacher_id,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        _save_data(data)
        return {'success': True, 'message': f'Resource {resource_id} deleted successfully.'}
    
    else:
        raise InvalidRequestException(f"Invalid operation_type: {operation_type}. Must be 'upload', 'query', or 'delete'.")


def publish_assignment(
    teacher_id: str,
    course_id: str,
    assignment_data: Dict[str, Any],
    resource_ids: Optional[List[str]] = None,
    is_group: bool = False,
    assignment_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Publish an assignment or learning task for a course.

    Args:
        teacher_id (str): The unique identifier of the teacher.
        course_id (str): The unique identifier of the course.
        assignment_data (dict): Assignment information including title, content, deadline, and points.
        resource_ids (list, optional): A list of associated resource IDs.
        is_group (bool, optional): Whether this is a group assignment. Default is False.
        assignment_id (str, optional): Custom assignment ID. If not provided, auto-generates one.

    Returns:
        dict: A dictionary containing publication results and assignment ID.
    """
    data = _load_data()
    _verify_teacher_course_permission(data, teacher_id, course_id)
    course = _find_course(data, course_id)
    
    if not assignment_data.get('title'):
        raise InvalidRequestException('assignment_data must include a title.')
    
    existing_ids = [a.get('assignment_id', '') for a in data.get('assignments', [])]
    if assignment_id:
        if assignment_id in existing_ids:
            raise DuplicateEntryException(f'Assignment ID already exists: {assignment_id}')
    else:
        assignment_id = _generate_id('ASN-', existing_ids)

    new_assignment = {
        'assignment_id': assignment_id,
        'course_id': course_id,
        'teacher_id': teacher_id,
        'title': assignment_data.get('title'),
        'content': assignment_data.get('content', ''),
        'deadline': assignment_data.get('deadline', ''),
        'points': assignment_data.get('points', 100),
        'resource_ids': resource_ids or [],
        'is_group': is_group,
        'submissions': [],
        'published_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'published'
    }
    
    data.setdefault('assignments', []).append(new_assignment)
    
    # Create notification record
    notification = {
        'notification_id': _generate_id('NTF-', [n.get('notification_id', '') for n in data.get('notifications', [])]),
        'type': 'assignment_published',
        'title': f'New Assignment: {assignment_data.get("title")}',
        'content': f'A new assignment has been published for {course.get("name")}. Deadline: {assignment_data.get("deadline", "TBD")}',
        'course_id': course_id,
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    data.setdefault('notifications', []).append(notification)
    
    _save_data(data)
    return {
        'success': True,
        'assignment_id': assignment_id,
        'message': f'Assignment {assignment_id} published successfully.',
        'notification_sent': True
    }


def grade_assignment(
    teacher_id: str,
    assignment_id: str,
    grading_data: List[Dict[str, Any]],
    batch_mode: str = 'custom',
    allow_regrade: bool = True
) -> Dict[str, Any]:
    """
    Grade assignments and record scores.

    Args:
        teacher_id (str): The unique identifier of the teacher.
        assignment_id (str): The unique identifier of the assignment.
        grading_data (list): A list of grading dictionaries containing student_id, score, and comment.
        batch_mode (str, optional): Grading mode - 'template' or 'custom'. Default is 'custom'.
        allow_regrade (bool, optional): Whether to allow regrading. Default is True.

    Returns:
        dict: A dictionary containing grading results and statistics.
    """
    data = _load_data()
    try:
        assignment = _find_assignment(data, assignment_id)
    except NotFoundException:
        # Auto-create the assignment if it doesn't exist
        existing_ids = [a.get('assignment_id', '') for a in data.get('assignments', [])]
        if assignment_id not in existing_ids:
            new_assignment = {
                'assignment_id': assignment_id,
                'teacher_id': teacher_id,
                'title': f'Assignment {assignment_id}',
                'content': '',
                'deadline': '',
                'points': 100,
                'resource_ids': [],
                'is_group': False,
                'submissions': [],
                'published_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'published'
            }
            data.setdefault('assignments', []).append(new_assignment)
            assignment = new_assignment
            _save_data(data)
            assignment = _find_assignment(data, assignment_id)
        else:
            raise

    if assignment.get('teacher_id') != teacher_id:
        raise PermissionDeniedException(f'Teacher {teacher_id} does not have permission for this assignment.')
    
    max_points = assignment.get('points', 100)
    graded_count = 0
    skipped_count = 0
    scores = []
    regrade_logs = []
    
    existing_grades = {g.get('student_id'): g for g in assignment.get('submissions', [])}
    
    for grade in grading_data:
        student_id = grade.get('student_id')
        score = grade.get('score', 0)
        comment = grade.get('comment', '')
        
        if not student_id:
            skipped_count += 1
            continue
        
        if score > max_points:
            score = max_points
        if score < 0:
            score = 0
        
        if student_id in existing_grades:
            if not allow_regrade:
                skipped_count += 1
                continue
            # Log regrade
            old_score = existing_grades[student_id].get('score', 0)
            regrade_logs.append({
                'student_id': student_id,
                'old_score': old_score,
                'new_score': score,
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            existing_grades[student_id]['score'] = score
            existing_grades[student_id]['comment'] = comment
            existing_grades[student_id]['graded_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            new_submission = {
                'student_id': student_id,
                'score': score,
                'comment': comment,
                'graded_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            assignment.setdefault('submissions', []).append(new_submission)
            existing_grades[student_id] = new_submission
        
        scores.append(score)
        graded_count += 1
    
    # Calculate statistics
    stats = {}
    if scores:
        stats = {
            'average': round(sum(scores) / len(scores), 2),
            'highest': max(scores),
            'lowest': min(scores),
            'total_graded': len(scores)
        }
    
    if regrade_logs:
        assignment.setdefault('regrade_history', []).extend(regrade_logs)
    
    _save_data(data)
    return {
        'success': True,
        'graded_count': graded_count,
        'skipped_count': skipped_count,
        'statistics': stats,
        'regrade_count': len(regrade_logs)
    }


def manage_grade_book(
    teacher_id: str,
    course_id: str,
    operation_type: str,
    assignment_ids: Optional[List[str]] = None,
    export_format: str = 'Excel'
) -> Dict[str, Any]:
    """
    Manage grade book including query, statistics, and export operations.

    Args:
        teacher_id (str): The unique identifier of the teacher.
        course_id (str): The unique identifier of the course.
        operation_type (str): The type of operation - 'query', 'statistics', or 'export'.
        assignment_ids (list, optional): Specific assignment IDs to include.
        export_format (str, optional): Export format - 'Excel' or 'CSV'. Default is 'Excel'.

    Returns:
        dict: A dictionary containing grade book data, statistics, or export link.
    """
    data = _load_data()
    _verify_teacher_course_permission(data, teacher_id, course_id)
    course = _find_course(data, course_id)
    operation_type = operation_type.lower()
    
    # Get all assignments for this course
    course_assignments = [a for a in data.get('assignments', []) if a.get('course_id') == course_id]
    if assignment_ids:
        course_assignments = [a for a in course_assignments if a.get('assignment_id') in assignment_ids]
    
    if operation_type == 'query':
        grade_book = []
        for student in course.get('students', []):
            student_grades = {
                'student_id': student.get('student_id'),
                'name': student.get('name'),
                'grades': []
            }
            for assignment in course_assignments:
                for submission in assignment.get('submissions', []):
                    if submission.get('student_id') == student.get('student_id'):
                        student_grades['grades'].append({
                            'assignment_id': assignment.get('assignment_id'),
                            'assignment_title': assignment.get('title'),
                            'score': submission.get('score'),
                            'max_points': assignment.get('points', 100)
                        })
            grade_book.append(student_grades)
        return {'success': True, 'grade_book': grade_book, 'student_count': len(grade_book)}
    
    elif operation_type == 'statistics':
        stats = {
            'course_id': course_id,
            'course_name': course.get('name'),
            'assignment_stats': []
        }
        for assignment in course_assignments:
            scores = [s.get('score', 0) for s in assignment.get('submissions', [])]
            if scores:
                assignment_stat = {
                    'assignment_id': assignment.get('assignment_id'),
                    'title': assignment.get('title'),
                    'average': round(sum(scores) / len(scores), 2),
                    'highest': max(scores),
                    'lowest': min(scores),
                    'submissions_count': len(scores)
                }
                stats['assignment_stats'].append(assignment_stat)
        return {'success': True, 'statistics': stats}
    
    elif operation_type == 'export':
        # Simulate export - return download link
        export_id = _generate_id('EXP-', [])
        export_filename = f"gradebook_{course_id}_{datetime.datetime.now().strftime('%Y%m%d')}.{export_format.lower()}"
        export_link = f"/downloads/exports/{export_filename}"
        
        return {
            'success': True,
            'export_id': export_id,
            'format': export_format,
            'download_link': export_link,
            'message': f'Grade book exported successfully. Student contact information has been desensitized.'
        }
    
    else:
        raise InvalidRequestException(f"Invalid operation_type: {operation_type}. Must be 'query', 'statistics', or 'export'.")


def process_student_interaction(
    teacher_id: str,
    interaction_type: str,
    content: str,
    student_id: Optional[str] = None,
    course_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process teacher-student interactions including Q&A and feedback.

    Args:
        teacher_id (str): The unique identifier of the teacher.
        interaction_type (str): The type of interaction - 'qa' (Q&A) or 'feedback'.
        content (str): The content of the interaction.
        student_id (str, optional): The specific student ID. If not provided, applies to all students.
        course_id (str, optional): The specific course ID for course-related interactions.

    Returns:
        dict: A dictionary containing interaction results and record ID.
    """
    data = _load_data()
    _find_teacher(data, teacher_id)
    
    interaction_type = interaction_type.lower()
    if interaction_type not in ['qa', 'feedback']:
        raise InvalidRequestException("interaction_type must be 'qa' or 'feedback'.")
    
    existing_ids = [i.get('interaction_id', '') for i in data.get('interactions', [])]
    interaction_id = _generate_id('INT-', existing_ids)
    
    recipient = student_id if student_id else 'all_students'
    if course_id:
        _verify_teacher_course_permission(data, teacher_id, course_id)
        course = _find_course(data, course_id)
        recipient = f"course_{course_id}" if not student_id else student_id
    
    new_interaction = {
        'interaction_id': interaction_id,
        'teacher_id': teacher_id,
        'interaction_type': interaction_type,
        'content': content,
        'recipient': recipient,
        'course_id': course_id,
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'sent'
    }
    
    data.setdefault('interactions', []).append(new_interaction)
    _save_data(data)
    
    return {
        'success': True,
        'interaction_id': interaction_id,
        'interaction_type': interaction_type,
        'recipient': recipient,
        'message': f'Interaction {interaction_id} recorded and sent successfully.'
    }


def send_notification(
    teacher_id: str,
    notification_data: Dict[str, Any],
    send_channel: str = 'in_app',
    schedule_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send teaching notifications to students.

    Args:
        teacher_id (str): The unique identifier of the teacher.
        notification_data (dict): Notification content including title, body, and recipients.
        send_channel (str, optional): The channel to send through - 'in_app', 'sms', or 'email'. Default is 'in_app'.
        schedule_time (str, optional): Scheduled time to send the notification in 'YYYY-MM-DD HH:MM:SS' format.

    Returns:
        dict: A dictionary containing send results and delivery statistics.
    """
    data = _load_data()
    _find_teacher(data, teacher_id)
    
    if not notification_data.get('title'):
        raise InvalidRequestException('notification_data must include a title.')
    if not notification_data.get('body'):
        raise InvalidRequestException('notification_data must include a body.')
    
    send_channel = send_channel.lower()
    if send_channel not in ['in_app', 'sms', 'email']:
        raise InvalidRequestException("send_channel must be 'in_app', 'sms', or 'email'.")
    
    existing_ids = [n.get('notification_id', '') for n in data.get('notifications', [])]
    notification_id = _generate_id('NTF-', existing_ids)
    
    recipients = notification_data.get('recipients', [])
    if not recipients:
        recipients = ['all']
    
    # Calculate delivery statistics (simulated)
    total_recipients = len(recipients) if recipients != ['all'] else 50  # Assume 50 for 'all'
    delivered = total_recipients
    failed = 0
    
    status = 'sent'
    if schedule_time:
        status = 'scheduled'
    
    new_notification = {
        'notification_id': notification_id,
        'teacher_id': teacher_id,
        'title': notification_data.get('title'),
        'body': notification_data.get('body'),
        'recipients': recipients,
        'send_channel': send_channel,
        'schedule_time': schedule_time,
        'status': status,
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'delivery_stats': {
            'total': total_recipients,
            'delivered': delivered,
            'failed': failed
        }
    }
    
    data.setdefault('notifications', []).append(new_notification)
    _save_data(data)
    
    return {
        'success': True,
        'notification_id': notification_id,
        'status': status,
        'delivery_stats': {
            'total': total_recipients,
            'delivered': delivered,
            'failed': failed
        },
        'message': f'Notification {notification_id} {"scheduled" if schedule_time else "sent"} successfully.'
    }


def sync_teaching_data(
    teacher_id: str,
    sync_type: str,
    backup_path: Optional[str] = None,
    sync_platform: str = 'cloud'
) -> Dict[str, Any]:
    """
    Synchronize and backup teaching data.

    Args:
        teacher_id (str): The unique identifier of the teacher.
        sync_type (str): The type of data to sync - 'courses', 'students', 'grades', or 'all'.
        backup_path (str, optional): Custom backup file path.
        sync_platform (str, optional): Platform to sync to - 'academic_system' or 'cloud'. Default is 'cloud'.

    Returns:
        dict: A dictionary containing sync results and backup information.
    """
    data = _load_data()
    _find_teacher(data, teacher_id)
    
    sync_type = sync_type.lower()
    valid_sync_types = ['courses', 'students', 'grades', 'all']
    if sync_type not in valid_sync_types:
        raise InvalidRequestException(f"sync_type must be one of {valid_sync_types}.")
    
    sync_platform = sync_platform.lower()
    if sync_platform not in ['academic_system', 'cloud']:
        raise InvalidRequestException("sync_platform must be 'academic_system' or 'cloud'.")
    
    # Determine what to sync
    sync_data = {}
    teacher_courses = [c for c in data.get('courses', []) if c.get('teacher_id') == teacher_id]
    
    if sync_type in ['courses', 'all']:
        sync_data['courses'] = len(teacher_courses)
    
    if sync_type in ['students', 'all']:
        total_students = sum(len(c.get('students', [])) for c in teacher_courses)
        sync_data['students'] = total_students
    
    if sync_type in ['grades', 'all']:
        teacher_assignment_ids = [a.get('assignment_id') for a in data.get('assignments', []) if a.get('teacher_id') == teacher_id]
        total_grades = sum(len(a.get('submissions', [])) for a in data.get('assignments', []) if a.get('assignment_id') in teacher_assignment_ids)
        sync_data['grades'] = total_grades
    
    # Generate backup path if not provided
    if not backup_path:
        backup_path = f"/backups/teacher_{teacher_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Log sync operation
    sync_log = {
        'sync_id': _generate_id('SYN-', [s.get('sync_id', '') for s in data.get('sync_logs', [])]),
        'teacher_id': teacher_id,
        'sync_type': sync_type,
        'sync_platform': sync_platform,
        'backup_path': backup_path,
        'synced_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'data_summary': sync_data
    }
    
    data.setdefault('sync_logs', []).append(sync_log)
    _save_data(data)
    
    return {
        'success': True,
        'sync_id': sync_log['sync_id'],
        'sync_type': sync_type,
        'sync_platform': sync_platform,
        'backup_path': backup_path,
        'data_synced': sync_data,
        'message': f'Teaching data synchronized to {sync_platform} successfully.'
    }
