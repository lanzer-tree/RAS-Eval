import json
import os
import shutil
from typing import List, Dict, Any

_WORKSPACE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
_init_candidate = os.path.join(_WORKSPACE, 'environment', 'initial', 'indoorRobot_init.json')
if not os.path.exists(_init_candidate) and os.path.exists('/workspace/environment/initial/indoorRobot_init.json'):
    _WORKSPACE = '/workspace'
DATA_PATH = os.path.join(_WORKSPACE, 'environment', 'reports', 'indoorRobot.json')
INIT_PATH = os.path.join(_WORKSPACE, 'environment', 'initial', 'indoorRobot_init.json')


class InvalidRequestException(Exception):
    pass


class NotFoundException(Exception):
    pass

INIT = False
def _ensure_work_env():
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


def _read_env() -> Dict[str, Any]:
    _ensure_work_env()
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _write_env(data: Dict[str, Any]):
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get_room(env: Dict[str, Any], room_id: str) -> Dict[str, Any]:
    for room in env.get('rooms', []):
        if room.get('room_id') == room_id:
            return room
    return None


def _get_current_room(env: Dict[str, Any]):
    return _get_room(env, env.get('current_room'))


def _find_object_in_room(room: Dict[str, Any], object_id: str):
    for obj in room.get('objects', []):
        if obj.get('object_id') == object_id:
            return obj
    return None


def _find_person_in_room(room: Dict[str, Any], person_id: str):
    for person in room.get('people', []):
        if person.get('person_id') == person_id:
            return person
    return None


def GetCurrentState() -> Dict[str, Any]:
    """Gets the current state of the indoor robot.

    Returns:
        dict: A dictionary containing current room and grabbed objects.
    """
    env = _read_env()
    return {
        'current_room': env.get('current_room'),
        'grabbed_objects': env.get('grabbed_objects', [])
    }


def ListRooms() -> Dict[str, Any]:
    """Lists all available rooms in the indoor environment.

    Returns:
        dict: A dictionary containing a list of rooms with their names and IDs.
    """
    env = _read_env()
    rooms = [{'room_name': r.get('room_name'), 'room_id': r.get('room_id')} for r in env.get('rooms', [])]
    return {'rooms': rooms}


def GoToRoom(room_id: str) -> Dict[str, Any]:
    """Moves the robot to a specified room.

    Args:
        room_id (str): The ID of the room to move to.

    Returns:
        dict: A dictionary containing a success message and the current room ID.
    """
    env = _read_env()
    if not _get_room(env, room_id):
        raise NotFoundException('room_id does not exist')
    env['current_room'] = room_id
    _write_env(env)
    return {'message': f'Moved to {room_id}', 'current_room': room_id}


def FindObjects(query: str) -> Dict[str, Any]:
    """Searches for objects in the current room matching the given query.

    Args:
        query (str): The search keyword to match against object names and descriptions.

    Returns:
        dict: A dictionary containing a list of matching objects with their details.
    """
    env = _read_env()
    room = _get_current_room(env)
    if not room:
        raise NotFoundException('Current room not set')
    q = (query or '').lower()
    results = []
    for obj in room.get('objects', []):
        name = (obj.get('object_name') or '').lower()
        desc = (obj.get('description') or '').lower()
        loc = (obj.get('object_location') or '').lower()
        if q in name or q in desc or q in loc:
            results.append({
                'object_id': obj.get('object_id'),
                'object_name': obj.get('object_name'),
                'object_location': obj.get('object_location'),
                'description': obj.get('description'),
                'can_be_grabbed': obj.get('can_be_grabbed', False)
            })
    return {'objects': results}


def LookAroundObject(object_id: str) -> Dict[str, Any]:
    """Finds objects around a specified target object or person in the current room.

    Args:
        object_id (str): The ID of the target object, person, or room to look around.

    Returns:
        dict: A dictionary containing a list of nearby objects with their details.
    """
    env = _read_env()
    for r in env.get('rooms', []):
        if object_id == r.get('room_id'):
            results = []
            for obj in r.get('objects', []):
                results.append({
                    'object_id': obj.get('object_id'),
                    'object_name': obj.get('object_name'),
                    'object_location': obj.get('object_location'),
                    'description': obj.get('description'),
                    'can_be_grabbed': obj.get('can_be_grabbed', False)
                })
            return {'objects': results}
    room = _get_current_room(env)
    if not room:
        raise NotFoundException('Current room not set')
    target = _find_object_in_room(room, object_id)
    if not target:
        grabbed = env.get('grabbed_objects', [])
        target = next((g for g in grabbed if g.get('object_id') == object_id), None)
    if not target:
        target = _find_person_in_room(room, object_id)
    if not target:
        raise NotFoundException('object_id does not exist in current room')
    around_ids = target.get('around', [])
    results = []
    for obj in room.get('objects', []):
        if obj.get('object_id') in around_ids:
            results.append({
                'object_id': obj.get('object_id'),
                'object_name': obj.get('object_name'),
                'object_location': obj.get('object_location'),
                'description': obj.get('description'),
                'can_be_grabbed': obj.get('can_be_grabbed', False)
            })
    return {'objects': results}


