import os
import shutil
import json
import uuid
from datetime import datetime, timedelta
import random

INIT = False
DATA_PATH = 'environment/reports/EmergencyManager.json'
INIT_PATH = 'environment/initial/EmergencyManager_init.json'

class InvalidRequestException(Exception):
    pass

class NotFoundException(Exception):
    pass

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

def _load_data():
    """Load data from the working environment file."""
    _ensure_work_env()
    with open(DATA_PATH, 'r') as f:
        return json.load(f)

def _save_data(data):
    """Save data to the working environment file."""
    with open(DATA_PATH, 'w') as f:
        json.dump(data, f, indent=4)

def create_dispatch_request(incident_location: str, resource_ids: list[str], incident_type: str, incident_severity: str, incident_description: str) -> dict:
    """
    Create an active new emergency dispatch request with available resources.

    Args:
        incident_location (str): The location of the incident in the street address format.
        resource_ids (list[str]): List of unique identifiers for the dispatch resources to be dispatched.
        incident_type (str): The primary type of the incident, one of ['Fire', 'Medical', 'Police'].
        incident_severity (str): The severity of the incident, one of ['Low', 'Medium', 'High'].
        incident_description (str): A brief description of the incident.
    """
    if incident_type not in ['Fire', 'Medical', 'Police']:
        raise InvalidRequestException("The 'incident_type' parameter is not one of ['Fire', 'Medical', 'Police'].")
    if incident_severity not in ['Low', 'Medium', 'High']:
        raise InvalidRequestException("The 'incident_severity' parameter is not one of ['Low', 'Medium', 'High'].")
    if not incident_location:
        raise InvalidRequestException("The 'incident_location' is invalid.")
    
    data = _load_data()
    resources = data['resources']
    incidents = data['incidents']
    
    # Check resources
    for rid in resource_ids:
        res = next((r for r in resources if r['resource_id'] == rid), None)
        if not res:
            raise NotFoundException(f"Resource {rid} does not exist.")
        if res['resource_status'] in ['Unavailable', 'Dispatched']:
            raise InvalidRequestException(f"Resource {rid} is not available.")
    
    # Create incident
    incident_id = str(uuid.uuid4())
    dispatch_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    incident = {
        'incident_id': incident_id,
        'incident_type': incident_type,
        'incident_location': incident_location,
        'incident_severity': incident_severity,
        'incident_status': 'Active',
        'dispatch_resource_ids': resource_ids,
        'dispatch_time': dispatch_time,
        'incident_description': incident_description
    }
    incidents.append(incident)
    
    # Update resources
    for rid in resource_ids:
        res = next(r for r in resources if r['resource_id'] == rid)
        res['resource_status'] = 'Dispatched'
        res['incident_id'] = incident_id
    
    _save_data(data)
    return {'incident_id': incident_id}

def redirect_dispatch_resources(resource_ids: list[str], target_type: str, incident_id_or_new_location: str) -> dict:
    """
    Redirect a specific dispatch resources to an already existing incident or a new location. If the location is provided, a new incident will be created and the dispatch resources will be redirected to the new incident.

    Args:
        resource_ids (list[str]): List of unique identifiers for the dispatch resources to be redirected.
        target_type (str): The type of the target location, one of ['Incident', 'Location'].
        incident_id_or_new_location (str): If 'target_type' is 'Incident', it is 'incident_id' of the incident to which the dispatch resources should be redirected. If 'target_type' is 'Location', it is the 'new_location' to which the dispatch resources should be redirected, in the street address format.
    """
    if not resource_ids:
        raise InvalidRequestException("The 'resource_ids' is not provided.")
    if target_type not in ['Incident', 'Location']:
        raise InvalidRequestException("The 'target_type' is not one of ['Incident', 'Location'].")
    if target_type == 'Location' and not incident_id_or_new_location:
        raise InvalidRequestException("The 'new_location' is invalid.")
    
    data = _load_data()
    resources = data['resources']
    incidents = data['incidents']
    
    # Check resources exist and are dispatched
    for rid in resource_ids:
        res = next((r for r in resources if r['resource_id'] == rid), None)
        if not res:
            raise NotFoundException(f"Resource {rid} does not exist.")
        if res['resource_status'] == 'Unavailable':
            raise InvalidRequestException(f"Resource {rid} is unavailable.")
    
    success = True
    incident_id = None
    
    if target_type == 'Incident':
        incident = next((i for i in incidents if i['incident_id'] == incident_id_or_new_location), None)
        if not incident:
            raise NotFoundException(f"Incident {incident_id_or_new_location} does not exist.")
        # Redirect to existing incident
        for rid in resource_ids:
            res = next(r for r in resources if r['resource_id'] == rid)
            res['incident_id'] = incident_id_or_new_location
            if incident_id_or_new_location not in incident['dispatch_resource_ids']:
                incident['dispatch_resource_ids'].append(rid)
    else:
        # Create new incident
        incident_id = str(uuid.uuid4())
        dispatch_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        incident = {
            'incident_id': incident_id,
            'incident_type': 'Unknown',  # Default
            'incident_location': incident_id_or_new_location,
            'incident_severity': 'Medium',  # Default
            'incident_status': 'Active',
            'dispatch_resource_ids': resource_ids,
            'dispatch_time': dispatch_time,
            'incident_description': 'Redirected incident'
        }
        incidents.append(incident)
        for rid in resource_ids:
            res = next(r for r in resources if r['resource_id'] == rid)
            res['incident_id'] = incident_id
    
    _save_data(data)
    result = {'success': success}
    if incident_id:
        result['incident_id'] = incident_id
    return result

