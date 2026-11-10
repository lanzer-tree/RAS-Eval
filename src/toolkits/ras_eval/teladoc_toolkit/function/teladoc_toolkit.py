import os
import json
import shutil
import secrets
from typing import Any, Dict, List

DATA_PATH = 'environment/reports/teladoc.json'
INIT_PATH = 'environment/initial/teladoc_init.json'

INIT = False


class InvalidRequestException(Exception):
    pass


class NotFoundException(Exception):
    pass


def _ensure_work_env():
    # Ensure working environment file exists by copying from init if necessary.
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
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_data(data: Dict[str, Any]):
    if not os.path.exists(os.path.dirname(DATA_PATH)):
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(4)}"


def _find_doctor(doctors: List[Dict[str, Any]], doctor_name: str):
    search_lower = doctor_name.lower().strip()
    search_no_prefix = search_lower.replace('dr.', '').replace('dr ', '').strip()
    search_words = search_no_prefix.split()

    best = None
    best_score = 0

    for d in doctors:
        name_lower = d.get('name', '').lower().strip()
        if name_lower == search_lower:
            return d

        name_no_prefix = name_lower.replace('dr.', '').replace('dr ', '').strip()
        name_words = name_no_prefix.split()

        if search_no_prefix == name_no_prefix:
            return d

        if search_no_prefix in name_no_prefix or name_no_prefix in search_no_prefix:
            score = 2
            if score > best_score:
                best_score = score
                best = d

        match_count = 0
        for sw in search_words:
            if any(sw in nw or nw in sw for nw in name_words):
                match_count += 1
        if match_count > 0 and match_count >= len(search_words) * 0.5:
            score = match_count
            if score > best_score:
                best_score = score
                best = d

    return best


_MONTH_MAP = {
    'january': '01', 'february': '02', 'march': '03', 'april': '04',
    'may': '05', 'june': '06', 'july': '07', 'august': '08',
    'september': '09', 'october': '10', 'november': '11', 'december': '12',
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
    'jun': '06', 'jul': '07', 'aug': '08',
    'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
}


def _normalize_date(date_str: str, default_year: str = '2026') -> str:
    if not date_str:
        return ''
    date_str = date_str.strip()
    if not date_str:
        return ''
    import re
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', date_str)
    if m:
        return date_str
    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2,4})$', date_str)
    if m:
        month, day, year = m.group(1), m.group(2), m.group(3)
        if len(year) == 2:
            year = '20' + year
        return f'{year}-{month.zfill(2)}-{day.zfill(2)}'
    date_lower = date_str.lower().replace(',', '').replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
    for month_name, month_num in _MONTH_MAP.items():
        if month_name in date_lower:
            day_match = re.search(r'(\d{1,2})', date_lower)
            if day_match:
                day = day_match.group(1).zfill(2)
                year_match = re.search(r'(\d{4})', date_lower)
                year = year_match.group(1) if year_match else default_year
                return f'{year}-{month_num}-{day}'
    return date_str


def SearchDoctors(keywords: str = '', location: str = '', date: str = '') -> Dict[str, Any]:
    """Search for doctors based on keywords, location, and availability date.
    
    Args:
        keywords (str): Search keywords for doctor name or specialty.
        location (str): Location filter for doctor search.
        date (str): Date to check for available appointment slots.
    """
    data = _load_data()
    doctors = []
    for d in data.get('doctors', []):
        if keywords:
            kw_lower = keywords.lower()
            kw_words = kw_lower.split()
            name_lower = d.get('name', '').lower()
            specialty_lower = d.get('specialty', '').lower()
            name_words = name_lower.split()
            specialty_words = specialty_lower.split()
            all_target_words = name_words + specialty_words
            all_target_full = [name_lower, specialty_lower]
            matched = False
            for kw in kw_words:
                for tw in all_target_words:
                    if kw in tw or tw in kw:
                        matched = True
                        break
                    if len(kw) >= 3 and len(tw) >= 3:
                        common_prefix_len = 0
                        for a, b in zip(kw, tw):
                            if a == b:
                                common_prefix_len += 1
                            else:
                                break
                        if common_prefix_len >= min(len(kw), len(tw)) - 2:
                            matched = True
                            break
                if not matched:
                    for tf in all_target_full:
                        if kw in tf:
                            matched = True
                            break
                if matched:
                    break
            if not matched:
                continue
        if location and location.lower() not in d.get('location', '').lower():
            continue
        if date:
            normalized_date = _normalize_date(date)
            slots = d.get('available_slots', [])
            if not any(normalized_date and slot.startswith(normalized_date) for slot in slots):
                continue
        doctors.append(d)
    return {'doctors': doctors}


