import os
import json
import shutil
import secrets
from typing import Any, Dict, List

DATA_PATH = 'environment/reports/expedia.json'
INIT_PATH = 'environment/initial/expedia_init.json'

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


def _validate_max_results(value: Any, default: int = 5, max_allowed: int = 10) -> int:
    try:
        v = int(value) if value is not None else default
    except Exception:
        raise InvalidRequestException("The 'max_results' is not an integer between 1 and 10.")
    if v < 1 or v > max_allowed:
        raise InvalidRequestException("The 'max_results' is not an integer between 1 and 10.")
    return v


def _filter_price(item_price: float, filters: Dict[str, Any]) -> bool:
    min_p = filters.get('min_price')
    max_p = filters.get('max_price')
    if min_p is not None and item_price < min_p:
        return False
    if max_p is not None and item_price > max_p:
        return False
    return True


def _matches_query(obj: Dict[str, Any], query: str) -> bool:
    text = json.dumps(obj).lower()
    return query.lower() in text


def SearchFlights(origin: str, destination: str, departure_date: str, travellers: Dict[str, Any], travel_class: str,
                  return_date: str = '', max_results: int = 5, filters: Dict[str, Any] = None) -> Dict[str, Any]:
    """Search for available flights based on specified criteria.
    
    Args:
        origin (str): The departure airport code or city.
        destination (str): The arrival airport code or city.
        departure_date (str): The date of departure.
        travellers (Dict[str, Any]): Information about the travellers.
        travel_class (str): The class of travel (e.g., economy, business).
        return_date (str): The date of return flight, optional.
        max_results (int): Maximum number of results to return.
        filters (Dict[str, Any]): Additional filters like airline, stops, price range.
    """
    if not origin or not destination or not departure_date or not travellers or not travel_class:
        raise InvalidRequestException("Required parameters are missing or invalid.")
    max_results = _validate_max_results(max_results)
    data = _load_data()
    flights = data.get('flights', [])
    filters = filters or {}
    results = []
    for f in flights:
        if f.get('departure_date') != departure_date:
            continue
        if f.get('origin') != origin or f.get('destination') != destination:
            continue
        if travel_class and f.get('travel_class') != travel_class:
            continue
        if not _filter_price(f.get('price', 0), filters):
            continue
        if filters.get('airline') and filters['airline'] != f.get('airline'):
            continue
        if filters.get('stops_filter'):
            allowed = filters['stops_filter']
            stops_label = 'direct' if f.get('stops', 0) == 0 else ('1_stop' if f.get('stops') == 1 else '2_plus_stops')
            if stops_label not in allowed:
                continue
        results.append(f)
        if len(results) >= max_results:
            break
    # add return options if provided
    if return_date:
        for f in flights:
            if f.get('departure_date') != return_date:
                continue
            if f.get('origin') != destination or f.get('destination') != origin:
                continue
            if travel_class and f.get('travel_class') != travel_class:
                continue
            if not _filter_price(f.get('price', 0), filters):
                continue
            results.append(f)
            if len(results) >= max_results:
                break
    return {'flight_options': results[:max_results]}


def GetFlightDetails(departure_date: str, flight_number: str) -> Dict[str, Any]:
    """Get detailed information about a specific flight.
    
    Args:
        departure_date (str): The date of departure.
        flight_number (str): The flight number to look up.
    """
    data = _load_data()
    for f in data.get('flights', []):
        if f.get('departure_date') == departure_date and flight_number in f.get('flight_numbers', []):
            details = {
                'airline': f.get('airline'),
                'departure_airport': f.get('departure_airport'),
                'departure_time': f.get('departure_time'),
                'arrival_airport': f.get('arrival_airport'),
                'arrival_time': f.get('arrival_time'),
                'duration': f.get('duration'),
                'aircraft_type': f.get('aircraft_type', ''),
                'aircraft_age': f.get('aircraft_age', 0)
            }
            return {'flight_details': details}
    raise NotFoundException("'flight_number' not found for 'departure_date'.")


def SearchAccommodations(city: str, check_in_date: str, check_out_date: str, guests: List[Dict[str, Any]],
                         location: str = '', max_results: int = 5, filters: Dict[str, Any] = None) -> Dict[str, Any]:
    """Search for available accommodations based on specified criteria.
    
    Args:
        city (str): The city where accommodation is needed.
        check_in_date (str): The check-in date.
        check_out_date (str): The check-out date.
        guests (List[Dict[str, Any]]): List of guest information.
        location (str): Specific location within the city, optional.
        max_results (int): Maximum number of results to return.
        filters (Dict[str, Any]): Additional filters like accommodation type, room type, rating.
    """
    if not city or not check_in_date or not check_out_date or guests is None:
        raise InvalidRequestException("The 'city', dates, or 'guests' are invalid.")
    max_results = _validate_max_results(max_results)
    filters = filters or {}
    data = _load_data()
    options = []
    for acc in data.get('accommodations', []):
        if acc.get('city') != city:
            continue
        if location and location.lower() not in acc.get('address', '').lower():
            continue
        if not _filter_price(acc.get('total_price', 0), filters):
            continue
        if filters.get('accommodation_type') and filters['accommodation_type'] != acc.get('accommodation_type'):
            continue
        if filters.get('room_type') and filters['room_type'] != acc.get('room_type'):
            continue
        if filters.get('min_rating') and acc.get('rating', 0) < filters['min_rating']:
            continue
        if filters.get('free_cancellation') is True and acc.get('free_cancellation') is not True:
            continue
        if filters.get('free_breakfast') is True and acc.get('free_breakfast') is not True:
            continue
        if filters.get('allow_smoking') is False and acc.get('allow_smoking') is True:
            continue
        if filters.get('allow_pets') is False and acc.get('allow_pets') is True:
            continue
        options.append(acc)
        if len(options) >= max_results:
            break
    return {'accommodation_options': options[:max_results]}


