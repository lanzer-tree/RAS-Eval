import json
import os
import shutil
from datetime import datetime
from math import ceil
from typing import Any, Dict, List, Optional

_WORKSPACE = '/workspace'
INIT_PATH = os.path.join(_WORKSPACE, 'environment', 'initial', 'carpark_init.json')
DATA_PATH = os.path.join(_WORKSPACE, 'environment', 'reports', 'carpark.json')

INIT = False


class InvalidRequestException(Exception):
    pass


class VehicleNotFoundException(Exception):
    pass


class SpotNotFoundException(Exception):
    pass


class SpotUnavailableException(Exception):
    pass


class PaymentProcessingException(Exception):
    pass


class StatisticsUnavailableException(Exception):
    pass


def _ensure_work_env() -> None:
    """Ensure the working environment file exists by copying from init if necessary."""
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


def _find_vehicle(data: Dict[str, Any], license_plate: str) -> Optional[Dict[str, Any]]:
    for vehicle in data.get('vehicles', []):
        if vehicle.get('license_plate') == license_plate:
            return vehicle
    return None


def _find_spot(data: Dict[str, Any], spot_id: str) -> Optional[Dict[str, Any]]:
    for spot in data.get('spots', []):
        if spot.get('spot_id') == spot_id:
            return spot
    return None