def estimate_dispatch_time(resource_id: str, destination_location: str) -> dict:
    """
    Estimate the dispatch time for a specific dispatch resource to reach a specified location.

    Args:
        resource_id (str): The unique identifier of the dispatch resource.
        destination_location (str): The destination location for the dispatch resource, in the street address format.
    """
    if not resource_id or not destination_location:
        raise InvalidRequestException("The 'resource_id' or 'destination_location' is not provided or invalid.")
    
    data = _load_data()
    resources = data['resources']
    res = next((r for r in resources if r['resource_id'] == resource_id), None)
    if not res:
        raise NotFoundException(f"Resource {resource_id} does not exist.")
    
    # Simple estimation: random time between 5-30 minutes
    minutes = random.randint(5, 30)
    estimated_time = f"{minutes:02d}:00:00"
    return {'estimated_time': estimated_time}

def find_nearby_resources(location: str, resource_type: str = None, max_results: int = 10) -> dict:
    """
    Find nearby dispatch resources based on a specified location and resource type.

    Args:
        location (str): The location to find nearby dispatch resources, in the street address format.
        resource_type (Optional[str]): The type of the dispatch resources to find, one of ['Fire', 'Medical', 'Police']. If not provided, all types of dispatch resources will be considered.
        max_results (int): The maximum number of results to return. Default is 10.
    """
    if resource_type and resource_type not in ['Fire', 'Medical', 'Police']:
        raise InvalidRequestException("The 'resource_type' parameter is not one of ['Fire', 'Medical', 'Police'].")
    if not location:
        raise InvalidRequestException("The 'location' is not provided or invalid.")
    
    data = _load_data()
    resources = data['resources']
    
    nearby = []
    for res in resources:
        if resource_type and res['resource_type'] != resource_type:
            continue
        # Simple distance: random miles
        distance = random.uniform(0.5, 10.0)
        nearby.append({
            'resource_id': res['resource_id'],
            'resource_type': res['resource_type'],
            'resource_location': res['resource_location'],
            'resource_status': res['resource_status'],
            'incident_id': res.get('incident_id'),
            'distance_to_location': round(distance, 2)
        })
    
    nearby.sort(key=lambda x: x['distance_to_location'])
    nearby = nearby[:max_results]
    
    return {'nearby_resources': nearby}

def get_incident_data(incident_id: str) -> dict:
    """
    Retrieve incident data for a specified incident.

    Args:
        incident_id (str): The unique identifier of the incident to retrieve data for.
    """
    if not incident_id:
        raise InvalidRequestException("The 'incident_id' is not provided or invalid.")
    
    data = _load_data()
    incidents = data['incidents']
    incident = next((i for i in incidents if i['incident_id'] == incident_id), None)
    if not incident:
        raise NotFoundException(f"The 'incident_id' {incident_id} does not exist.")
    
    return {'incident_data': incident}

def get_resource_data(resource_id: str) -> dict:
    """
    Retrieve data for a specified dispatch resource.

    Args:
        resource_id (str): The unique identifier of the dispatch resource to retrieve data for.

    Returns:
        dict: A dictionary containing the resource_data.
    """
    if not resource_id:
        raise InvalidRequestException("The 'resource_id' is not provided or invalid.")
    
    data = _load_data()
    resources = data['resources']
    res = next((r for r in resources if r['resource_id'] == resource_id), None)
    if not res:
        raise NotFoundException(f"The 'resource_id' {resource_id} does not exist.")
    
    return {'resource_data': res}