def Booking(option_ids: List[str], payment_method: Dict[str, Any], travellers: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Book flights or accommodations with the specified options.
    
    Args:
        option_ids (List[str]): List of option IDs to book.
        payment_method (Dict[str, Any]): Payment information including card details.
        travellers (List[Dict[str, Any]]): List of traveller information, required for flights.
    """
    if not option_ids:
        raise InvalidRequestException("The 'option_ids' is empty.")
    if not payment_method or not all(k in payment_method for k in ['card_number', 'expiry_date']):
        raise InvalidRequestException("Payment information is invalid.")
    data = _load_data()
    flights = {f['option_id']: f for f in data.get('flights', [])}
    accs = {a['option_id']: a for a in data.get('accommodations', [])}

    flight_ids = [oid for oid in option_ids if oid in flights]
    acc_ids = [oid for oid in option_ids if oid in accs]
    unknown = [oid for oid in option_ids if oid not in flights and oid not in accs]
    if unknown:
        raise NotFoundException("One or more of the 'option_ids' does not exist.")
    if flight_ids and not travellers:
        raise InvalidRequestException("The 'travellers' parameter is not provided for flight booking.")

    results = []
    payment_last4 = payment_method['card_number'][-4:]
    timestamp = data.get('now_timestamp', '2025-01-01:10:00:00')

    if flight_ids:
        flight_total = round(sum(flights[oid].get('price', 0) for oid in flight_ids), 2)
        flight_reservation_id = f"res_{secrets.token_hex(6)}"
        flight_reservation = {
            'reservation_id': flight_reservation_id,
            'reservation_type': 'flight',
            'booking_timestamp': timestamp,
            'reservation_status': 'confirmed',
            'total_price': flight_total,
            'refundable_amount': round(flight_total * 0.8, 2),
            'options': flight_ids,
            'additional_information': {'travellers': travellers or [], 'payment_last4': payment_last4}
        }
        data.setdefault('reservations', []).append(flight_reservation)
        results.append({'success': True, 'reservation_id': flight_reservation_id, 'reservation_type': 'flight', 'total_price': flight_total})

    if acc_ids:
        acc_total = round(sum(accs[oid].get('total_price', 0) for oid in acc_ids), 2)
        acc_reservation_id = f"res_{secrets.token_hex(6)}"
        acc_reservation = {
            'reservation_id': acc_reservation_id,
            'reservation_type': 'accommodation',
            'booking_timestamp': timestamp,
            'reservation_status': 'confirmed',
            'total_price': acc_total,
            'refundable_amount': round(acc_total * 0.8, 2),
            'options': acc_ids,
            'additional_information': {'travellers': travellers or [], 'payment_last4': payment_last4}
        }
        data.setdefault('reservations', []).append(acc_reservation)
        results.append({'success': True, 'reservation_id': acc_reservation_id, 'reservation_type': 'accommodation', 'total_price': acc_total})

    _save_data(data)

    if len(results) == 1:
        return {'booking_results': results[0]}
    return {'booking_results': results}


def SearchReservations(reservation_type: str, query: str, start_date: str = '', end_date: str = '', max_results: int = 5) -> Dict[str, Any]:
    """Search for reservations based on type and query criteria.
    
    Args:
        reservation_type (str): Type of reservation ('flight' or 'accommodation').
        query (str): Search query string.
        start_date (str): Start date filter, optional.
        end_date (str): End date filter, optional.
        max_results (int): Maximum number of results to return.
    """
    if reservation_type not in ['flight', 'accommodation']:
        raise InvalidRequestException("The 'reservation_type' is not one of ['flight', 'accommodation'].")
    if not query:
        raise InvalidRequestException("The 'query' is empty.")
    max_results = _validate_max_results(max_results, default=5, max_allowed=50)
    data = _load_data()
    results = []
    for r in data.get('reservations', []):
        if r.get('reservation_type') != reservation_type:
            continue
        if not _matches_query(r, query):
            continue
        results.append(r)
        if len(results) >= max_results:
            break
    return {'reservations': results}


def CancelReservations(reservation_ids: List[str]) -> Dict[str, Any]:
    """Cancel one or more reservations.
    
    Args:
        reservation_ids (List[str]): List of reservation IDs to cancel.
    """
    if not reservation_ids:
        raise InvalidRequestException("The 'reservation_ids' is empty.")
    data = _load_data()
    id_to_res = {r['reservation_id']: r for r in data.get('reservations', [])}
    for rid in reservation_ids:
        if rid not in id_to_res:
            raise NotFoundException("One or more of the 'reservation_ids' does not exist.")
        if id_to_res[rid].get('reservation_status') == 'cancelled':
            raise InvalidRequestException("At least one of the reservations in 'reservation_ids' is already cancelled.")
    for rid in reservation_ids:
        id_to_res[rid]['reservation_status'] = 'cancelled'
        id_to_res[rid]['refundable_amount'] = round(id_to_res[rid].get('total_price', 0) * 0.8, 2)
    _save_data(data)
    return {'success': True}


def RetrieveSavedInformation(information_type: str) -> Dict[str, Any]:
    """Retrieve saved information of a specific type.
    
    Args:
        information_type (str): Type of information to retrieve ('payments' or 'people').
    """
    if information_type not in ['payments', 'people']:
        raise InvalidRequestException("The 'information_type' is not one of ['payments', 'people'].")
    data = _load_data()
    return {'retrieved_information': data.get('saved_information', {}).get(information_type, [])}
