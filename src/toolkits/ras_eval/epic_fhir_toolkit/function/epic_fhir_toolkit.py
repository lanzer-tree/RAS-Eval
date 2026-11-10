import json
import os
import shutil
import uuid
from typing import Any, Dict, List

DATA_PATH = 'environment/reports/epicFHIR.json'
INIT_PATH = 'environment/initial/epicFHIR_init.json'
INIT = False


class InvalidRequestException(Exception):
    """Raised when the request syntax or parameters are invalid"""


class NotFoundException(Exception):
    """Raised when the referenced resource cannot be located"""


def _ensure_work_env() -> None:
    """Ensure the working environment file exists by copying the init snapshot if needed"""
    global INIT
    if not os.path.exists(INIT_PATH):
        raise InvalidRequestException(f'Init file not found: {INIT_PATH}')
    data_dir = os.path.dirname(DATA_PATH)
    if data_dir and not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    if not INIT:
        shutil.copyfile(INIT_PATH, DATA_PATH)
        INIT = True
    if not os.path.exists(DATA_PATH):
        shutil.copyfile(INIT_PATH, DATA_PATH)


def _load_data() -> Dict[str, Any]:
    """Load the current environment snapshot from disk."""
    _ensure_work_env()
    with open(DATA_PATH, 'r', encoding='utf-8') as file:
        return json.load(file)


def _save_data(data: Dict[str, Any]) -> None:
    """Persist the environment snapshot to disk."""
    data_dir = os.path.dirname(DATA_PATH)
    if data_dir and not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    with open(DATA_PATH, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2)


def _generate_unique_id(prefix: str) -> str:
    """Return a compact unique identifier for toolkit resources."""
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _get_patient(data: Dict[str, Any], patient_id: str) -> Dict[str, Any] | None:
    """Find a patient definition by identifier."""
    for patient in data.get('patients', []):
        if patient.get('patient_id') == patient_id:
            return patient
    return None


def _get_doctor(data: Dict[str, Any], doctor_id: str) -> Dict[str, Any] | None:
    """Find a doctor definition by identifier."""
    for doctor in data.get('doctors', []):
        if doctor.get('doctor_id') == doctor_id:
            return doctor
    return None


def _validate_max_results(max_results: int) -> None:
    """Ensure max_results is a positive integer."""
    if not isinstance(max_results, int) or max_results <= 0:
        raise InvalidRequestException("The 'max_results' parameter is not a valid integer.")


def _ensure_fields(data: Dict[str, Any], required: List[str], name: str) -> None:
    """Assert that the provided data dictionary contains the required fields."""
    if not isinstance(data, dict):
        raise InvalidRequestException(f"The '{name}' parameter is not valid.")
    missing = [field for field in required if field not in data]
    if missing:
        raise InvalidRequestException(
            f"The '{name}' parameter is missing fields: {', '.join(missing)}."
        )