def edit_incident(incident_id: str, incident_type: str = None, incident_severity: str = None, incident_description: str = None, incident_status: str = None, resource_ids: list[str] = None) -> dict:
    """
    Edit the data for a specified incident. This function should be used to assign new resources to an incident unless they have already been notified; it will NOT notify them of the assignment.

    Args:
        incident_id (str): The unique identifier of the incident to edit.
        incident_type (str, optional): If provided, the new type of the incident, one of ['Fire', 'Medical', 'Police'].
        incident_severity (str, optional): If provided, the new severity of the incident, one of ['Low', 'Medium', 'High'].
        incident_description (str, optional): If provided, the new description of the incident.
        incident_status (str, optional): If provided, the new status of the incident, one of ['Active', 'Closed'].
        resource_ids (list, optional): If provided, the new list of unique identifiers for the dispatch resources assigned to this incident.

    Returns:
        dict: A dictionary containing the edit_status.
    """
    if not incident_id:
        raise InvalidRequestException("The 'incident_id' is not provided or invalid.")
    
    data = _load_data()
    incidents = data['incidents']
    resources = data['resources']
    incident = next((i for i in incidents if i['incident_id'] == incident_id), None)
    if not incident:
        raise NotFoundException(f"The 'incident_id' {incident_id} does not exist.")
    
    if incident_type:
        if incident_type not in ['Fire', 'Medical', 'Police']:
            raise InvalidRequestException("The 'incident_type' parameter is not one of ['Fire', 'Medical', 'Police'].")
        incident['incident_type'] = incident_type
    if incident_severity:
        if incident_severity not in ['Low', 'Medium', 'High']:
            raise InvalidRequestException("The 'incident_severity' parameter is not one of ['Low', 'Medium', 'High'].")
        incident['incident_severity'] = incident_severity
    if incident_description:
        incident['incident_description'] = incident_description
    if incident_status:
        if incident_status not in ['Active', 'Closed']:
            raise InvalidRequestException("The 'incident_status' parameter is not one of ['Active', 'Closed'].")
        incident['incident_status'] = incident_status
    if resource_ids is not None:
        # Update resource assignments
        old_resources = set(incident['dispatch_resource_ids'])
        new_resources = set(resource_ids)
        to_remove = old_resources - new_resources
        to_add = new_resources - old_resources
        
        for rid in to_remove:
            res = next(r for r in resources if r['resource_id'] == rid)
            res['resource_status'] = 'Available'
            res['incident_id'] = None
        for rid in to_add:
            res = next(r for r in resources if r['resource_id'] == rid)
            if res['resource_status'] == 'Unavailable':
                raise InvalidRequestException(f"Resource {rid} is unavailable.")
            res['resource_status'] = 'Dispatched'
            res['incident_id'] = incident_id
        
        incident['dispatch_resource_ids'] = resource_ids
    
    _save_data(data)
    return {'edit_status': True}

def search_incidents(location: str, incident_type: str = None, severity: str = None, incident_status: str = None, max_results: int = 10) -> dict:
    """
    Search for incidents based on a specified location and incident type.

    Args:
        location (str): The location to search for incidents, in the street address format.
        incident_type (str, optional): The type of the incidents to search for, one of ['Fire', 'Medical', 'Police']. If not provided, all types of incidents will be considered.
        severity (str, optional): The severity of the incidents to search for, one of ['Low', 'Medium', 'High']. If not provided, all severities of incidents will be considered.
        incident_status (str, optional): If provided, the new status of the incident, one of ['Active', 'Closed'].
        max_results (int, optional): The maximum number of results to return. Default is 10.

    Returns:
        dict: A dictionary containing the incidents.
    """
    if incident_type and incident_type not in ['Fire', 'Medical', 'Police']:
        raise InvalidRequestException("The 'incident_type' parameter is not one of ['Fire', 'Medical', 'Police'].")
    if severity and severity not in ['Low', 'Medium', 'High']:
        raise InvalidRequestException("The 'severity' parameter is not one of ['Low', 'Medium', 'High'].")
    if not location:
        raise InvalidRequestException("The 'location' is invalid.")
    
    data = _load_data()
    incidents = data['incidents']
    
    results = []
    for inc in incidents:
        if incident_type and inc['incident_type'] != incident_type:
            continue
        if severity and inc['incident_severity'] != severity:
            continue
        if incident_status and inc['incident_status'] != incident_status:
            continue
        # Simple location match: if location in incident_location
        if location.lower() in inc['incident_location'].lower():
            results.append(inc)
    
    results = results[:max_results]
    return {'incidents': results}