def GetAllowedOperations(target_object_id: str, interact_grabbed_object_ids: List[str] = None) -> Dict[str, Any]:
    """Gets the allowed operations for a target object or person in the current room.

    Args:
        target_object_id (str): The ID of the target object or person to query operations for.
        interact_grabbed_object_ids (list): List of grabbed object IDs to interact with.

    Returns:
        dict: A dictionary containing a list of allowed operations for the target.
    """
    env = _read_env()
    room = _get_current_room(env)
    if not room:
        raise NotFoundException('Current room not set')
    if target_object_id == room.get('room_id'):
        return {'allowed_operations': room.get('allowed_operations', [])}
    target = _find_object_in_room(room, target_object_id)
    if not target:
        grabbed = env.get('grabbed_objects', [])
        target = next((g for g in grabbed if g.get('object_id') == target_object_id), None)
    if not target:
        target = _find_person_in_room(room, target_object_id)
    if not target:
        raise NotFoundException('target_object_id does not exist in current room')

    if interact_grabbed_object_ids:
        grabbed_ids = {g.get('object_id') for g in env.get('grabbed_objects', [])}
        for gid in interact_grabbed_object_ids:
            if gid not in grabbed_ids:
                raise InvalidRequestException('interact_grabbed_object_ids contains unknown object')

    return {'allowed_operations': target.get('allowed_operations', [])}