def _serialize_document(document: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a clinical document for tool output."""
    return {
        'document_id': document.get('document_id'),
        'document_data': {
            'type': document.get('type'),
            'date': document.get('date'),
            'summary': document.get('summary'),
            'details': document.get('details')
        }
    }


def _serialize_appointment(appointment: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize an appointment for tool output."""
    return {
        'appointment_id': appointment.get('appointment_id'),
        'appointment_data': {
            'doctor_id': appointment.get('doctor_id'),
            'doctor_name': appointment.get('doctor_name'),
            'date': appointment.get('date'),
            'time': appointment.get('time'),
            'location': appointment.get('location'),
            'status': appointment.get('status')
        }
    }


def _serialize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a patient record for tool output."""
    return {
        'patient_id': record.get('patient_id'),
        'record_id': record.get('record_id'),
        'record_data': record.get('record_data')
    }


def _serialize_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a diagnostic report for tool output."""
    return {
        'report_id': report.get('report_id'),
        'report_data': {
            'type': report.get('type'),
            'date': report.get('date'),
            'results': report.get('results'),
            'interpretation': report.get('interpretation'),
            'doctor_id': report.get('doctor_id'),
            'doctor_name': report.get('doctor_name')
        }
    }


def SearchPatients(search_term: str, max_results: int = 10) -> Dict[str, Any]:
    """Search for patients by demographic or clinical keywords.

    Args:
        search_term (str): The keyword to search for in patient data.
        max_results (int): Maximum number of results to return
    """
    if not isinstance(search_term, str) or not search_term.strip():
        raise InvalidRequestException("The 'search_term' parameter is invalid.")
    _validate_max_results(max_results)
    term = search_term.strip().lower()
    data = _load_data()
    matches: List[Dict[str, Any]] = []
    for patient in data.get('patients', []):
        search_space = [
            patient.get('patient_id', ''),
            patient.get('name', ''),
            ' '.join(patient.get('conditions', [])),
            ' '.join(patient.get('allergies', []))
        ]
        search_space.extend(str(value) for value in patient.get('contact_info', {}).values())
        if any(term in str(value).lower() for value in search_space if value):
            matches.append({
                'patient_id': patient.get('patient_id'),
                'name': patient.get('name'),
                'age': patient.get('age'),
                'gender': patient.get('gender')
            })
        if len(matches) >= max_results:
            break
    return {'patients_info': matches}


def GetPatientDetails(patient_id: str) -> Dict[str, Any]:
    """Retrieve complete demographics and clinical data for a patient.

    Args:
        patient_id (str): The unique identifier of the patient
    """
    if not isinstance(patient_id, str) or not patient_id.strip():
        raise InvalidRequestException("The 'patient_id' parameter is invalid.")
    data = _load_data()
    patient = _get_patient(data, patient_id)
    if not patient:
        raise NotFoundException("The 'patient_id' does not exist.")
    return {'patient_data': patient}


def SearchFhirDoctors(search_term: str, max_results: int = 10) -> Dict[str, Any]:
    """Search for doctors by name, ID, or specialty.

    Args:
        search_term (str): The keyword to search for in doctor data.
        max_results (int): Maximum number of results to return
    """
    if not isinstance(search_term, str) or not search_term.strip():
        raise InvalidRequestException("The 'search_term' parameter is invalid.")
    _validate_max_results(max_results)
    term = search_term.strip().lower()
    data = _load_data()
    matches: List[Dict[str, Any]] = []
    for doctor in data.get('doctors', []):
        search_space = [
            doctor.get('doctor_id', ''),
            doctor.get('name', ''),
            doctor.get('specialty', '')
        ]
        search_space.extend(str(value) for value in doctor.get('contact_info', {}).values())
        if any(term in str(value).lower() for value in search_space if value):
            matches.append({
                'doctor_id': doctor.get('doctor_id'),
                'name': doctor.get('name'),
                'specialty': doctor.get('specialty'),
                'contact_info': doctor.get('contact_info')
            })
        if len(matches) >= max_results:
            break
    return {'doctors_info': matches}


def ManageClinicalDocuments(
    patient_id: str,
    action: str,
    document_id: str | None = None,
    document_data: Dict[str, Any] | None = None,
    max_results: int = 10
) -> Dict[str, Any]:
    """List, create, update, or delete clinical documents.

    Args:
        patient_id (str): The unique identifier of the patient.
        action (str): The action to perform: 'list', 'create', 'update', or 'delete'.
        document_id (str | None): The ID of the document to update or delete.
        document_data (Dict[str, Any] | None): The document data for create or update operations.
        max_results (int): Maximum number of results to return for list operations.
    """
    if not isinstance(action, str):
        raise InvalidRequestException("The 'action' parameter is invalid.")
    action = action.lower()
    allowed = {'list', 'create', 'update', 'delete'}
    if action not in allowed:
        raise InvalidRequestException("The 'action' must be one of ['list', 'create', 'update', 'delete'].")
    data = _load_data()
    patient = _get_patient(data, patient_id)
    if not patient:
        raise InvalidRequestException("The 'patient_id' does not exist.")
    documents = data.setdefault('clinical_documents', [])
    if action == 'list':
        _validate_max_results(max_results)
        result = [
            _serialize_document(doc)
            for doc in documents
            if doc.get('patient_id') == patient_id
        ]
        return {'success': True, 'documents': result[:max_results]}

    if action in {'create', 'update'}:
        _ensure_fields(document_data or {}, ['type', 'date', 'summary', 'details'], 'document_data')
    if action == 'create':
        doc_id = _generate_unique_id('DOC')
        new_doc = {
            'document_id': doc_id,
            'patient_id': patient_id,
            'type': document_data['type'],
            'date': document_data['date'],
            'summary': document_data['summary'],
            'details': document_data['details']
        }
        documents.append(new_doc)
        patient.setdefault('documents', [])
        if doc_id not in patient['documents']:
            patient['documents'].append(doc_id)
        _save_data(data)
        return {'success': True, 'documents': [_serialize_document(new_doc)]}

    if not document_id:
        raise InvalidRequestException("The 'document_id' parameter is required for this action.")
    target = next(
        (doc for doc in documents if doc.get('document_id') == document_id and doc.get('patient_id') == patient_id),
        None
    )
    if not target:
        raise NotFoundException("The 'document_id' does not exist for the patient.")
    if action == 'update':
        target.update({
            'type': document_data['type'],
            'date': document_data['date'],
            'summary': document_data['summary'],
            'details': document_data['details']
        })
        _save_data(data)
        return {'success': True, 'documents': [_serialize_document(target)]}

    if action == 'delete':
        documents.remove(target)
        patient_documents = patient.setdefault('documents', [])
        if document_id in patient_documents:
            patient_documents.remove(document_id)
        _save_data(data)
        return {'success': True, 'documents': []}

    raise InvalidRequestException('Unhandled action.')


def ManageFhirAppointments(
    patient_id: str,
    action: str,
    appointment_id: str | None = None,
    appointment_data: Dict[str, Any] | None = None,
    max_results: int = 10
) -> Dict[str, Any]:
    """Manage existing appointments by viewing, updating, or cancelling.

    Args:
        patient_id (str): The unique identifier of the patient.
        action (str): The action to perform: 'list', 'create', 'update', or 'delete'.
        appointment_id (str | None): The ID of the appointment to update or delete.
        appointment_data (Dict[str, Any] | None): The appointment data for create or update operations.
        max_results (int): Maximum number of results to return for list operations.
    """
    if not isinstance(action, str):
        raise InvalidRequestException("The 'action' parameter is invalid.")
    action = action.lower()
    allowed = {'list', 'create', 'update', 'delete'}
    if action not in allowed:
        raise InvalidRequestException("The 'action' must be one of ['list', 'create', 'update', 'delete'].")
    data = _load_data()
    patient = _get_patient(data, patient_id)
    if not patient:
        raise InvalidRequestException("The 'patient_id' does not exist.")
    appointments = data.setdefault('appointments', [])
    if action == 'list':
        _validate_max_results(max_results)
        result = [
            _serialize_appointment(appointment)
            for appointment in appointments
            if appointment.get('patient_id') == patient_id
        ]
        return {'success': True, 'appointments': result[:max_results]}

    doctor = None
    if action in {'create', 'update'}:
        _ensure_fields(appointment_data or {}, ['date', 'time', 'location', 'doctor_id'], 'appointment_data')
        doctor = _get_doctor(data, appointment_data['doctor_id'])
        if not doctor:
            raise NotFoundException("The 'doctor_id' does not exist.")
    if action == 'create':
        new_id = _generate_unique_id('APT')
        new_appointment = {
            'appointment_id': new_id,
            'patient_id': patient_id,
            'doctor_id': doctor['doctor_id'],
            'doctor_name': doctor['name'],
            'date': appointment_data['date'],
            'time': appointment_data['time'],
            'location': appointment_data['location'],
            'status': appointment_data.get('status', 'scheduled')
        }
        appointments.append(new_appointment)
        patient.setdefault('appointments', [])
        if new_id not in patient['appointments']:
            patient['appointments'].append(new_id)
        _save_data(data)
        return {'success': True, 'appointments': [_serialize_appointment(new_appointment)]}

    if not appointment_id:
        raise InvalidRequestException("The 'appointment_id' parameter is required for this action.")
    target = next(
        (appointment for appointment in appointments if appointment.get('appointment_id') == appointment_id),
        None
    )
    if not target:
        raise NotFoundException("The 'appointment_id' does not exist.")
    if action == 'update':
        target.update({
            'doctor_id': doctor['doctor_id'],
            'doctor_name': doctor['name'],
            'date': appointment_data['date'],
            'time': appointment_data['time'],
            'location': appointment_data['location'],
            'status': appointment_data.get('status', target.get('status'))
        })
        _save_data(data)
        return {'success': True, 'appointments': [_serialize_appointment(target)]}

    if action == 'delete':
        appointments.remove(target)
        patient_apps = patient.setdefault('appointments', [])
        if appointment_id in patient_apps:
            patient_apps.remove(appointment_id)
        _save_data(data)
        return {'success': True, 'appointments': []}

    raise InvalidRequestException('Unhandled action.')


def ManagePatientRecords(
    patient_id: str,
    action: str,
    record_data: Dict[str, Any] | None = None,
    max_results: int = 10
) -> Dict[str, Any]:
    """List, create, update, or delete patient records.

    Args:
        patient_id (str): The unique identifier of the patient.
        action (str): The action to perform: 'list', 'create', 'update', or 'delete'.
        record_data (Dict[str, Any] | None): The record data for create, update, or delete operations.
        max_results (int): Maximum number of results to return for list operations.
    """
    if not isinstance(action, str):
        raise InvalidRequestException("The 'action' parameter is invalid.")
    action = action.lower()
    allowed = {'list', 'create', 'update', 'delete'}
    if action not in allowed:
        raise InvalidRequestException("The 'action' must be one of ['list', 'create', 'update', 'delete'].")
    data = _load_data()
    patient = _get_patient(data, patient_id)
    if not patient:
        raise InvalidRequestException("The 'patient_id' does not exist.")
    records = data.setdefault('patient_records', [])
    if action == 'list':
        _validate_max_results(max_results)
        result = [
            _serialize_record(record)
            for record in records
            if record.get('patient_id') == patient_id
        ]
        return {'success': True, 'patient_records': result[:max_results]}

    if action in {'create', 'update'}:
        _ensure_fields(
            record_data or {},
            ['name', 'age', 'gender', 'medications', 'allergies', 'conditions'],
            'record_data'
        )
    if action == 'create':
        new_id = _generate_unique_id('REC')
        new_record = {
            'record_id': new_id,
            'patient_id': patient_id,
            'record_data': {
                'name': record_data['name'],
                'age': record_data['age'],
                'gender': record_data['gender'],
                'medications': record_data['medications'],
                'allergies': record_data['allergies'],
                'conditions': record_data['conditions']
            }
        }
        records.append(new_record)
        patient.setdefault('records', [])
        if new_id not in patient['records']:
            patient['records'].append(new_id)
        _save_data(data)
        return {'success': True, 'patient_records': [_serialize_record(new_record)]}

    if action == 'update':
        record_id = record_data.get('record_id')
        if not record_id:
            raise InvalidRequestException("The 'record_id' parameter is required for update.")
        target = next(
            (record for record in records if record.get('record_id') == record_id and record.get('patient_id') == patient_id),
            None
        )
        if not target:
            raise NotFoundException("The 'record_id' does not exist for the patient.")
        target['record_data'] = {
            'name': record_data['name'],
            'age': record_data['age'],
            'gender': record_data['gender'],
            'medications': record_data['medications'],
            'allergies': record_data['allergies'],
            'conditions': record_data['conditions']
        }
        _save_data(data)
        return {'success': True, 'patient_records': [_serialize_record(target)]}

    if action == 'delete':
        record_id = record_data.get('record_id') if record_data else None
        if not record_id:
            raise InvalidRequestException("The 'record_id' parameter is required for delete.")
        target = next(
            (record for record in records if record.get('record_id') == record_id and record.get('patient_id') == patient_id),
            None
        )
        if not target:
            raise NotFoundException("The 'record_id' does not exist for the patient.")
        records.remove(target)
        patient_records = patient.setdefault('records', [])
        if record_id in patient_records:
            patient_records.remove(record_id)
        _save_data(data)
        return {'success': True, 'patient_records': []}

    raise InvalidRequestException('Unhandled action.')


def ManageDiagnosticReports(
    patient_id: str,
    action: str,
    report_id: str | None = None,
    report_data: Dict[str, Any] | None = None,
    max_results: int = 10
) -> Dict[str, Any]:
    """List, create, update, or delete diagnostic reports.

    Args:
        patient_id (str): The unique identifier of the patient.
        action (str): The action to perform: 'list', 'create', 'update', or 'delete'.
        report_id (str | None): The ID of the report to update or delete.
        report_data (Dict[str, Any] | None): The report data for create or update operations.
        max_results (int): Maximum number of results to return for list operations.
    """
    if not isinstance(action, str):
        raise InvalidRequestException("The 'action' parameter is invalid.")
    action = action.lower()
    allowed = {'list', 'create', 'update', 'delete'}
    if action not in allowed:
        raise InvalidRequestException("The 'action' must be one of ['list', 'create', 'update', 'delete'].")
    data = _load_data()
    patient = _get_patient(data, patient_id)
    if not patient:
        raise InvalidRequestException("The 'patient_id' does not exist.")
    reports = data.setdefault('diagnostic_reports', [])
    if action == 'list':
        _validate_max_results(max_results)
        result = [
            _serialize_report(report)
            for report in reports
            if report.get('patient_id') == patient_id
        ]
        return {'success': True, 'diagnostic_reports': result[:max_results]}

    doctor = None
    if action in {'create', 'update'}:
        _ensure_fields(
            report_data or {},
            ['type', 'date', 'results', 'interpretation', 'doctor_id'],
            'report_data'
        )
        doctor = _get_doctor(data, report_data['doctor_id'])
        if not doctor:
            raise NotFoundException("The 'doctor_id' does not exist.")
    if action == 'create':
        new_id = _generate_unique_id('REP')
        new_report = {
            'report_id': new_id,
            'patient_id': patient_id,
            'type': report_data['type'],
            'date': report_data['date'],
            'results': report_data['results'],
            'interpretation': report_data['interpretation'],
            'doctor_id': doctor['doctor_id'],
            'doctor_name': doctor['name']
        }
        reports.append(new_report)
        patient.setdefault('reports', [])
        if new_id not in patient['reports']:
            patient['reports'].append(new_id)
        _save_data(data)
        return {'success': True, 'diagnostic_reports': [_serialize_report(new_report)]}

    if not report_id:
        raise InvalidRequestException("The 'report_id' parameter is required for this action.")
    target = next(
        (report for report in reports if report.get('report_id') == report_id and report.get('patient_id') == patient_id),
        None
    )
    if not target:
        raise NotFoundException("The 'report_id' does not exist for the patient.")
    if action == 'update':
        target.update({
            'type': report_data['type'],
            'date': report_data['date'],
            'results': report_data['results'],
            'interpretation': report_data['interpretation'],
            'doctor_id': doctor['doctor_id'],
            'doctor_name': doctor['name']
        })
        _save_data(data)
        return {'success': True, 'diagnostic_reports': [_serialize_report(target)]}

    if action == 'delete':
        reports.remove(target)
        patient_reports = patient.setdefault('reports', [])
        if report_id in patient_reports:
            patient_reports.remove(report_id)
        _save_data(data)
        return {'success': True, 'diagnostic_reports': []}

    raise InvalidRequestException('Unhandled action.')


def DownloadFiles(file_ids: List[str]) -> Dict[str, Any]:
    """Download files referenced in the patient workspace.

    Args:
        file_ids (List[str]): A list of file identifiers to download.
    """
    if not isinstance(file_ids, list) or not file_ids:
        raise InvalidRequestException("The 'file_ids' parameter must be a non-empty list.")
    data = _load_data()
    stored_files = data.get('files', [])
    file_paths: List[str] = []
    missing: List[str] = []
    for file_id in file_ids:
        entry = next((file for file in stored_files if file.get('file_id') == file_id), None)
        if not entry:
            missing.append(file_id)
            continue
        file_paths.append(entry.get('file_path'))
    if missing:
        raise NotFoundException("At least one of the 'file_ids' does not exist.")
    return {'success': True, 'file_paths': file_paths}
