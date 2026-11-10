import datetime
import json
import os
import shutil
import uuid
from typing import Any, Dict, List, Optional

INIT_PATH = 'environment/initial/Quizlet_init.json'
DATA_PATH = 'environment/reports/Quizlet.json'
INIT = False


class InvalidRequestException(Exception):
    pass


class NotFoundException(Exception):
    pass


class PermissionDeniedException(Exception):
    pass


class DuplicateEntryException(Exception):
    pass


class LimitExceededException(Exception):
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


def _find_user(data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Find a user by ID."""
    for user in data.get('users', []):
        if user.get('user_id') == user_id:
            return user
    raise NotFoundException(f'User not found: {user_id}')


def _find_study_set(data: Dict[str, Any], set_id: str) -> Dict[str, Any]:
    """Find a study set by ID."""
    for study_set in data.get('study_sets', []):
        if study_set.get('set_id') == set_id:
            return study_set
    raise NotFoundException(f'Study set not found: {set_id}')


def _find_plan(data: Dict[str, Any], plan_id: str) -> Dict[str, Any]:
    """Find a recite plan by ID."""
    for plan in data.get('recite_plans', []):
        if plan.get('plan_id') == plan_id:
            return plan
    raise NotFoundException(f'Recite plan not found: {plan_id}')


def _find_quiz_task(data: Dict[str, Any], task_id: str) -> Dict[str, Any]:
    """Find a quiz task by ID."""
    for task in data.get('quiz_tasks', []):
        if task.get('task_id') == task_id:
            return task
    raise NotFoundException(f'Quiz task not found: {task_id}')


def _find_group(data: Dict[str, Any], group_id: str) -> Dict[str, Any]:
    """Find a study group by ID."""
    for group in data.get('study_groups', []):
        if group.get('group_id') == group_id:
            return group
    raise NotFoundException(f'Study group not found: {group_id}')


def _verify_set_access(data: Dict[str, Any], user_id: str, set_id: str, require_edit: bool = False) -> Dict[str, Any]:
    """Verify that a user has access to a study set."""
    study_set = _find_study_set(data, set_id)
    
    # Owner always has access
    if study_set.get('owner_id') == user_id:
        return study_set
    
    # Check visibility
    visibility = study_set.get('visibility', 'private')
    if visibility == 'public':
        if require_edit:
            # Check shared permissions
            for share in study_set.get('shared_with', []):
                if share.get('target_id') == user_id and share.get('permission') == 'edit':
                    return study_set
            raise PermissionDeniedException(f'User {user_id} does not have edit permission for study set {set_id}')
        return study_set
    
    # Check if shared with user
    for share in study_set.get('shared_with', []):
        if share.get('target_id') == user_id:
            if require_edit and share.get('permission') != 'edit':
                raise PermissionDeniedException(f'User {user_id} does not have edit permission for study set {set_id}')
            return study_set
    
    # Check if shared with user's groups
    user = _find_user(data, user_id)
    user_groups = user.get('groups', [])
    for share in study_set.get('shared_with', []):
        if share.get('target_type') == 'group' and share.get('target_id') in user_groups:
            if require_edit and share.get('permission') != 'edit':
                raise PermissionDeniedException(f'User {user_id} does not have edit permission for study set {set_id}')
            return study_set
    
    raise PermissionDeniedException(f'User {user_id} does not have access to study set {set_id}')


def create_study_set(
    user_id: str,
    set_title: str,
    study_items: List[Dict[str, str]],
    set_type: Optional[str] = "flashcard",
    tags: Optional[List[str]] = None,
    visibility: Optional[str] = "private"
) -> Dict[str, Any]:
    """
    Create a new study set (flashcards, knowledge points, or formulas).

    Args:
        user_id (str): The unique identifier of the user creating the study set.
        set_title (str): The title of the study set.
        study_items (list): A list of study items, each containing 'term' (question/term) and 'definition' (answer/definition).
        set_type (str, optional): The type of study set: 'flashcard', 'knowledge', or 'formula'. Default is 'flashcard'.
        tags (list, optional): A list of tags for categorization.
        visibility (str, optional): The visibility setting: 'private', 'public', or 'group'. Default is 'private'.

    Returns:
        dict: A dictionary containing the operation result, set ID, and preview link.
    """
    data = _load_data()
    _find_user(data, user_id)
    
    # Validate study items
    if not study_items or len(study_items) == 0:
        raise InvalidRequestException('study_items cannot be empty.')
    
    if len(study_items) > 100:
        raise InvalidRequestException('Cannot import more than 100 study items at once.')
    
    for item in study_items:
        if not item.get('term') or not item.get('definition'):
            raise InvalidRequestException('Each study item must have both term and definition.')
    
    # Validate set_type
    valid_types = ['flashcard', 'knowledge', 'formula']
    if set_type not in valid_types:
        raise InvalidRequestException(f"Invalid set_type: {set_type}. Must be one of {valid_types}.")
    
    # Validate visibility
    valid_visibility = ['private', 'public', 'group']
    if visibility not in valid_visibility:
        raise InvalidRequestException(f"Invalid visibility: {visibility}. Must be one of {valid_visibility}.")
    
    existing_ids = [s.get('set_id', '') for s in data.get('study_sets', [])]
    new_set_id = _generate_id('SET-', existing_ids)
    
    # Add unique IDs to study items
    for idx, item in enumerate(study_items):
        item['item_id'] = f"{new_set_id}-ITEM-{idx + 1:04d}"
        item['mastered'] = False
    
    new_study_set = {
        'set_id': new_set_id,
        'owner_id': user_id,
        'title': set_title,
        'set_type': set_type,
        'tags': tags or [],
        'visibility': visibility,
        'study_items': study_items,
        'item_count': len(study_items),
        'shared_with': [],
        'version_history': [],
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    data.setdefault('study_sets', []).append(new_study_set)
    _save_data(data)
    
    preview_link = f"https://quizlet.com/sets/{new_set_id}/preview"
    
    return {
        'success': True,
        'set_id': new_set_id,
        'preview_link': preview_link,
        'item_count': len(study_items),
        'message': f'Study set "{set_title}" created successfully with {len(study_items)} items.'
    }


def get_study_set(
    user_id: str,
    set_id: str,
    operation_type: str,
    update_data: Optional[Dict[str, Any]] = None,
    query_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Query, update, or delete a study set.

    Args:
        user_id (str): The unique identifier of the user.
        set_id (str): The unique identifier of the study set.
        operation_type (str): The type of operation: 'query', 'update', or 'delete'.
        update_data (dict, optional): Update content including title, study_items, or tags. Required for 'update' operation.
        query_fields (list, optional): Specific fields to return in query results.

    Returns:
        dict: A dictionary containing the operation result and study set information for query operations.
    """
    data = _load_data()
    operation_type = operation_type.lower()
    
    if operation_type == 'query':
        study_set = _verify_set_access(data, user_id, set_id, require_edit=False)
        
        if query_fields:
            result = {field: study_set.get(field) for field in query_fields if field in study_set}
        else:
            result = study_set.copy()
        
        return {'success': True, 'study_set': result}
    
    elif operation_type == 'update':
        if not update_data:
            raise InvalidRequestException('update_data is required for update operation.')
        
        study_set = _verify_set_access(data, user_id, set_id, require_edit=True)
        
        # Save version history
        version_record = {
            'version': len(study_set.get('version_history', [])) + 1,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'changes': list(update_data.keys())
        }
        study_set.setdefault('version_history', []).append(version_record)
        
        # Apply updates
        allowed_fields = ['title', 'study_items', 'tags', 'visibility', 'set_type']
        for key, value in update_data.items():
            if key in allowed_fields:
                if key == 'study_items':
                    # Re-index study items
                    for idx, item in enumerate(value):
                        if 'item_id' not in item:
                            item['item_id'] = f"{set_id}-ITEM-{idx + 1:04d}"
                        if 'mastered' not in item:
                            item['mastered'] = False
                    study_set['item_count'] = len(value)
                study_set[key] = value
        
        study_set['updated_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        _save_data(data)
        
        return {'success': True, 'set_id': set_id, 'message': f'Study set {set_id} updated successfully.'}
    
    elif operation_type == 'delete':
        study_set = _find_study_set(data, set_id)
        
        if study_set.get('owner_id') != user_id:
            raise PermissionDeniedException(f'Only the owner can delete study set {set_id}.')
        
        data['study_sets'] = [s for s in data.get('study_sets', []) if s.get('set_id') != set_id]
        _save_data(data)
        
        return {'success': True, 'message': f'Study set {set_id} deleted successfully.'}
    
    else:
        raise InvalidRequestException(f"Invalid operation_type: {operation_type}. Must be 'query', 'update', or 'delete'.")


def generate_recite_plan(
    user_id: str,
    set_id: str,
    target_days: int,
    daily_amount: Optional[int] = None,
    recite_mode: Optional[str] = "new_and_review"
) -> Dict[str, Any]:
    """
    Generate a personalized recitation plan based on the Ebbinghaus forgetting curve.

    Args:
        user_id (str): The unique identifier of the user.
        set_id (str): The unique identifier of the study set.
        target_days (int): The target number of days to complete the study set.
        daily_amount (int, optional): The daily learning amount. If not provided, it will be automatically calculated.
        recite_mode (str, optional): The recitation mode: 'new_and_review' or 'new_only'. Default is 'new_and_review'.

    Returns:
        dict: A dictionary containing the structured recitation plan with daily item lists and review rhythm.
    """
    data = _load_data()
    study_set = _verify_set_access(data, user_id, set_id, require_edit=False)
    
    study_items = study_set.get('study_items', [])
    total_items = len(study_items)
    
    if total_items == 0:
        raise InvalidRequestException('Study set has no items to generate a plan.')
    
    if target_days < 1:
        raise InvalidRequestException('target_days must be at least 1.')
    
    # Calculate daily amount if not provided
    if daily_amount is None:
        daily_amount = max(1, (total_items + target_days - 1) // target_days)
    
    # Validate recite_mode
    valid_modes = ['new_and_review', 'new_only']
    if recite_mode not in valid_modes:
        raise InvalidRequestException(f"Invalid recite_mode: {recite_mode}. Must be one of {valid_modes}.")
    
    existing_ids = [p.get('plan_id', '') for p in data.get('recite_plans', [])]
    new_plan_id = _generate_id('PLAN-', existing_ids)
    
    # Generate daily schedule based on Ebbinghaus curve
    # Review intervals: 1, 2, 4, 7, 15 days after learning
    review_intervals = [1, 2, 4, 7, 15]
    
    daily_schedule = []
    item_index = 0
    
    for day in range(1, target_days + 1):
        day_plan = {
            'day': day,
            'date': (datetime.datetime.now() + datetime.timedelta(days=day - 1)).strftime('%Y-%m-%d'),
            'new_items': [],
            'review_items': [],
            'status': 'pending'
        }
        
        # Add new items
        if item_index < total_items:
            new_count = min(daily_amount, total_items - item_index)
            day_plan['new_items'] = [study_items[i]['item_id'] for i in range(item_index, item_index + new_count)]
            item_index += new_count
        
        # Add review items (from previous days based on Ebbinghaus curve)
        if recite_mode == 'new_and_review':
            for interval in review_intervals:
                review_day = day - interval
                if review_day > 0 and review_day <= len(daily_schedule):
                    review_items = daily_schedule[review_day - 1].get('new_items', [])
                    day_plan['review_items'].extend(review_items)
        
        daily_schedule.append(day_plan)
    
    new_plan = {
        'plan_id': new_plan_id,
        'user_id': user_id,
        'set_id': set_id,
        'target_days': target_days,
        'daily_amount': daily_amount,
        'recite_mode': recite_mode,
        'total_items': total_items,
        'daily_schedule': daily_schedule,
        'current_day': 1,
        'progress': 0.0,
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'active'
    }
    
    data.setdefault('recite_plans', []).append(new_plan)
    _save_data(data)
    
    return {
        'success': True,
        'plan_id': new_plan_id,
        'total_items': total_items,
        'target_days': target_days,
        'daily_amount': daily_amount,
        'recite_mode': recite_mode,
        'daily_schedule': daily_schedule[:7],  # Return first 7 days preview
        'message': f'Recitation plan generated with {daily_amount} items per day over {target_days} days.'
    }


def start_quiz_practice(
    user_id: str,
    set_id: str,
    quiz_type: str,
    question_count: Optional[int] = 10,
    difficulty: Optional[str] = "random"
) -> Dict[str, Any]:
    """
    Start an online quiz practice session.

    Args:
        user_id (str): The unique identifier of the user.
        set_id (str): The unique identifier of the study set.
        quiz_type (str): The type of quiz: 'multiple_choice', 'fill_blank', or 'matching'.
        question_count (int, optional): The number of questions. Default is 10.
        difficulty (str, optional): The difficulty level: 'random', 'basic', or 'advanced'. Default is 'random'.

    Returns:
        dict: A dictionary containing the quiz task with question list and task ID.
    """
    data = _load_data()
    study_set = _verify_set_access(data, user_id, set_id, require_edit=False)
    
    study_items = study_set.get('study_items', [])
    
    if len(study_items) == 0:
        raise InvalidRequestException('Study set has no items to create a quiz.')
    
    # Validate quiz_type
    valid_types = ['multiple_choice', 'fill_blank', 'matching']
    if quiz_type not in valid_types:
        raise InvalidRequestException(f"Invalid quiz_type: {quiz_type}. Must be one of {valid_types}.")
    
    # Validate difficulty
    valid_difficulties = ['random', 'basic', 'advanced']
    if difficulty not in valid_difficulties:
        raise InvalidRequestException(f"Invalid difficulty: {difficulty}. Must be one of {valid_difficulties}.")
    
    # Adjust question count if needed
    actual_count = min(question_count, len(study_items))
    
    existing_ids = [t.get('task_id', '') for t in data.get('quiz_tasks', [])]
    new_task_id = _generate_id('QUIZ-', existing_ids)
    
    # Get user's mistake history for advanced difficulty
    user_mistakes = []
    for notebook in data.get('mistake_notebooks', []):
        if notebook.get('user_id') == user_id and notebook.get('set_id') == set_id:
            user_mistakes = notebook.get('mistakes', [])
            break
    
    mistake_item_ids = [m.get('item_id') for m in user_mistakes]
    
    # Select items based on difficulty
    import random
    if difficulty == 'advanced':
        # Prioritize items that were previously answered incorrectly
        priority_items = [item for item in study_items if item['item_id'] in mistake_item_ids]
        other_items = [item for item in study_items if item['item_id'] not in mistake_item_ids]
        random.shuffle(priority_items)
        random.shuffle(other_items)
        selected_items = (priority_items + other_items)[:actual_count]
    else:
        selected_items = random.sample(study_items, actual_count)
    
    # Generate questions based on quiz type
    questions = []
    for idx, item in enumerate(selected_items):
        question = {
            'question_id': f"{new_task_id}-Q{idx + 1:03d}",
            'item_id': item['item_id'],
            'term': item['term'],
            'correct_answer': item['definition'],
            'quiz_type': quiz_type
        }
        
        if quiz_type == 'multiple_choice':
            # Generate wrong options from other items
            other_defs = [i['definition'] for i in study_items if i['item_id'] != item['item_id']]
            wrong_options = random.sample(other_defs, min(3, len(other_defs)))
            all_options = wrong_options + [item['definition']]
            random.shuffle(all_options)
            question['options'] = all_options
        
        questions.append(question)
    
    new_task = {
        'task_id': new_task_id,
        'user_id': user_id,
        'set_id': set_id,
        'quiz_type': quiz_type,
        'difficulty': difficulty,
        'question_count': actual_count,
        'questions': questions,
        'answers': [],
        'status': 'in_progress',
        'started_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'score': None
    }
    
    data.setdefault('quiz_tasks', []).append(new_task)
    _save_data(data)
    
    # Return questions without correct answers
    public_questions = []
    for q in questions:
        pq = {
            'question_id': q['question_id'],
            'term': q['term'],
            'quiz_type': q['quiz_type']
        }
        if 'options' in q:
            pq['options'] = q['options']
        public_questions.append(pq)
    
    return {
        'success': True,
        'task_id': new_task_id,
        'quiz_type': quiz_type,
        'difficulty': difficulty,
        'question_count': actual_count,
        'questions': public_questions,
        'message': f'Quiz practice started with {actual_count} {quiz_type} questions.'
    }


def submit_quiz_answer(
    user_id: str,
    task_id: str,
    answers: List[Dict[str, str]],
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Submit quiz answers and get grading results.

    Args:
        user_id (str): The unique identifier of the user.
        task_id (str): The unique identifier of the quiz task.
        answers (list): A list of answer dictionaries, each containing 'question_id' and 'user_answer'.
        notes (str, optional): Optional notes about the answers, such as reasons for mistakes.

    Returns:
        dict: A dictionary containing grading results with score, wrong answers, and explanations.
    """
    data = _load_data()
    task = _find_quiz_task(data, task_id)
    
    if task.get('user_id') != user_id:
        raise PermissionDeniedException(f'User {user_id} does not have access to quiz task {task_id}.')
    
    if task.get('status') == 'completed':
        raise InvalidRequestException(f'Quiz task {task_id} has already been completed.')
    
    questions = task.get('questions', [])
    question_map = {q['question_id']: q for q in questions}
    
    correct_count = 0
    results = []
    wrong_items = []
    
    for answer in answers:
        question_id = answer.get('question_id')
        user_answer = answer.get('user_answer', '').strip()
        
        if question_id not in question_map:
            continue
        
        question = question_map[question_id]
        correct_answer = question.get('correct_answer', '')
        
        is_correct = user_answer.lower() == correct_answer.lower()
        
        if is_correct:
            correct_count += 1
        else:
            wrong_items.append({
                'item_id': question.get('item_id'),
                'term': question.get('term'),
                'correct_answer': correct_answer,
                'user_answer': user_answer,
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        results.append({
            'question_id': question_id,
            'term': question.get('term'),
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct
        })
    
    total_questions = len(questions)
    score = round((correct_count / total_questions) * 100, 2) if total_questions > 0 else 0
    
    # Update task
    task['answers'] = answers
    task['results'] = results
    task['score'] = score
    task['status'] = 'completed'
    task['completed_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if notes:
        task['notes'] = notes
    
    # Update mistake notebook
    if wrong_items:
        set_id = task.get('set_id')
        mistake_notebook = None
        for notebook in data.get('mistake_notebooks', []):
            if notebook.get('user_id') == user_id and notebook.get('set_id') == set_id:
                mistake_notebook = notebook
                break
        
        if not mistake_notebook:
            existing_ids = [n.get('notebook_id', '') for n in data.get('mistake_notebooks', [])]
            new_notebook_id = _generate_id('NOTEBOOK-', existing_ids)
            mistake_notebook = {
                'notebook_id': new_notebook_id,
                'user_id': user_id,
                'set_id': set_id,
                'mistakes': []
            }
            data.setdefault('mistake_notebooks', []).append(mistake_notebook)
        
        # Add new mistakes (avoid duplicates)
        existing_item_ids = [m.get('item_id') for m in mistake_notebook.get('mistakes', [])]
        for wrong in wrong_items:
            if wrong['item_id'] not in existing_item_ids:
                wrong['mastered'] = False
                mistake_notebook['mistakes'].append(wrong)
            else:
                # Update existing mistake with latest attempt
                for m in mistake_notebook['mistakes']:
                    if m['item_id'] == wrong['item_id']:
                        m['last_wrong_answer'] = wrong['user_answer']
                        m['last_attempt'] = wrong['timestamp']
                        m['attempt_count'] = m.get('attempt_count', 1) + 1
    
    _save_data(data)
    
    return {
        'success': True,
        'task_id': task_id,
        'score': score,
        'correct_count': correct_count,
        'total_questions': total_questions,
        'results': results,
        'wrong_count': len(wrong_items),
        'message': f'Quiz completed! Score: {score}% ({correct_count}/{total_questions})'
    }


def join_study_group(
    user_id: str,
    operation_type: str,
    group_name: Optional[str] = None,
    group_id: Optional[str] = None,
    invite_user_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create or join a study group.

    Args:
        user_id (str): The unique identifier of the user.
        operation_type (str): The type of operation: 'create' or 'join'.
        group_name (str, optional): The name of the group. Required for 'create' operation.
        group_id (str, optional): The unique identifier of the group. Required for 'join' operation.
        invite_user_ids (list, optional): A list of user IDs to invite when creating a group.

    Returns:
        dict: A dictionary containing the operation result and group information.
    """
    data = _load_data()
    user = _find_user(data, user_id)
    operation_type = operation_type.lower()
    
    # Check group limit
    user_groups = user.get('groups', [])
    if len(user_groups) >= 10 and operation_type in ['create', 'join']:
        raise LimitExceededException(f'User {user_id} has reached the maximum limit of 10 groups.')
    
    if operation_type == 'create':
        if not group_name:
            raise InvalidRequestException('group_name is required for creating a group.')
        
        if len(group_name) < 2 or len(group_name) > 50:
            raise InvalidRequestException('Group name must be between 2 and 50 characters.')
        
        existing_ids = [g.get('group_id', '') for g in data.get('study_groups', [])]
        new_group_id = _generate_id('GROUP-', existing_ids)
        
        members = [{'user_id': user_id, 'role': 'admin', 'joined_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]
        pending_invites = []
        
        # Process invitations
        if invite_user_ids:
            for invite_id in invite_user_ids:
                if invite_id != user_id:
                    try:
                        _find_user(data, invite_id)
                        pending_invites.append({
                            'user_id': invite_id,
                            'invited_by': user_id,
                            'invited_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'status': 'pending'
                        })
                    except NotFoundException:
                        pass  # Skip invalid user IDs
        
        new_group = {
            'group_id': new_group_id,
            'group_name': group_name,
            'creator_id': user_id,
            'visibility': 'private',
            'members': members,
            'pending_invites': pending_invites,
            'shared_sets': [],
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        data.setdefault('study_groups', []).append(new_group)
        
        # Add group to user
        user.setdefault('groups', []).append(new_group_id)
        
        _save_data(data)
        
        return {
            'success': True,
            'group_id': new_group_id,
            'group_name': group_name,
            'member_count': 1,
            'pending_invites': len(pending_invites),
            'message': f'Study group "{group_name}" created successfully.'
        }
    
    elif operation_type == 'join':
        if not group_id:
            raise InvalidRequestException('group_id is required for joining a group.')
        
        group = _find_group(data, group_id)
        
        # Check if already a member
        for member in group.get('members', []):
            if member.get('user_id') == user_id:
                raise DuplicateEntryException(f'User {user_id} is already a member of group {group_id}.')
        
        # Check visibility and invitation status
        if group.get('visibility') == 'private':
            # Check if user was invited
            invited = False
            for invite in group.get('pending_invites', []):
                if invite.get('user_id') == user_id and invite.get('status') == 'pending':
                    invite['status'] = 'accepted'
                    invited = True
                    break
            
            if not invited:
                raise PermissionDeniedException(f'Group {group_id} is private. You need an invitation to join.')
        
        # Add member
        group.setdefault('members', []).append({
            'user_id': user_id,
            'role': 'member',
            'joined_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Add group to user
        user.setdefault('groups', []).append(group_id)
        
        _save_data(data)
        
        return {
            'success': True,
            'group_id': group_id,
            'group_name': group.get('group_name'),
            'member_count': len(group.get('members', [])),
            'message': f'Successfully joined group "{group.get("group_name")}".'
        }
    
    else:
        raise InvalidRequestException(f"Invalid operation_type: {operation_type}. Must be 'create' or 'join'.")


def share_study_set(
    user_id: str,
    set_id: str,
    share_target: str,
    share_permission: Optional[str] = "view",
    expire_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Share a study set with another user or group.

    Args:
        user_id (str): The unique identifier of the user sharing the set.
        set_id (str): The unique identifier of the study set to share.
        share_target (str): The target to share with (user ID or group ID).
        share_permission (str, optional): The permission level: 'view' or 'edit'. Default is 'view'.
        expire_time (str, optional): The expiration time for the share (YYYY-MM-DD HH:MM:SS). Default is permanent.

    Returns:
        dict: A dictionary containing the share result and share link or invitation code.
    """
    data = _load_data()
    study_set = _find_study_set(data, set_id)
    
    if study_set.get('owner_id') != user_id:
        raise PermissionDeniedException(f'Only the owner can share study set {set_id}.')
    
    # Validate permission
    valid_permissions = ['view', 'edit']
    if share_permission not in valid_permissions:
        raise InvalidRequestException(f"Invalid share_permission: {share_permission}. Must be one of {valid_permissions}.")
    
    # Validate expire_time format
    if expire_time:
        try:
            datetime.datetime.strptime(expire_time, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise InvalidRequestException('expire_time must be in format YYYY-MM-DD HH:MM:SS.')
    
    # Determine target type
    target_type = 'user'
    if share_target.startswith('GROUP-'):
        target_type = 'group'
        _find_group(data, share_target)
    else:
        _find_user(data, share_target)
    
    # Check if already shared
    for share in study_set.get('shared_with', []):
        if share.get('target_id') == share_target:
            # Update existing share
            share['permission'] = share_permission
            share['expire_time'] = expire_time
            share['updated_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            _save_data(data)
            return {
                'success': True,
                'set_id': set_id,
                'share_target': share_target,
                'permission': share_permission,
                'message': f'Share permission updated for {share_target}.'
            }
    
    # Create new share
    share_code = str(uuid.uuid4())[:8].upper()
    share_link = f"https://quizlet.com/share/{set_id}/{share_code}"
    
    new_share = {
        'target_id': share_target,
        'target_type': target_type,
        'permission': share_permission,
        'share_code': share_code,
        'share_link': share_link,
        'expire_time': expire_time,
        'shared_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'active'
    }
    
    study_set.setdefault('shared_with', []).append(new_share)
    _save_data(data)
    
    return {
        'success': True,
        'set_id': set_id,
        'share_target': share_target,
        'target_type': target_type,
        'permission': share_permission,
        'share_link': share_link,
        'share_code': share_code,
        'message': f'Study set shared with {share_target} successfully.'
    }


def query_learning_progress(
    user_id: str,
    query_target: str,
    set_id: Optional[str] = None,
    time_range: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Query learning progress and statistics.

    Args:
        user_id (str): The unique identifier of the user.
        query_target (str): The target to query: 'study_set', 'recite_plan', or 'quiz_record'.
        set_id (str, optional): The specific study set ID to query.
        time_range (dict, optional): A dictionary with 'start_date' and 'end_date' in YYYY-MM-DD format.

    Returns:
        dict: A dictionary containing structured progress data with completion rate, accuracy, and weak areas.
    """
    data = _load_data()
    _find_user(data, user_id)
    
    query_target = query_target.lower()
    valid_targets = ['study_set', 'recite_plan', 'quiz_record']
    if query_target not in valid_targets:
        raise InvalidRequestException(f"Invalid query_target: {query_target}. Must be one of {valid_targets}.")
    
    result = {
        'user_id': user_id,
        'query_target': query_target,
        'query_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    if query_target == 'study_set':
        # Get user's study sets or specific set
        if set_id:
            study_set = _verify_set_access(data, user_id, set_id, require_edit=False)
            study_sets = [study_set]
        else:
            study_sets = [s for s in data.get('study_sets', []) if s.get('owner_id') == user_id]
        
        # Calculate mastery for each set
        sets_progress = []
        for s in study_sets:
            items = s.get('study_items', [])
            mastered = sum(1 for item in items if item.get('mastered', False))
            total = len(items)
            mastery_rate = round((mastered / total) * 100, 2) if total > 0 else 0
            sets_progress.append({
                'set_id': s.get('set_id'),
                'title': s.get('title'),
                'total_items': total,
                'mastered_items': mastered,
                'mastery_rate': mastery_rate
            })
        
        result['study_sets'] = sets_progress
        result['total_sets'] = len(sets_progress)
    
    elif query_target == 'recite_plan':
        plans = [p for p in data.get('recite_plans', []) if p.get('user_id') == user_id]
        
        if set_id:
            plans = [p for p in plans if p.get('set_id') == set_id]
        
        plans_progress = []
        for plan in plans:
            schedule = plan.get('daily_schedule', [])
            completed_days = sum(1 for day in schedule if day.get('status') == 'completed')
            total_days = len(schedule)
            progress_rate = round((completed_days / total_days) * 100, 2) if total_days > 0 else 0
            plans_progress.append({
                'plan_id': plan.get('plan_id'),
                'set_id': plan.get('set_id'),
                'total_days': total_days,
                'completed_days': completed_days,
                'progress_rate': progress_rate,
                'status': plan.get('status')
            })
        
        result['recite_plans'] = plans_progress
        result['total_plans'] = len(plans_progress)
    
    elif query_target == 'quiz_record':
        tasks = [t for t in data.get('quiz_tasks', []) if t.get('user_id') == user_id and t.get('status') == 'completed']
        
        if set_id:
            tasks = [t for t in tasks if t.get('set_id') == set_id]
        
        # Apply time range filter
        if time_range:
            start_date = time_range.get('start_date')
            end_date = time_range.get('end_date')
            filtered_tasks = []
            for t in tasks:
                completed_at = t.get('completed_at', '')[:10]
                if start_date and completed_at < start_date:
                    continue
                if end_date and completed_at > end_date:
                    continue
                filtered_tasks.append(t)
            tasks = filtered_tasks
        
        total_quizzes = len(tasks)
        avg_score = round(sum(t.get('score', 0) for t in tasks) / total_quizzes, 2) if total_quizzes > 0 else 0
        
        # Identify weak areas
        weak_items = {}
        for task in tasks:
            for r in task.get('results', []):
                if not r.get('is_correct'):
                    item_id = r.get('term')
                    weak_items[item_id] = weak_items.get(item_id, 0) + 1
        
        weak_areas = sorted(weak_items.items(), key=lambda x: x[1], reverse=True)[:10]
        
        result['quiz_statistics'] = {
            'total_quizzes': total_quizzes,
            'average_score': avg_score,
            'highest_score': max([t.get('score', 0) for t in tasks]) if tasks else 0,
            'lowest_score': min([t.get('score', 0) for t in tasks]) if tasks else 0
        }
        result['weak_areas'] = [{'term': term, 'wrong_count': count} for term, count in weak_areas]
        result['improvement_suggestion'] = 'Focus on the terms listed in weak_areas for targeted practice.' if weak_areas else 'Great job! Keep practicing to maintain your knowledge.'
    
    return result


def review_mistake_notebook(
    user_id: str,
    set_id: Optional[str] = None,
    review_mode: Optional[str] = "by_time",
    question_count: Optional[int] = 10
) -> Dict[str, Any]:
    """
    Review mistakes from the mistake notebook.

    Args:
        user_id (str): The unique identifier of the user.
        set_id (str, optional): The specific study set ID to filter mistakes.
        review_mode (str, optional): The review mode: 'by_time' or 'by_type'. Default is 'by_time'.
        question_count (int, optional): The number of questions to review. Default is 10.

    Returns:
        dict: A dictionary containing the mistake review task with questions, original wrong answers, and explanations.
    """
    data = _load_data()
    _find_user(data, user_id)
    
    # Validate review_mode
    valid_modes = ['by_time', 'by_type']
    if review_mode not in valid_modes:
        raise InvalidRequestException(f"Invalid review_mode: {review_mode}. Must be one of {valid_modes}.")
    
    # Collect mistakes
    all_mistakes = []
    for notebook in data.get('mistake_notebooks', []):
        if notebook.get('user_id') != user_id:
            continue
        if set_id and notebook.get('set_id') != set_id:
            continue
        
        for mistake in notebook.get('mistakes', []):
            if not mistake.get('mastered', False):
                mistake_copy = mistake.copy()
                mistake_copy['set_id'] = notebook.get('set_id')
                mistake_copy['notebook_id'] = notebook.get('notebook_id')
                all_mistakes.append(mistake_copy)
    
    if not all_mistakes:
        return {
            'success': True,
            'message': 'No mistakes to review. Great job!',
            'questions': [],
            'question_count': 0
        }
    
    # Sort by review mode
    import random
    if review_mode == 'by_time':
        all_mistakes.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    elif review_mode == 'by_type':
        # Prioritize frequently wrong items
        all_mistakes.sort(key=lambda x: x.get('attempt_count', 1), reverse=True)
    
    # Select questions
    selected_mistakes = all_mistakes[:question_count]
    
    # Generate review task
    existing_ids = [t.get('task_id', '') for t in data.get('quiz_tasks', [])]
    new_task_id = _generate_id('REVIEW-', existing_ids)
    
    questions = []
    for idx, mistake in enumerate(selected_mistakes):
        questions.append({
            'question_id': f"{new_task_id}-Q{idx + 1:03d}",
            'item_id': mistake.get('item_id'),
            'set_id': mistake.get('set_id'),
            'term': mistake.get('term'),
            'correct_answer': mistake.get('correct_answer'),
            'last_wrong_answer': mistake.get('user_answer') or mistake.get('last_wrong_answer'),
            'attempt_count': mistake.get('attempt_count', 1)
        })
    
    return {
        'success': True,
        'task_id': new_task_id,
        'review_mode': review_mode,
        'question_count': len(questions),
        'questions': questions,
        'message': f'Mistake review task created with {len(questions)} questions.',
        'tip': 'Review each term carefully and compare your last answer with the correct one.'
    }