def register_vehicle(license_plate: str, vehicle_type: str, owner_info: Dict[str, Any]) -> Dict[str, Any]:
    """Register a new vehicle with owner details for the parking lot.

    Args:
        license_plate (str): The identifier of the incoming vehicle.
        vehicle_type (str): The category used for pricing (e.g., sedan, suv, ev).
        owner_info (Dict[str, Any]): Contact information for the vehicle owner.

    Returns:
        Dict[str, Any]: Success flag plus the stored vehicle record.

    Raises:
        InvalidRequestException: Raised when the request lacks required fields or the vehicle already exists.
    """
    if not license_plate or not license_plate.strip():
        raise InvalidRequestException('License plate is required.')
    data = _load_data()
    vehicles = data.setdefault('vehicles', [])
    if _find_vehicle(data, license_plate):
        raise InvalidRequestException('Vehicle already registered.')

    entry = {
        'license_plate': license_plate,
        'vehicle_type': vehicle_type,
        'owner_info': owner_info,
        'status': 'awaiting',
        'spot_id': '',
        'registered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    vehicles.append(entry)
    _save_data(data)
    return {'success': True, 'vehicle': entry}


def get_vehicle_info(license_plate: str) -> Dict[str, Any]:
    """Retrieve stored details for a specific vehicle.

    Args:
        license_plate (str): The license plate to look up.

    Returns:
        Dict[str, Any]: A dictionary containing the vehicle record.

    Raises:
        VehicleNotFoundException: Raised when no matching vehicle is available.
    """
    data = _load_data()
    vehicle = _find_vehicle(data, license_plate)
    if not vehicle:
        raise VehicleNotFoundException('Vehicle not found in the registry.')
    return {'vehicle': vehicle}


def update_vehicle_status(license_plate: str, new_status: str) -> Dict[str, Any]:
    """Update the status label for a vehicle.

    Args:
        license_plate (str): The vehicle that needs a status change.
        new_status (str): The new status label (e.g., parked, exited, paid).

    Returns:
        Dict[str, Any]: A success flag and updated state description.

    Raises:
        InvalidRequestException: When the new status is empty.
        VehicleNotFoundException: When the license plate is unregistered.
    """
    if not new_status:
        raise InvalidRequestException('Status value cannot be empty.')
    data = _load_data()
    vehicle = _find_vehicle(data, license_plate)
    if not vehicle:
        raise VehicleNotFoundException('Vehicle not found in the registry.')
    vehicle['status'] = new_status
    vehicle['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    _save_data(data)
    return {'success': True, 'license_plate': license_plate, 'new_status': new_status}


def delete_vehicle(license_plate: str) -> Dict[str, Any]:
    """Delete a vehicle from the registry and free its spot.

    Args:
        license_plate (str): The vehicle to remove from records.

    Returns:
        Dict[str, Any]: Confirmation that the record was deleted.

    Raises:
        VehicleNotFoundException: When the vehicle does not exist.
    """
    data = _load_data()
    vehicles = data.get('vehicles', [])
    vehicle = _find_vehicle(data, license_plate)
    if not vehicle:
        raise VehicleNotFoundException('Vehicle not found in the registry.')
    spot_id = vehicle.get('spot_id')
    vehicles.remove(vehicle)
    if spot_id:
        spot = _find_spot(data, spot_id)
        if spot:
            spot['status'] = 'available'
            spot['license_plate'] = ''
    _save_data(data)
    return {'success': True, 'message': f'{license_plate} removed from registry.'}


def get_available_spots(spot_type: Optional[str] = None) -> Dict[str, Any]:
    """List available spots, optionally filtering by type.

    Args:
        spot_type (Optional[str]): A spot category filter such as compact, large, or ev.

    Returns:
        Dict[str, Any]: Available spot list and count.
    """
    data = _load_data()
    spots = data.get('spots', [])
    candidates = [spot for spot in spots if spot.get('status') == 'available']
    if spot_type:
        candidates = [spot for spot in candidates if spot.get('type') == spot_type]
    return {'available_spots': candidates, 'count': len(candidates)}


def allocate_spot(license_plate: str, spot_id: str) -> Dict[str, Any]:
    """Assign an available spot to a registered vehicle.

    Args:
        license_plate (str): The vehicle that needs a spot.
        spot_id (str): The target parking spot to reserve.

    Returns:
        Dict[str, Any]: Confirmation of the allocation.

    Raises:
        VehicleNotFoundException: When the vehicle is not registered.
        SpotNotFoundException: When the spot does not exist.
        SpotUnavailableException: When the spot is already occupied.
    """
    data = _load_data()
    vehicle = _find_vehicle(data, license_plate)
    spot = _find_spot(data, spot_id)
    if not vehicle:
        raise VehicleNotFoundException('Vehicle not found in the registry.')
    if not spot:
        raise SpotNotFoundException('Spot does not exist.')
    if spot.get('status') != 'available':
        raise SpotUnavailableException('Spot is not available.')
    spot['status'] = 'occupied'
    spot['license_plate'] = license_plate
    vehicle['spot_id'] = spot_id
    vehicle['status'] = 'parked'
    vehicle['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    _save_data(data)
    return {'success': True, 'spot_id': spot_id, 'license_plate': license_plate}


def release_spot(spot_id: str) -> Dict[str, Any]:
    """Release a spot and update the associated vehicle status.

    Args:
        spot_id (str): The identifier of the spot to free.

    Returns:
        Dict[str, Any]: Success flag and the license plate that was released.

    Raises:
        SpotNotFoundException: When the spot identifier is invalid.
    """
    data = _load_data()
    spot = _find_spot(data, spot_id)
    if not spot:
        raise SpotNotFoundException('Spot does not exist.')
    if spot.get('status') != 'occupied':
        return {'success': False, 'message': 'Spot already available.'}
    license_plate = spot.get('license_plate')
    spot['status'] = 'available'
    spot['license_plate'] = ''
    if license_plate:
        vehicle = _find_vehicle(data, license_plate)
        if vehicle:
            vehicle['status'] = 'exited'
            vehicle['spot_id'] = ''
            vehicle['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    _save_data(data)
    return {'success': True, 'spot_id': spot_id, 'released_vehicle': license_plate}


def get_spot_status(spot_id: str) -> Dict[str, Any]:
    """Return the current status of a specific parking spot.

    Args:
        spot_id (str): The spot whose status should be retrieved.

    Returns:
        Dict[str, Any]: The spot metadata.

    Raises:
        SpotNotFoundException: When the spot is missing in the registry.
    """
    data = _load_data()
    spot = _find_spot(data, spot_id)
    if not spot:
        raise SpotNotFoundException('Spot does not exist.')
    return {'spot': spot}


def calculate_parking_fee(entry_time: str, exit_time: str, vehicle_type: str) -> Dict[str, Any]:
    """Calculate the parking fee based on time span and vehicle category.

    Args:
        entry_time (str): The start timestamp in the format YYYY-MM-DD HH:MM:SS.
        exit_time (str): The exit timestamp in the same format.
        vehicle_type (str): The vehicle category for pricing tables.

    Returns:
        Dict[str, Any]: Fee after rounding plus computed hours and vehicle type.

    Raises:
        InvalidRequestException: When the timestamps are invalid or inconsistent.
    """
    try:
        start = datetime.strptime(entry_time, '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime(exit_time, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        raise InvalidRequestException('Invalid datetime format; use YYYY-MM-DD HH:MM:SS.')
    if end <= start:
        raise InvalidRequestException('Exit time must be after entry time.')
    duration = end - start
    hours = ceil(duration.total_seconds() / 3600)
    rate_table = {'sedan': 2.5, 'suv': 3.5, 'truck': 4.5, 'ev': 2.2, 'compact': 2.0}
    rate = rate_table.get(vehicle_type.lower(), 3.0)
    fee = round(hours * rate, 2)
    return {'fee': fee, 'hours': hours, 'vehicle_type': vehicle_type}


def _update_statistics_on_payment(data: Dict[str, Any], amount: float) -> None:
    stats = data.setdefault('statistics', {})
    daily = stats.setdefault('daily', {})
    today = datetime.now()
    date_key = today.strftime('%Y-%m-%d')
    entry = daily.setdefault(date_key, {'entries': 0, 'exits': 0, 'revenue': 0.0})
    entry['revenue'] = round(entry.get('revenue', 0.0) + amount, 2)
    revenue_store = stats.setdefault('revenue', {})
    monthly_key = today.strftime('%Y-%m')
    yearly_key = today.strftime('%Y')
    revenue_store.setdefault(monthly_key, {'total': 0.0})
    revenue_store.setdefault(yearly_key, {'total': 0.0})
    revenue_store[monthly_key]['total'] = round(revenue_store[monthly_key]['total'] + amount, 2)
    revenue_store[yearly_key]['total'] = round(revenue_store[yearly_key]['total'] + amount, 2)


def process_payment(license_plate: str, amount: float, payment_method: str) -> Dict[str, Any]:
    """Record a payment made by a driver.

    Args:
        license_plate (str): The vehicle making the payment.
        amount (float): The amount collected.
        payment_method (str): The method used (card, cash, app).

    Returns:
        Dict[str, Any]: Confirmation that the payment was stored.

    Raises:
        PaymentProcessingException: When the amount is non-positive.
    """
    if amount <= 0:
        raise PaymentProcessingException('Amount must be greater than zero.')
    data = _load_data()
    payments = data.setdefault('payments', [])
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    payments.append({
        'license_plate': license_plate,
        'amount': amount,
        'payment_method': payment_method,
        'timestamp': timestamp
    })
    _update_statistics_on_payment(data, amount)
    _save_data(data)
    return {'success': True, 'amount': amount, 'method': payment_method, 'timestamp': timestamp}


def get_payment_history(license_plate: str) -> Dict[str, Any]:
    """Fetch all payment records for a specific vehicle.

    Args:
        license_plate (str): The license plate whose payments are needed.

    Returns:
        Dict[str, Any]: Payment history entries for the requested vehicle.
    """
    data = _load_data()
    payments = data.get('payments', [])
    history = [payment for payment in payments if payment.get('license_plate') == license_plate]
    return {'license_plate': license_plate, 'payments': history}


def get_daily_statistics(date: Optional[str] = None) -> Dict[str, Any]:
    """Provide entries, exits, and revenue for a target date.

    Args:
        date (Optional[str]): Specific day in YYYY-MM-DD format.

    Returns:
        Dict[str, Any]: Daily summary including entries, exits, and revenue.

    Raises:
        StatisticsUnavailableException: When requested data is absent.
    """
    data = _load_data()
    daily = data.get('statistics', {}).get('daily', {})
    if date:
        stats = daily.get(date)
        if not stats:
            return {'date': date, 'entries': 0, 'exits': 0, 'revenue': 0.0}
        return {'date': date, 'entries': stats.get('entries', 0), 'exits': stats.get('exits', 0), 'revenue': stats.get('revenue', 0.0)}
    if not daily:
        return {'date': 'N/A', 'entries': 0, 'exits': 0, 'revenue': 0.0}
    latest_date = sorted(daily.keys())[-1]
    stats = daily[latest_date]
    return {'date': latest_date, 'entries': stats.get('entries', 0), 'exits': stats.get('exits', 0), 'revenue': stats.get('revenue', 0.0)}


def get_occupancy_rate(time_range: Optional[str] = None) -> Dict[str, Any]:
    """Compute the current occupancy percentage for the lot.

    Args:
        time_range (Optional[str]): A human-friendly label for the requested window.

    Returns:
        Dict[str, Any]: Occupancy count, total spots, and rate string.
    """
    data = _load_data()
    spots = data.get('spots', [])
    total = len(spots)
    if total == 0:
        return {'time_range': time_range or 'current', 'occupied': 0, 'total': 0, 'rate': '0.00%'}
    occupied = len([spot for spot in spots if spot.get('status') == 'occupied'])
    rate = occupied / total
    return {
        'time_range': time_range or 'current',
        'occupied': occupied,
        'total': total,
        'rate': f"{rate:.2%}"
    }


def get_revenue_report(period: str) -> Dict[str, Any]:
    """Summarize revenue for a specified month or year.

    Args:
        period (str): Month (YYYY-MM) or year (YYYY) identifier.

    Returns:
        Dict[str, Any]: Period, total revenue, and source marker.
    """
    data = _load_data()
    revenue_store = data.get('statistics', {}).get('revenue', {})
    if period in revenue_store:
        total = revenue_store[period].get('total', 0.0)
        return {'period': period, 'total_revenue': round(total, 2), 'source': 'cached'}
    payments = data.get('payments', [])
    total = 0.0
    for payment in payments:
        if payment.get('timestamp', '').startswith(period):
            total += float(payment.get('amount', 0.0))
    return {'period': period, 'total_revenue': round(total, 2), 'source': 'computed'}
