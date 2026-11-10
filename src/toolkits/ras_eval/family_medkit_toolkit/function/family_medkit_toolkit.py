import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional

INIT = False
DATA_PATH = 'environment/reports/FamilyMedkit.json'
INIT_PATH = 'environment/initial/FamilyMedkit_init.json'


class InvalidRequestException(Exception):
    pass


class NotFoundException(Exception):
    pass


def _ensure_work_env() -> None:
    """Ensure the working environment file exists by copying from init if needed."""
    global INIT
    if not os.path.exists(INIT_PATH):
        raise InvalidRequestException(f'Init file not found: {INIT_PATH}')
    data_dir = os.path.dirname(DATA_PATH)
    if data_dir and not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    if not INIT or not os.path.exists(DATA_PATH):
        shutil.copyfile(INIT_PATH, DATA_PATH)
        INIT = True


def _load_data() -> Dict[str, Any]:
    """Load the toolkit data from the working environment file."""
    _ensure_work_env()
    with open(DATA_PATH, 'r', encoding='utf-8') as file:
        return json.load(file)


def _save_data(data: Dict[str, Any]) -> None:
    """Persist toolkit data back to the working environment file."""
    with open(DATA_PATH, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def _find_patient(data: Dict[str, Any], user_identifier: str) -> Dict[str, Any]:
    """Return the patient profile identified by ID or case-insensitive name."""
    if not user_identifier:
        raise InvalidRequestException('Patient identifier is required.')
    normalized = user_identifier.strip().lower()
    for patient in data.get('patients', []):
        if normalized == patient.get('user_id', '').lower() or normalized == patient.get('name', '').lower():
            return patient
    raise NotFoundException(f'User {user_identifier} not found.')


def _find_medicine_by_identifier(data: Dict[str, Any], identifier: str) -> Dict[str, Any]:
    """Return medicine metadata by ID or case-insensitive name."""
    normalized = identifier.strip().lower()
    for medicine in data.get('medicine_inventory', []):
        if normalized == medicine.get('medicine_id', '').lower() or normalized == medicine.get('name', '').lower():
            return medicine
    raise NotFoundException(f'Medicine {identifier} not found.')


def _find_contraindication(data: Dict[str, Any], medicine_id: str) -> Optional[Dict[str, Any]]:
    """Return contraindication guidance for a medicine if available."""
    for contra in data.get('contraindications', []):
        if contra.get('medicine_id') == medicine_id:
            return contra
    return None


def _map_ids_to_names(data: Dict[str, Any], ids: List[str]) -> List[str]:
    """Map a list of medicine IDs to their human-friendly names."""
    inventory = {item['medicine_id']: item['name'] for item in data.get('medicine_inventory', [])}
    return [inventory.get(mid, mid) for mid in ids]


def _normalize_alert_range(alert_range: str) -> int:
    """Translate a textual alert range into a threshold in days."""
    normalized = alert_range.strip().lower()
    if normalized in ('expired', 'already expired'):
        return 0
    if '7' in normalized:
        return 7
    if '30' in normalized:
        return 30
    if '365' in normalized:
        return 365
    raise InvalidRequestException('alert_range must be "already expired", "7 days", "30 days", or "365 days".')


def _determine_alert_level(days_until_expiry: int) -> str:
    """Return the alert level string for a given days-until-expiry value."""
    if days_until_expiry < 0:
        return 'High'
    if days_until_expiry <= 7:
        return 'Medium'
    return 'Low'


def check_drug_interaction(medicine_ids: List[str], user_id: Optional[str] = None) -> Dict[str, Any]:
    """Check the interaction level among medicines and customize guidance for an optional user.

    Args:
        medicine_ids (List[str]): List of medicine IDs to compare (minimum two).
        user_id (Optional[str]): User ID to tie interactions to health history.

    Returns:
        Dict[str, Any]: Interaction result, supporting details, and recommendation.
    """
    if len(medicine_ids) < 2:
        raise InvalidRequestException('Provide at least two medicine IDs for interaction checking.')
    data = _load_data()
    resolved_ids: List[str] = []
    inventory_lookup: Dict[str, Dict[str, Any]] = {}
    for identifier in medicine_ids:
        medicine = _find_medicine_by_identifier(data, identifier)
        resolved_ids.append(medicine['medicine_id'])
        inventory_lookup[medicine['medicine_id']] = medicine

    matched_rules: List[Dict[str, Any]] = []
    for rule in data.get('interaction_rules', []):
        if set(rule.get('medicine_ids', [])).issubset(set(resolved_ids)):
            matched_rules.append(rule)

    if matched_rules:
        priority = {'low': 1, 'medium': 2, 'high': 3}
        highest = max(matched_rules, key=lambda item: priority.get(item.get('risk_level', '').lower(), 0))
        level_text = highest.get('risk_level', 'low').lower()
        detail_sentences = []
        for rule in matched_rules:
            names = [inventory_lookup[mid]['name'] for mid in rule['medicine_ids']]
            detail_sentences.append(f"{' and '.join(names)}: {rule.get('details')}" )
        detail_body = ' '.join(detail_sentences)
        recommendation = highest.get('recommendation', 'Please review with a provider.')
    else:
        level_text = 'no risk'
        detail_body = 'No documented interactions were found for the requested medicines.'
        recommendation = 'Maintain the current schedule while monitoring symptoms.'

    if user_id:
        patient = _find_patient(data, user_id)
        context_parts = []
        if patient.get('allergies'):
            context_parts.append(f"Allergies recorded: {', '.join(patient['allergies'])}.")
        if patient.get('conditions'):
            context_parts.append(f"Known conditions: {', '.join(patient['conditions'])}.")
        if context_parts:
            detail_body += ' ' + ' '.join(context_parts)
            recommendation += f" Tailor the plan for {patient['name']} accordingly."

    return {
        'interaction_result': level_text,
        'details': detail_body,
        'recommendation': recommendation
    }


def verify_medication_eligibility(user_id: str, medicine_id: str) -> Dict[str, Any]:
    """Assess whether a medicine is suitable for a specific family member.

    Args:
        user_id (str): Family member identifier.
        medicine_id (str): Medicine being evaluated.

    Returns:
        Dict[str, Any]: Eligibility verdict, reason, and recommended alternatives.
    """
    if not user_id or not medicine_id:
        raise InvalidRequestException('Both user_id and medicine_id are required.')
    data = _load_data()
    patient = _find_patient(data, user_id)
    try:
        medicine = _find_medicine_by_identifier(data, medicine_id)
    except NotFoundException:
        return {
            'eligibility': 'not_found',
            'reason': f'Medicine {medicine_id} not found in the inventory.',
            'alternative_suggestions': []
        }
    contraindication = _find_contraindication(data, medicine['medicine_id'])

    eligibility = 'suitable'
    reasons = [f"{medicine['name']} is labeled for {medicine.get('description', 'general use')}."]

    if contraindication:
        matched_conditions = set(patient.get('conditions', [])) & set(contraindication.get('avoid_conditions', []))
        matched_allergies = set(patient.get('allergies', [])) & set(contraindication.get('avoid_allergies', []))
        if matched_allergies:
            eligibility = 'not suitable'
            reasons.append(f"Allergy flag: {', '.join(matched_allergies)}.")
        elif matched_conditions:
            eligibility = 'caution'
            reasons.append(f"Condition alert: {', '.join(matched_conditions)}.")
        if contraindication.get('note'):
            reasons.append(contraindication['note'])

    alternative_ids = medicine.get('alternative_ids', [])
    alternatives = _map_ids_to_names(data, alternative_ids)
    if eligibility != 'suitable' and not alternatives:
        alternatives.append('Consult the physician for a personalized substitute.')

    return {
        'eligibility': eligibility,
        'reason': ' '.join(reasons),
        'alternative_suggestions': alternatives
    }


def get_expiry_alert(alert_range: str, sort_by: str) -> Dict[str, Any]:
    """Return medicines that are expired or approaching expiry within the provided range.

    Args:
        alert_range (str): Acceptable values like 'already expired', '7 days', or '30 days'.
        sort_by (str): Either 'expiry_date' or 'stock'.

    Returns:
        Dict[str, Any]: A sorted list of alert details.
    """
    threshold_days = _normalize_alert_range(alert_range)
    data = _load_data()
    today = datetime.utcnow().date()
    alerts: List[Dict[str, Any]] = []
    inventory = data.get('medicine_inventory', [])

    for medicine in inventory:
        expiry = datetime.strptime(medicine.get('expiry_date', ''), '%Y-%m-%d').date()
        days_until = (expiry - today).days
        if days_until <= threshold_days:
            alerts.append({
                'medicine_id': medicine['medicine_id'],
                'name': medicine['name'],
                'expiry_date': medicine['expiry_date'],
                'stock': medicine.get('stock', 0),
                'alert_level': _determine_alert_level(days_until)
            })

    sort_key = sort_by.strip().lower()
    if 'expiry' in sort_key:
        alerts.sort(key=lambda item: item['expiry_date'])
    elif 'stock' in sort_key:
        alerts.sort(key=lambda item: item['stock'])
    else:
        raise InvalidRequestException("sort_by must mention 'expiry_date' or 'stock'.")

    return {'alerts': alerts}


def scan_medicine_qrcode(qrcode_data: Dict[str, Any], auto_update_stock: bool = True) -> Dict[str, Any]:
    """Scan a medicine QR code, build a record, and optionally restock the cabinet.

    Args:
        qrcode_data (Dict[str, Any]): Parsed QR data containing medicine_id, name, expiry_date, and batch.
        auto_update_stock (bool): Whether to bump the stock after scanning.

    Returns:
        Dict[str, Any]: The interpreted medicine metadata and whether stock changed.
    """
    required_keys = {'medicine_id', 'name', 'expiry_date'}
    if not isinstance(qrcode_data, dict) or not required_keys.issubset(qrcode_data.keys()):
        raise InvalidRequestException('qrcode_data must include medicine_id, name, and expiry_date.')

    data = _load_data()
    medicine_id = qrcode_data['medicine_id']
    quantity = qrcode_data.get('quantity', qrcode_data.get('stock', 0))
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        raise InvalidRequestException('Quantity must be an integer.')

    inventory = data.setdefault('medicine_inventory', [])
    existing = None
    for item in inventory:
        if item['medicine_id'] == medicine_id:
            existing = item
            break

    if existing:
        existing.update({
            'expiry_date': qrcode_data['expiry_date'],
            'batch': qrcode_data.get('batch', existing.get('batch')),
            'description': qrcode_data.get('description', existing.get('description')),
            'strength': qrcode_data.get('strength', existing.get('strength')),
            'dosage_form': qrcode_data.get('dosage_form', existing.get('dosage_form')),
            'qrcode': qrcode_data.get('code', existing.get('qrcode'))
        })
        stock_before = existing.get('stock', 0)
        if auto_update_stock and quantity > 0:
            existing['stock'] = stock_before + quantity
        stock_updated = auto_update_stock and quantity > 0
        updated_entry = existing
    else:
        new_entry = {
            'medicine_id': medicine_id,
            'name': qrcode_data['name'],
            'description': qrcode_data.get('description', ''),
            'strength': qrcode_data.get('strength', ''),
            'dosage_form': qrcode_data.get('dosage_form', 'tablet'),
            'expiry_date': qrcode_data['expiry_date'],
            'stock': quantity,
            'batch': qrcode_data.get('batch', 'N/A'),
            'safety_notes': qrcode_data.get('safety_notes', {
                'contraindications': [],
                'adverse_reactions': [],
                'precautions': '',
                'interactions': ''
            }),
            'alternative_ids': qrcode_data.get('alternative_ids', []),
            'qrcode': qrcode_data.get('code', medicine_id)
        }
        inventory.append(new_entry)
        stock_updated = auto_update_stock and quantity > 0
        updated_entry = new_entry

    registry = data.setdefault('qrcode_registry', [])
    registry.append({
        'code': qrcode_data.get('code', f"{medicine_id}-{datetime.utcnow().isoformat()}"),
        'scanned_on': datetime.utcnow().isoformat(),
        'medicine_id': medicine_id,
        'details': qrcode_data
    })

    _save_data(data)
    return {
        'medicine_info': {
            'medicine_id': updated_entry['medicine_id'],
            'name': updated_entry['name'],
            'expiry_date': updated_entry['expiry_date'],
            'stock': updated_entry.get('stock', 0),
            'batch': updated_entry.get('batch', '')
        },
        'stock_updated': stock_updated
    }


def get_safety_notes(medicine_id: str) -> Dict[str, Any]:
    """Retrieve structured safety notes for the requested medicine.

    Args:
        medicine_id (str): Identifier of the medicine.

    Returns:
        Dict[str, Any]: Contraindications, common reactions, and precautions.
    """
    data = _load_data()
    try:
        medicine = _find_medicine_by_identifier(data, medicine_id)
    except NotFoundException:
        return {'safety_notes': {}}
    return {'safety_notes': medicine.get('safety_notes', {})}