def ApplyAllowedOperation(target_object_id: str, operation_id: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
    """Applies an allowed operation to a target object in the current room.

    Args:
        target_object_id (str): The ID of the target object to apply the operation to.
        operation_id (str): The ID of the operation to apply.
        arguments (dict): Optional arguments for the operation.

    Returns:
        dict: A dictionary containing the operation result message and updated grabbed objects.
    """
    env = _read_env()
    room = _get_current_room(env)
    if not room:
        raise NotFoundException('Current room not set')
    target = _find_object_in_room(room, target_object_id)
    grabbed = env.setdefault('grabbed_objects', [])
    if not target:
        g_target = next((g for g in grabbed if g.get('object_id') == target_object_id), None)
        if not g_target:
            raise NotFoundException('target_object_id does not exist')
        if operation_id.startswith('place'):
            target = g_target
        else:
            raise NotFoundException('operation not available for grabbed object')
    if not operation_id.startswith('place'):
        operations = target.get('allowed_operations', [])
        op = next((o for o in operations if o.get('operation_id') == operation_id), None)
        if not op:
            raise NotFoundException('operation_id does not exist')

    # grab operation
    if operation_id.startswith('grab'):
        if not target.get('can_be_grabbed', False):
            raise InvalidRequestException('Object cannot be grabbed')
        if len(grabbed) >= 5:
            raise InvalidRequestException('Cannot grab more than 5 objects')
        # already grabbed?
        if any(g.get('object_id') == target_object_id for g in grabbed):
            return {'message': 'Object already grabbed', 'updated_grabbed_objects': grabbed}
        grabbed.append({
            'object_id': target.get('object_id'),
            'object_name': target.get('object_name'),
            'description': target.get('description'),
            'object_location': target.get('object_location'),
            'can_be_grabbed': target.get('can_be_grabbed', False),
            'allowed_operations': target.get('allowed_operations', [])
        })
        # remove from room objects list
        room['objects'] = [o for o in room.get('objects', []) if o.get('object_id') != target_object_id]
        env['rooms'] = [r if r.get('room_id') != room.get('room_id') else room for r in env.get('rooms', [])]
        _write_env(env)
        return {'message': f'Grabbed {target_object_id}', 'updated_grabbed_objects': grabbed}

    # place operation
    if operation_id.startswith('place'):
        place_on = None
        if arguments:
            place_on = arguments.get('place_on')
        # ensure object is grabbed
        g_obj = next((g for g in grabbed if g.get('object_id') == target_object_id), None)
        if not g_obj:
            raise InvalidRequestException('Object is not grabbed')
        # remove from grabbed
        grabbed[:] = [g for g in grabbed if g.get('object_id') != target_object_id]
        # add back to room
        target_copy = {
            'object_id': g_obj.get('object_id'),
            'object_name': g_obj.get('object_name'),
            'description': g_obj.get('description'),
            'object_location': place_on or target.get('object_location') or 'on counter',
            'can_be_grabbed': target.get('can_be_grabbed', True),
            'allowed_operations': target.get('allowed_operations', [])
        }
        room.setdefault('objects', []).append(target_copy)
        env['rooms'] = [r if r.get('room_id') != room.get('room_id') else room for r in env.get('rooms', [])]
        _write_env(env)
        return {'message': f'Placed {target_object_id} at {target_copy.get("object_location")}', 'updated_grabbed_objects': grabbed}

    # toggle on/off operations
    if operation_id in ('turn_on', 'turn_off', 'turn_on_kettle', 'turn_off_kettle', 'turn_on_tv', 'turn_off_tv'):
        new_state = 'on' if 'on' in operation_id else 'off'
        target['status'] = new_state
        env['rooms'] = [r if r.get('room_id') != room.get('room_id') else room for r in env.get('rooms', [])]
        _write_env(env)
        return {'message': f'{target_object_id} turned {new_state}', 'updated_grabbed_objects': grabbed}

    # simple transform operations like cut/slice
    if operation_id in ('slice', 'cut', 'slice_apple'):
        target['description'] = f'Sliced {target.get("object_name", "object")}'
        env['rooms'] = [r if r.get('room_id') != room.get('room_id') else room for r in env.get('rooms', [])]
        _write_env(env)
        return {'message': f'{target_object_id} sliced', 'updated_grabbed_objects': grabbed}

    return {'message': 'Operation applied', 'updated_grabbed_objects': grabbed}


def FindPeople(query: str) -> Dict[str, Any]:
    """Searches for people in the current room matching the given query.

    Args:
        query (str): The search keyword to match against person names and descriptions.

    Returns:
        dict: A dictionary containing a list of matching people with their details.
    """
    env = _read_env()
    room = _get_current_room(env)
    if not room:
        raise NotFoundException('Current room not set')
    q = (query or '').lower()
    results = []
    for person in room.get('people', []):
        name = (person.get('person_name') or '').lower()
        desc = (person.get('description') or '').lower()
        if q in name or q in desc:
            results.append({
                'person_id': person.get('person_id'),
                'person_name': person.get('person_name'),
                'person_location': person.get('person_location'),
                'description': person.get('description')
            })
    return {'found_people': results}


def HandObjectsToPerson(object_ids: List[str], person_id: str) -> Dict[str, Any]:
    """Hands grabbed objects to a person in the current room.

    Args:
        object_ids (list): List of object IDs to hand to the person.
        person_id (str): The ID of the person to hand the objects to.

    Returns:
        dict: A dictionary containing a success message and updated grabbed objects.
    """
    env = _read_env()
    room = _get_current_room(env)
    if not room:
        raise NotFoundException('Current room not set')
    if not object_ids:
        raise InvalidRequestException('object_ids is empty')
    person = _find_person_in_room(room, person_id)
    if not person:
        raise NotFoundException('person_id does not exist in current room')
    grabbed = env.get('grabbed_objects', [])
    grabbed_ids = {g.get('object_id') for g in grabbed}
    for oid in object_ids:
        if oid not in grabbed_ids:
            raise InvalidRequestException('Some object_ids are not grabbed')
    # remove handed objects from grabbed
    handed = [g for g in grabbed if g.get('object_id') in object_ids]
    grabbed[:] = [g for g in grabbed if g.get('object_id') not in object_ids]
    env['grabbed_objects'] = grabbed
    _write_env(env)
    return {'message': f'Handed {len(handed)} object(s) to {person_id}', 'updated_grabbed_objects': grabbed}


__all__ = [
    'GetCurrentState', 'ListRooms', 'GoToRoom', 'FindObjects', 'LookAroundObject',
    'GetAllowedOperations', 'ApplyAllowedOperation', 'FindPeople', 'HandObjectsToPerson',
    'InvalidRequestException', 'NotFoundException'
]