def ConsultDoctor(doctor_name: str, reason: str) -> Dict[str, Any]:
    """Create a new consultation with a doctor.
    
    Args:
        doctor_name (str): Name of the doctor to consult.
        reason (str): Reason for the consultation.
    """
    if not doctor_name or not reason:
        raise InvalidRequestException("The 'doctor_name' or 'reason' parameter is not valid.")
    data = _load_data()
    doctor = _find_doctor(data.get('doctors', []), doctor_name)
    if not doctor:
        raise NotFoundException(f"Doctor {doctor_name} not found.")
    doctor_id = doctor['doctor_id']
    consultation_id = _new_id('consult')
    data.setdefault('consultations', []).append({
        'consultation_id': consultation_id,
        'doctor_id': doctor_id,
        'reason': reason,
        'status': 'open'
    })
    _save_data(data)
    return {'consultation_id': consultation_id}


def ScheduleAppointment(doctor_name: str, date: str, time: str, reason: str) -> Dict[str, Any]:
    """Schedule an appointment with a doctor.
    
    Args:
        doctor_name (str): Name of the doctor to schedule with.
        date (str): Date of the appointment.
        time (str): Time of the appointment.
        reason (str): Reason for the appointment.
    """
    if not doctor_name or not date or not time or not reason:
        raise InvalidRequestException("Required parameters are missing or invalid.")
    data = _load_data()
    doctor = _find_doctor(data.get('doctors', []), doctor_name)
    if not doctor:
        raise NotFoundException(f"Doctor {doctor_name} not found.")
    doctor_id = doctor['doctor_id']
    appointment_id = _new_id('appt')
    appointment = {
        'appointment_id': appointment_id,
        'doctor_id': doctor_id,
        'date': date,
        'time': time,
        'reason': reason,
        'status': 'scheduled'
    }
    data.setdefault('appointments', []).append(appointment)
    _save_data(data)
    return {'appointment_id': appointment_id, 'success': True}


def ManageAppointments(appointment_id: str, action: str, date: str = '', time: str = '') -> Dict[str, Any]:
    """Manage existing appointments by viewing, updating, or cancelling.
    
    Args:
        appointment_id (str): ID of the appointment to manage.
        action (str): Action to perform (view, update, or cancel).
        date (str): New date for the appointment (only for update action).
        time (str): New time for the appointment (only for update action).
    """
    if not appointment_id or not action:
        raise InvalidRequestException("The 'appointment_id' or 'action' parameter is not valid.")
    data = _load_data()
    appt = next((a for a in data.get('appointments', []) if a.get('appointment_id') == appointment_id), None)
    if not appt:
        if action == 'view':
            return {'appointments': data.get('appointments', [])}
        raise NotFoundException("The 'appointment_id' parameter does not exist.")
    if action == 'view':
        return {'appointment_details': appt}
    if action == 'update':
        if date:
            appt['date'] = date
        if time:
            appt['time'] = time
        appt['status'] = 'scheduled'
    elif action == 'cancel':
        appt['status'] = 'cancelled'
    else:
        raise InvalidRequestException("The 'action' parameter is not valid.")
    _save_data(data)
    return {'appointment_details': appt}


def AccessUserInfo() -> Dict[str, Any]:
    """Access the user's personal information."""
    data = _load_data()
    return {'user_info': data.get('user_info', {})}


def AccessMedicalHistory() -> Dict[str, Any]:
    """Access the user's medical health records."""
    data = _load_data()
    return {'health_records': data.get('health_records', [])}


