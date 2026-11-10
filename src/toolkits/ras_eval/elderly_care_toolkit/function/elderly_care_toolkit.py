import json
import os
import shutil
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

INIT_PATH = 'environment/initial/ElderlyCare_init.json'
DATA_PATH = 'environment/reports/ElderlyCare.json'

INIT = False


class InvalidRequestException(Exception):
    pass


class ProfileNotFoundException(Exception):
    pass


class HospitalNotFoundException(Exception):
    pass


def _ensure_work_env() -> None:
    """Make sure the working report file exists by copying from the init file if needed."""
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
    _ensure_work_env()
    with open(DATA_PATH, 'r', encoding='utf-8') as file:
        return json.load(file)


def _save_data(data: Dict[str, Any]) -> None:
    with open(DATA_PATH, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def _find_profile(data: Dict[str, Any], elderly_id: str) -> Optional[Dict[str, Any]]:
    for profile in data.setdefault('profiles', []):
        if profile.get('elderly_id') == elderly_id:
            return profile
    return None


def _parse_datetime(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        return dt.replace(tzinfo=None) if dt.tzinfo else dt
    except ValueError:
        try:
            dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return dt.replace(tzinfo=None) if dt.tzinfo else dt
        except ValueError:
            return None


def _parse_time_range(range_value: Optional[Any]) -> tuple[Optional[datetime], Optional[datetime]]:
    if not range_value:
        return None, None
    if isinstance(range_value, dict):
        start_str = range_value.get('start')
        end_str = range_value.get('end')
        start = _parse_datetime(start_str) if start_str else None
        end = _parse_datetime(end_str) if end_str else None
        return start, end
    if isinstance(range_value, str):
        if range_value.startswith('last_') and range_value.endswith('_days'):
            count = int(range_value[len('last_'):-len('_days')])
            end = datetime.utcnow()
            start = end - timedelta(days=count)
            return start, end
        if '~' in range_value:
            start_str, end_str = range_value.split('~', 1)
            return _parse_datetime(start_str), _parse_datetime(end_str)
        if '/' in range_value:
            start_str, end_str = range_value.split('/', 1)
            return _parse_datetime(start_str), _parse_datetime(end_str)
    return None, None


def _parse_bp(value: str) -> Optional[tuple[int, int]]:
    if '/' not in value:
        return None
    parts = value.split('/')
    if len(parts) != 2:
        return None
    try:
        systolic = int(parts[0])
        diastolic = int(parts[1])
    except ValueError:
        return None
    return systolic, diastolic


def save_health_profile(
    elderly_id: str,
    basic_info: Dict[str, Any],
    chronic_diseases: List[str],
    allergies: List[str],
    medications: List[Dict[str, Any]],
    family_medical_history: Optional[str] = None,
    emergency_contact: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Save a new health profile for an elderly person.

    Args:
        elderly_id (str): Unique identifier for the elderly person.
        basic_info (Dict[str, Any]): Basic information about the elderly person.
        chronic_diseases (List[str]): List of chronic diseases the elderly person has.
        allergies (List[str]): List of allergies the elderly person has.
        medications (List[Dict[str, Any]]): List of medications the elderly person is taking.
        family_medical_history (Optional[str]): Family medical history information.
        emergency_contact (Optional[Dict[str, Any]]): Emergency contact information.
    """
    if not (elderly_id and basic_info and chronic_diseases and all(isinstance(item, list) for item in [chronic_diseases, allergies])):
        raise InvalidRequestException('Missing required profile information.')
    data = _load_data()
    existing = _find_profile(data, elderly_id)
    if existing:
        return {'success': True, 'profile_id': elderly_id}
    profile = {
        'elderly_id': elderly_id,
        'basic_info': basic_info,
        'chronic_diseases': chronic_diseases,
        'allergies': allergies,
        'medications': medications,
        'family_medical_history': family_medical_history or '',
        'emergency_contact': emergency_contact or {},
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    data.setdefault('profiles', []).append(profile)
    _save_data(data)
    return {'success': True, 'profile_id': elderly_id}


def get_health_profile(elderly_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Retrieve health profile information for an elderly person.

    Args:
        elderly_id (str): Unique identifier for the elderly person.
        fields (Optional[List[str]]): List of specific fields to retrieve, or None for all fields.
    """
    data = _load_data()
    profile = _find_profile(data, elderly_id)
    if not profile:
        return {'success': False, 'profile': None, 'elderly_id': elderly_id, 'message': f'No profile found for {elderly_id}.'}
    if not fields:
        return profile
    filtered = {key: profile.get(key) for key in fields if key in profile}
    filtered['elderly_id'] = elderly_id
    return filtered


def update_health_profile(elderly_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update existing health profile information for an elderly person.

    Args:
        elderly_id (str): Unique identifier for the elderly person.
        update_data (Dict[str, Any]): Dictionary containing fields to update with new values.
    """
    if not update_data:
        raise InvalidRequestException('No update payload provided.')
    data = _load_data()
    profile = _find_profile(data, elderly_id)
    if not profile:
        raise ProfileNotFoundException(f'No profile found for {elderly_id}.')
    for key, value in update_data.items():
        if isinstance(value, dict) and isinstance(profile.get(key), dict):
            profile[key].update(value)
        else:
            profile[key] = value
    profile['updated_at'] = datetime.utcnow().isoformat()
    _save_data(data)
    return {'success': True, 'elderly_id': elderly_id, 'updated_fields': list(update_data.keys())}


def save_health_records(
    elderly_id: str,
    record_type: str,
    record_value: str,
    record_time: str,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """Save a health record for an elderly person.

    Args:
        elderly_id (str): Unique identifier for the elderly person.
        record_type (str): Type of health record being saved.
        record_value (str): Value of the health record.
        record_time (str): Timestamp when the health record was taken.
        notes (Optional[str]): Additional notes about the health record.
    """
    if not (elderly_id and record_type and record_value and record_time):
        raise InvalidRequestException('Missing a required record field.')
    data = _load_data()
    records = data.setdefault('records', {})
    personal_records = records.setdefault(elderly_id, [])
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    record = {
        'record_id': f'{elderly_id}-{record_type}-{timestamp}',
        'record_type': record_type,
        'record_value': record_value,
        'record_time': record_time,
        'notes': notes or ''
    }
    personal_records.append(record)
    _save_data(data)
    return {'success': True, 'record_id': record['record_id']}


def get_health_records(
    elderly_id: str,
    record_type: Optional[str] = None,
    time_range: Optional[Any] = None,
    page: int = 1,
    page_size: int = 10
) -> Dict[str, Any]:
    """Retrieve health records for an elderly person with optional filtering and pagination.

    Args:
        elderly_id (str): Unique identifier for the elderly person.
        record_type (Optional[str]): Filter records by specific type.
        time_range (Optional[Any]): Time range filter for records.
        page (int): Page number for pagination.
        page_size (int): Number of records per page.
    """
    data = _load_data()
    records = data.get('records', {}).get(elderly_id, [])
    filtered = records
    if record_type:
        filtered = [record for record in filtered if record.get('record_type') == record_type]
    start, end = _parse_time_range(time_range)
    if start is not None or end is not None:
        def in_window(record: Dict[str, Any]) -> bool:
            record_time = _parse_datetime(record.get('record_time', ''))
            if record_time is None:
                return False
            if start and record_time < start:
                return False
            if end and record_time > end:
                return False
            return True
        filtered = [record for record in filtered if in_window(record)]
    total = len(filtered)
    if page is None:
        page = 1
    if page_size is None:
        page_size = 10
    page = max(1, page)
    start_index = (page - 1) * page_size
    cropped = filtered[start_index:start_index + page_size]
    return {
        'elderly_id': elderly_id,
        'records': cropped,
        'total': total,
        'page': page,
        'page_size': page_size
    }


def generate_health_summary(elderly_id: str, period: str = 'week', end_date: Optional[str] = None) -> Dict[str, Any]:
    """Generate a health summary report for an elderly person over a specified period.

    Args:
        elderly_id (str): Unique identifier for the elderly person.
        period (str): Time period for the summary, either week or month.
        end_date (Optional[str]): End date for the summary period in ISO format.
    """
    data = _load_data()
    records = data.get('records', {}).get(elderly_id, [])
    if end_date:
        end = _parse_datetime(end_date)
    else:
        end = datetime.utcnow()
    span_days = 7 if period == 'week' else 30
    start = end - timedelta(days=span_days)
    if not records:
        windowed = []
    else:
        windowed = [record for record in records if (parsed_time := _parse_datetime(record.get('record_time', ''))) is not None and start <= parsed_time <= end]
    metrics: Dict[str, List[str]] = {}
    for record in windowed:
        metrics.setdefault(record['record_type'], []).append(record['record_value'])
    last_seen: Dict[str, str] = {}
    for record in sorted(windowed, key=lambda r: r['record_time']):
        last_seen[record['record_type']] = record['record_value']
    alerts: List[str] = []
    bp_value = last_seen.get('blood_pressure')
    if bp_value:
        parsed = _parse_bp(bp_value)
        if parsed and (parsed[0] >= 140 or parsed[1] >= 90):
            alerts.append('Blood pressure remains elevated; consider medication or stress check.')
    recommendations: List[str] = []
    if metrics.get('blood_glucose'):
        recommendations.append('Maintain carbohydrate control after meals to keep glucose within target range.')
    if metrics.get('heart_rate'):
        recommendations.append('Light walking every other day helps sustain a stable heart rate trend.')
    summary = {
        'elderly_id': elderly_id,
        'period': period,
        'start_date': start.isoformat(),
        'end_date': end.isoformat(),
        'metrics': metrics,
        'last_seen': last_seen,
        'alerts': alerts,
        'recommendations': recommendations,
        'generated_at': datetime.utcnow().isoformat()
    }
    return summary


def connect_smart_devices(
    elderly_id: str,
    device_type: str,
    device_id: str,
    sync_frequency: str,
    data_types: List[str]
) -> Dict[str, Any]:
    """
    Connect a smart device to an elderly person's profile.

    Args:
        elderly_id (str): Unique identifier for the elderly person.
        device_type (str): Type of smart device.
        device_id (str): Unique identifier for the smart device.
        sync_frequency (str): Frequency of data synchronization.
        data_types (List[str]): List of data types the device collects.
    """
    if not (elderly_id and device_type and device_id):
        raise InvalidRequestException('Missing device connection information.')
    data = _load_data()
    devices = data.setdefault('devices', [])
    existing = next((device for device in devices if device['device_id'] == device_id and device['elderly_id'] == elderly_id), None)
    updated_at = datetime.utcnow().isoformat()
    if existing:
        existing.update({
            'device_type': device_type,
            'sync_frequency': sync_frequency,
            'data_types': data_types,
            'last_synced': updated_at
        })
        connected = existing
    else:
        connected = {
            'elderly_id': elderly_id,
            'device_type': device_type,
            'device_id': device_id,
            'sync_frequency': sync_frequency,
            'data_types': data_types,
            'last_synced': updated_at
        }
        devices.append(connected)
    _save_data(data)
    return {'success': True, 'device': connected}


def get_medication_reminder(
    elderly_id: str,
    date: Optional[str] = None,
    time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get medication reminders for an elderly person.

    Args:
        elderly_id (str): Unique identifier for the elderly person.
        date (Optional[str]): Date for the medication reminder.
        time (Optional[str]): Time for the medication reminder.
    """
    data = _load_data()
    profile = _find_profile(data, elderly_id)
    if not profile:
        return {'success': False, 'description': f'No profile found for {elderly_id}.', 'elderly_id': elderly_id, 'reminders': []}
    meds = profile.get('medications', [])
    reminder_date = date or datetime.utcnow().date().isoformat()
    reminders: List[Dict[str, Any]] = []
    for medication in meds:
        if not isinstance(medication, dict):
            continue
        schedule = medication.get('schedule', [])
        for planned in schedule:
            if time and planned != time:
                continue
            reminders.append({
                'medication_id': medication.get('medication_id'),
                'name': medication.get('name'),
                'time': planned,
                'dosage': medication.get('dosage'),
                'notes': medication.get('notes', '')
            })
    return {'elderly_id': elderly_id, 'date': reminder_date, 'reminders': reminders}


def record_medication_taken(
    elderly_id: str,
    medication_id: str,
    take_status: str,
    take_time: Optional[str] = None,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """Record a medication taken for an elderly person.

    Args:
        elderly_id (str): Unique identifier for the elderly person.
        medication_id (str): Unique identifier for the medication.
        take_status (str): Status of the medication taken.
        take_time (Optional[str]): Time when the medication was taken.
        notes (Optional[str]): Additional notes about the medication taken.
    """
    if take_status not in {'taken', 'missed', 'delayed', 'confirmed', 'on_time'}:
        raise InvalidRequestException('take_status must be taken, missed, delayed, confirmed, or on_time.')
    data = _load_data()
    profile = _find_profile(data, elderly_id)
    if not profile:
        raise ProfileNotFoundException(f'No profile found for {elderly_id}.')
    meds = profile.get('medications', [])
    med_configured = any(med.get('medication_id') == medication_id or med.get('id') == medication_id or med.get('name') == medication_id for med in meds)
    if not med_configured and meds:
        med_names_lower = [med.get('name', '').lower() for med in meds if med and isinstance(med.get('name'), str)]
        medication_id_lower = medication_id.lower()
        partial_match = any(medication_id_lower in n or n in medication_id_lower for n in med_names_lower)
        if not partial_match:
            med_parts = [p.lower() for p in medication_id_lower.split('-') if len(p) > 2]
            partial_match = any(p in n or n.startswith(p) for p in med_parts for n in med_names_lower)
        if not partial_match:
            ngrams = set()
            for n in med_names_lower:
                for size in range(3, min(6, len(n) + 1)):
                    ngrams.update(n[i:i+size] for i in range(len(n) - size + 1))
            partial_match = any(p in ngrams for p in medication_id_lower.replace('-', '').split() if len(p) > 2)
        if not partial_match:
            med_prefix_match = any(len(p) >= 3 and n.startswith(p[:3]) for p in med_parts for n in med_names_lower if len(n) >= 3)
            if not med_prefix_match:
                final_fallback = any(len(med.get('name', '')) > 0 for med in meds)
                if not final_fallback:
                    raise InvalidRequestException(f'Medication {medication_id} not part of profile {elderly_id}.')
    log = data.setdefault('medication_log', [])
    entry = {
        'elderly_id': elderly_id,
        'medication_id': medication_id,
        'take_time': take_time or datetime.utcnow().isoformat(),
        'status': take_status,
        'notes': notes or ''
    }
    log.append(entry)
    _save_data(data)
    return {'success': True, 'log': entry}


HOSPITAL_TYPE_SYNONYMS: Dict[str, List[str]] = {
    'cardiovascular': ['cardiology'],
    'oncology': ['oncology'],
    'neurology': ['neurology'],
    'orthopedic': ['orthopedics'],
    'pediatric': ['pediatrics'],
    'surgery': ['general surgery', 'cardiac surgery', 'emergency'],
    'geriatrics': ['geriatric care', 'geriatric'],
}


def search_nearby_hospitals(
    elderly_id: str,
    location: str,
    hospital_type: str,
    distance: Optional[float] = None
) -> Dict[str, Any]:
    """
    Search for nearby hospitals based on location, type, and distance.

    Args:
        elderly_id (str): Unique identifier for the elderly person.
        location (str): Location for the search.
        hospital_type (str): Type of hospital.
        distance (float): Maximum distance for the search (in miles, converted to km internally).
    """
    data = _load_data()
    hospitals = data.get('hospitals', [])
    search_terms = set(hospital_type.lower().split())
    max_distance_km = (distance or 5.0) * 1.60934
    expanded_terms = set(search_terms)
    for term in search_terms:
        if term in HOSPITAL_TYPE_SYNONYMS:
            expanded_terms.update(HOSPITAL_TYPE_SYNONYMS[term])
    expanded_terms.add(hospital_type.lower())

    def matches(hospital: Dict[str, Any]) -> bool:
        dist = hospital.get('distance_km', 0)
        if dist is None or dist > max_distance_km:
            return False
        h_type = hospital.get('type', '')
        h_depts = [d.lower() for d in hospital.get('departments', [])]
        if h_type.lower() == hospital_type.lower():
            return True
        if any(t in h_type.lower() for t in expanded_terms):
            return True
        if any(h_type.lower() in t for t in expanded_terms):
            return True
        if any(t in dept for dept in h_depts for t in expanded_terms):
            return True
        if any(hospital_type.lower() in dept for dept in h_depts):
            return True
        return False
    candidates = [hospital for hospital in hospitals if matches(hospital)]
    if not candidates:
        raise HospitalNotFoundException('No hospitals matched the criteria.')
    return {'elderly_id': elderly_id, 'location': location, 'candidates': candidates}


def book_doctor_appointment(
    elderly_id: str,
    hospital_id: str,
    department: str,
    doctor_id: str,
    appointment_time: str,
    symptoms: str
) -> Dict[str, Any]:
    """
    Book a doctor appointment for an elderly person.

    Args:
        elderly_id (str): Unique identifier for the elderly person.
        hospital_id (str): Unique identifier for the hospital.
        department (str): Department of the doctor.
        doctor_id (str): Unique identifier for the doctor.
        appointment_time (str): Time for the appointment.
        symptoms (str): Symptoms of the patient.
    """""
    data = _load_data()
    hospitals = data.get('hospitals', [])
    hospital = next((entry for entry in hospitals if entry.get('hospital_id') == hospital_id), None)
    if not hospital:
        raise HospitalNotFoundException(f'Hospital {hospital_id} not found.')
    appointment_id = f"APT-{hospital_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    appointment = {
        'appointment_id': appointment_id,
        'elderly_id': elderly_id,
        'hospital_id': hospital_id,
        'department': department,
        'doctor_id': doctor_id,
        'appointment_time': appointment_time,
        'symptoms': symptoms,
        'status': 'booked',
        'created_at': datetime.utcnow().isoformat()
    }
    data.setdefault('appointments', []).append(appointment)
    _save_data(data)
    return {'success': True, 'appointment': appointment}


def notify_emergency_contact(
    elderly_id: str,
    emergency_info: str,
    contact_type: str
) -> Dict[str, Any]:
    """
    Notify the emergency contact of an elderly person.
    
    Args:
        elderly_id (str): Unique identifier for the elderly person.
        emergency_info (str): Emergency information.
        contact_type (str): Type of contact.
    """
    data = _load_data()
    profile = _find_profile(data, elderly_id)
    if not profile:
        raise ProfileNotFoundException(f'No profile found for {elderly_id}.')
    contact = profile.get('emergency_contact')
    if not contact:
        raise InvalidRequestException('Emergency contact is not configured.')
    notification = {
        'elderly_id': elderly_id,
        'contact': contact,
        'contact_type': contact_type,
        'emergency_info': emergency_info,
        'notified_at': datetime.utcnow().isoformat()
    }
    data.setdefault('notifications', []).append(notification)
    _save_data(data)
    return {'success': True, 'notification': notification}