def RequestPrescription(medication_name: str, dosage: str, doctor_name: str) -> Dict[str, Any]:
    """Request a prescription from a doctor.
    
    Args:
        medication_name (str): Name of the medication being requested.
        dosage (str): Dosage information for the medication.
        doctor_name (str): Name of the doctor to request prescription from.
    """
    if not medication_name or not dosage or not doctor_name:
        raise InvalidRequestException("The 'medication_name', 'dosage', or 'doctor_name' parameter is not valid.")
    data = _load_data()
    doctor = _find_doctor(data.get('doctors', []), doctor_name)
    if not doctor:
        raise NotFoundException(f"Doctor {doctor_name} not found.")
    doctor_id = doctor['doctor_id']
    req_id = _new_id('rx')
    entry = {
        'prescription_request_id': req_id,
        'medication_name': medication_name,
        'dosage': dosage,
        'doctor_id': doctor_id,
        'status': 'pending'
    }
    data.setdefault('prescriptions', []).append(entry)
    _save_data(data)
    return {'prescription_request_id': req_id, 'success': True}


def ViewPrescriptions() -> Dict[str, Any]:
    """View all prescription requests."""
    data = _load_data()
    return {'prescriptions': data.get('prescriptions', [])}


def SendMessage(consultation_id: str, message_content: str) -> Dict[str, Any]:
    """Send a message in a consultation and receive doctor's response.
    
    Args:
        consultation_id (str): ID of the consultation to send message to.
        message_content (str): Content of the message to send.
    """
    if not consultation_id or not message_content:
        raise InvalidRequestException("The 'consultation_id' or 'message_content' parameter is not valid.")
    data = _load_data()
    consult = next((c for c in data.get('consultations', []) if c.get('consultation_id') == consultation_id), None)
    if not consult:
        raise NotFoundException("The 'consultation_id' parameter does not exist.")
    data.setdefault('messages', []).append({
        'consultation_id': consultation_id,
        'from': 'patient',
        'content': message_content
    })
    doctor_response = f"Doctor response to: {message_content}"
    data['messages'].append({
        'consultation_id': consultation_id,
        'from': 'doctor',
        'content': doctor_response
    })
    _save_data(data)
    return {'doctor_response': doctor_response}


def LeaveReview(doctor_name: str, rating: int, review_content: str) -> Dict[str, Any]:
    """Leave a review for a doctor.
    
    Args:
        doctor_name (str): Name of the doctor being reviewed.
        rating (int): Rating score from 1 to 5.
        review_content (str): Content of the review.
    """
    if not doctor_name or not review_content or rating is None:
        raise InvalidRequestException("Required parameters are missing or invalid.")
    try:
        rating_val = int(rating)
    except Exception:
        raise InvalidRequestException("The 'rating' parameter is not valid.")
    if rating_val < 1 or rating_val > 5:
        raise InvalidRequestException("The 'rating' parameter is not valid.")
    data = _load_data()
    doctor = _find_doctor(data.get('doctors', []), doctor_name)
    if not doctor:
        raise NotFoundException(f"Doctor {doctor_name} not found.")
    doctor_id = doctor['doctor_id']
    review = {
        'doctor_id': doctor_id,
        'rating': rating_val,
        'review_content': review_content
    }
    data.setdefault('reviews', []).append(review)
    _save_data(data)
    return {'success': True}


def ViewReviews(doctor_name: str) -> Dict[str, Any]:
    """View all reviews for a specific doctor.
    
    Args:
        doctor_name (str): Name of the doctor to view reviews for.
    """
    if not doctor_name:
        raise InvalidRequestException("The 'doctor_name' parameter is not valid.")
    data = _load_data()
    doctor = _find_doctor(data.get('doctors', []), doctor_name)
    if not doctor:
        raise NotFoundException(f"Doctor {doctor_name} not found.")
    doctor_id = doctor['doctor_id']
    reviews = [r for r in data.get('reviews', []) if r.get('doctor_id') == doctor_id]
    return {'reviews': reviews}
