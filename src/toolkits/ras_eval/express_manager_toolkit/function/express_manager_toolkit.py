import json
import os
import re
import shutil
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

DATA_PATH = os.path.join('environment', 'reports', 'expressManager.json')
INIT_PATH = os.path.join('environment', 'initial', 'expressManager_init.json')

INIT = False


class InvalidRequestException(Exception):
    pass


class NotFoundException(Exception):
    pass


def _ensure_work_env():
    #Ensure working environment file exists by copying from init if necessary.
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


def _write_env(data: Dict[str, Any]) -> None:
    if not os.path.exists(os.path.dirname(DATA_PATH)):
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _parse_dt(dt_str: str) -> datetime:
    try:
        return datetime.strptime(dt_str, '%Y-%m-%d:%H:%M:%S')
    except Exception:
        raise InvalidRequestException("Datetime must be in format 'YYYY-MM-DD:HH:MM:SS'.")


def _fmt_dt(dt: datetime) -> str:
    return dt.strftime('%Y-%m-%d:%H:%M:%S')


def _get_current_time(env: Dict[str, Any]) -> datetime:
    now_str = ((env.get('meta') or {}).get('current_time'))
    if not now_str:
        # fallback to a deterministic timestamp if missing
        now_str = '2025-12-18:08:00:00'
    return _parse_dt(now_str)


def _make_id(prefix: str, seed: str) -> str:
    """Make a stable identifier from a seed."""
    digest = uuid.uuid5(uuid.NAMESPACE_DNS, seed).hex[:16]
    return f"{prefix}{digest}"


def _validate_contact_number(phone: str) -> bool:
    if not phone or not isinstance(phone, str):
        return False
    # permissive but non-empty and digit-containing
    if not re.search(r"\d", phone):
        return False
    if len(phone) < 7 or len(phone) > 25:
        return False
    if not re.match(r"^[+0-9()\-\s]+$", phone):
        return False
    return True


def _validate_person_info(info: Dict[str, Any], field_name: str) -> None:
    if not isinstance(info, dict):
        raise InvalidRequestException(f"{field_name} must be an object")
    for k in ['full_name', 'address', 'contact_number']:
        if k not in info:
            raise InvalidRequestException(f"{field_name} missing required key '{k}'")
        if not isinstance(info.get(k), str) or not info.get(k).strip():
            raise InvalidRequestException(f"{field_name}.{k} is invalid")
    if not _validate_contact_number(info.get('contact_number', '')):
        raise InvalidRequestException(f"{field_name}.contact_number is invalid")


def _validate_package_details(package_details: Dict[str, Any]) -> None:
    if not isinstance(package_details, dict):
        raise InvalidRequestException('package_details must be an object')
    for k in ['description', 'weight', 'dimensions']:
        if k not in package_details:
            raise InvalidRequestException(f"package_details missing required key '{k}'")
    if not isinstance(package_details.get('description'), str) or not package_details['description'].strip():
        raise InvalidRequestException('package_details.description is invalid')
    try:
        weight = float(package_details.get('weight'))
    except Exception:
        raise InvalidRequestException('package_details.weight must be a number (grams)')
    if weight <= 0 or weight > 100000:
        raise InvalidRequestException('package_details.weight is out of allowed range')
    if not isinstance(package_details.get('dimensions'), str) or not package_details['dimensions'].strip():
        raise InvalidRequestException('package_details.dimensions is invalid')


def _validate_special_handling(special_handling: Optional[List[str]]) -> List[str]:
    allowed = {
        'signature_required',
        'fragile',
        'oversized',
        'dangerous_goods',
        'temperature_sensitive'
    }
    if special_handling is None:
        return []
    if not isinstance(special_handling, list):
        raise InvalidRequestException('special_handling must be an array')
    normalized = []
    for item in special_handling:
        if not isinstance(item, str) or item not in allowed:
            raise InvalidRequestException('special_handling contains invalid option')
        if item not in normalized:
            normalized.append(item)
    return normalized


def _shipping_methods() -> List[str]:
    return ['ground', 'express', 'overnight', '2-day']


def _eta_days(method: str) -> int:
    if method == 'ground':
        return 5
    if method == 'express':
        return 2
    if method == '2-day':
        return 2
    if method == 'overnight':
        return 1
    return 5


def _base_cost(method: str) -> float:
    if method == 'ground':
        return 8.0
    if method == '2-day':
        return 18.0
    if method == 'express':
        return 22.0
    if method == 'overnight':
        return 35.0
    return 10.0


def _rate_per_kg(method: str) -> float:
    if method == 'ground':
        return 4.0
    if method == '2-day':
        return 6.5
    if method == 'express':
        return 7.5
    if method == 'overnight':
        return 11.0
    return 5.0


def _special_handling_surcharge(special_handling: List[str]) -> float:
    surcharges = {
        'signature_required': 2.0,
        'fragile': 3.5,
        'oversized': 8.0,
        'dangerous_goods': 14.0,
        'temperature_sensitive': 12.0
    }
    return float(sum(surcharges.get(x, 0.0) for x in (special_handling or [])))


def GetQuote(
    package_details: Dict[str, Any],
    sender_information: Dict[str, Any],
    recipient_information: Dict[str, Any],
    pickup_time: str,
    special_handling: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Get a quote for shipping a package.

    Args:
        package_details (Dict[str, Any]): Must include 'description' (str), 'weight' (number, grams), and 'dimensions' (str, h*w*d in cm).
        sender_information (Dict[str, Any]): Sender info with 'full_name', 'address', and 'contact_number'.
        recipient_information (Dict[str, Any]): Recipient info with 'full_name', 'address', and 'contact_number'.
        pickup_time (str): Desired pickup time with format 'YYYY-MM-DD:HH:MM:SS'.
        special_handling (Optional[List[str]], optional): One or more of ['signature_required', 'fragile', 'oversized', 'dangerous_goods', 'temperature_sensitive'].

    Raises:
        InvalidRequestException: If inputs are invalid, pickup time is invalid/too soon,
            or special handling is invalid.
    """
    _validate_package_details(package_details)
    _validate_person_info(sender_information, 'sender_information')
    _validate_person_info(recipient_information, 'recipient_information')
    special = _validate_special_handling(special_handling)

    pickup_dt = _parse_dt(pickup_time)

    env = _read_env()
    now_dt = _get_current_time(env)
    # pickup must be at least 1 hour after "current_time" in env
    if pickup_dt < now_dt + timedelta(hours=1):
        raise InvalidRequestException('pickup_time is invalid or too soon')

    weight_g = float(package_details['weight'])
    weight_kg = weight_g / 1000.0

    shipping_quote: Dict[str, Any] = {}
    for method in _shipping_methods():
        cost = _base_cost(method) + _rate_per_kg(method) * weight_kg + _special_handling_surcharge(special)
        eta = pickup_dt + timedelta(days=_eta_days(method))
        shipping_quote[method] = {
            'shipping_cost': round(float(cost), 2),
            'estimated_delivery_date': _fmt_dt(eta)
        }

    seed = json.dumps(
        {
            'package_details': package_details,
            'sender_information': sender_information,
            'recipient_information': recipient_information,
            'pickup_time': pickup_time,
            'special_handling': special
        },
        sort_keys=True,
        ensure_ascii=False
    )
    quote_id = _make_id('qt_', seed)

    env.setdefault('quotes', {})[quote_id] = {
        'quote_id': quote_id,
        'package_details': package_details,
        'sender_information': sender_information,
        'recipient_information': recipient_information,
        'pickup_time': pickup_time,
        'special_handling': special,
        'shipping_quote': shipping_quote,
        'created_at': _fmt_dt(now_dt)
    }
    _write_env(env)

    return {'quote_id': quote_id, 'shipping_quote': shipping_quote}


def CreateShipmentLabel(quote_id: str, shipping_method: str) -> Dict[str, Any]:
    """Create a shipping label for a package.

    Args:
        quote_id (str): The unique identifier of the shipping quote.
        shipping_method (str): One of ['ground', 'express', 'overnight', '2-day'].

    Raises:
        NotFoundException: If the quote id does not exist.
        InvalidRequestException: If the shipping method is invalid for the quote.
    """
    if not quote_id or not isinstance(quote_id, str):
        raise InvalidRequestException('quote_id is invalid')
    if shipping_method not in _shipping_methods():
        raise InvalidRequestException('shipping_method is invalid')

    env = _read_env()
    quotes = env.get('quotes', {})
    quote = quotes.get(quote_id)
    if not quote:
        raise NotFoundException('quote_id does not exist')

    shipping_quote = quote.get('shipping_quote') or {}
    if shipping_method not in shipping_quote:
        raise InvalidRequestException('shipping method is not a valid option for the quote')

    shipment_id = _make_id('shp_', f"{quote_id}|{shipping_method}")
    now_dt = _get_current_time(env)

    pickup_time = quote.get('pickup_time')
    pickup_dt = _parse_dt(pickup_time)
    estimated_delivery_date = shipping_quote[shipping_method]['estimated_delivery_date']

    shipment = {
        'shipment_id': shipment_id,
        'shipment_status': {
            'status': 'pending',
            'description': 'Shipping label created. Awaiting pickup.',
            'timestamp': _fmt_dt(now_dt)
        },
        'sender_information': quote.get('sender_information'),
        'recipient_information': quote.get('recipient_information'),
        'dates': {
            'pickup_date': pickup_time,
            'actual_pickup_date': '',
            'estimated_delivery_date': estimated_delivery_date,
            'actual_delivery_date': ''
        },
        'package_details': quote.get('package_details'),
        'shipping_method': shipping_method,
        'special_handling': quote.get('special_handling', [])
    }

    env.setdefault('shipments', {})[shipment_id] = shipment
    _write_env(env)

    return {'shipment_id': shipment_id}


def GetShipmentDetails(shipment_id: str) -> Dict[str, Any]:
    """Get the current status and details of a shipment.

    Args:
        shipment_id (str): The unique identifier of the shipment.

    Raises:
        NotFoundException: If the shipment id does not exist.
    """
    if not shipment_id or not isinstance(shipment_id, str):
        raise InvalidRequestException('shipment_id is invalid')

    env = _read_env()
    shipments = env.get('shipments', {})
    shipment = shipments.get(shipment_id)
    if not shipment:
        raise NotFoundException('shipment_id does not exist')

    return {
        'shipment_status': shipment.get('shipment_status', {}),
        'sender_information': shipment.get('sender_information', {}),
        'recipient_information': shipment.get('recipient_information', {}),
        'dates': shipment.get('dates', {}),
        'package_details': shipment.get('package_details', {}),
        'shipping_method': shipment.get('shipping_method', ''),
        'special_handling': shipment.get('special_handling', [])
    }


def ManageShipment(
    shipment_id: str,
    operation: str,
    new_receipient_information: Optional[Dict[str, Any]] = None,
    new_pickup_time: Optional[str] = None
) -> Dict[str, Any]:
    """Manage a shipment (cancel, reschedule pickup, redirect, return to sender).

    Args:
        shipment_id (str): The unique identifier of the shipment.
        operation (str): One of ['cancel', 'reschedule_pickup', 'redirect', 'return_to_sender'].
        new_receipient_information (Optional[Dict[str, Any]], optional): New recipient info for redirect.
        new_pickup_time (str, optional): New pickup time for reschedule, format 'YYYY-MM-DD:HH:MM:SS'.

    Raises:
        InvalidRequestException: If inputs are invalid or operation violates status constraints.
        NotFoundException: If the shipment id does not exist.
    """
    if not shipment_id or not isinstance(shipment_id, str):
        raise InvalidRequestException('shipment_id is invalid')

    allowed_ops = ['cancel', 'reschedule_pickup', 'redirect', 'return_to_sender']
    if operation not in allowed_ops:
        raise InvalidRequestException('operation is invalid')

    env = _read_env()
    shipments = env.get('shipments', {})
    shipment = shipments.get(shipment_id)
    if not shipment:
        raise NotFoundException('shipment_id does not exist')

    status = (shipment.get('shipment_status') or {}).get('status')
    now_dt = _get_current_time(env)

    if operation in ['cancel', 'reschedule_pickup'] and status != 'pending':
        raise InvalidRequestException("'cancel' and 'reschedule_pickup' can only be performed when status is 'pending'")
    if operation in ['redirect', 'return_to_sender'] and status not in ('pending', 'in_transit'):
        raise InvalidRequestException("'redirect' and 'return_to_sender' can only be performed when status is 'pending' or 'in_transit'")

    if operation == 'cancel':
        shipment['shipment_status'] = {
            'status': 'cancelled',
            'description': 'Shipment cancelled before pickup.',
            'timestamp': _fmt_dt(now_dt)
        }
        _write_env(env)
        return {'operation_status': True}

    if operation == 'reschedule_pickup':
        if not new_pickup_time:
            raise InvalidRequestException('new_pickup_time is required for reschedule_pickup')
        new_dt = _parse_dt(new_pickup_time)
        if new_dt < now_dt + timedelta(hours=1):
            raise InvalidRequestException('new_pickup_time is invalid or too soon')
        shipment.setdefault('dates', {})['pickup_date'] = new_pickup_time
        # update estimated delivery date based on shipping_method
        method = shipment.get('shipping_method')
        shipment['dates']['estimated_delivery_date'] = _fmt_dt(new_dt + timedelta(days=_eta_days(method)))
        shipment['shipment_status'] = {
            'status': 'pending',
            'description': 'Pickup rescheduled.',
            'timestamp': _fmt_dt(now_dt)
        }
        _write_env(env)
        return {'operation_status': True}

    if operation == 'redirect':
        if not isinstance(new_receipient_information, dict):
            raise InvalidRequestException('new_receipient_information is required for redirect')
        _validate_person_info(new_receipient_information, 'new_receipient_information')
        shipment['recipient_information'] = new_receipient_information
        shipment['shipment_status'] = {
            'status': 'in_transit',
            'description': 'Shipment redirected to a new recipient/address.',
            'timestamp': _fmt_dt(now_dt)
        }
        _write_env(env)
        return {'operation_status': True}

    # return_to_sender
    sender = shipment.get('sender_information')
    if not isinstance(sender, dict):
        raise InvalidRequestException('sender_information missing on shipment')
    shipment['recipient_information'] = sender
    shipment['shipment_status'] = {
        'status': 'in_transit',
        'description': 'Return to sender requested. Package is being routed back to the sender.',
        'timestamp': _fmt_dt(now_dt)
    }
    shipment.setdefault('flags', {})['return_to_sender'] = True
    _write_env(env)
    return {'operation_status': True}


def SearchShipment(search_term: str) -> Dict[str, Any]:
    """Search for existing shipments.

    Args:
        search_term (str): Term to search in shipment details.

    Raises:
        InvalidRequestException: If the search term is invalid.
    """
    if search_term is None or not isinstance(search_term, str) or not search_term.strip():
        raise InvalidRequestException('search_term is invalid')

    env = _read_env()
    shipments = env.get('shipments', {})

    q = search_term.strip().lower()
    tokens = [t for t in re.split(r"\s+", q) if t]
    results = []
    for sid, s in shipments.items():
        status = ((s.get('shipment_status') or {}).get('status') or '')
        sender = (s.get('sender_information') or {})
        recipient = (s.get('recipient_information') or {})
        package_desc = (s.get('package_details') or {}).get('description', '')
        hay = ' '.join([
            sid,
            status,
            sender.get('full_name', ''),
            sender.get('address', ''),
            recipient.get('full_name', ''),
            recipient.get('address', ''),
            package_desc
        ]).lower()
        # require that all tokens appear somewhere in hay (simple AND matching)
        if all(tok in hay for tok in tokens):
            results.append({'shipment_id': sid, 'shipment_status': status})

    return {'shipments': results}


def SearchSavedAddresses(search_term: str) -> Dict[str, Any]:
    """Search for user's saved addresses and contact numbers.

    Args:
        search_term (str): The term to search for in the address details.

    """
    if search_term is None or not isinstance(search_term, str):
        raise InvalidRequestException('search_term is invalid')

    env = _read_env()
    addresses = env.get('saved_addresses', [])
    q = search_term.strip().lower()

    results = []
    for a in addresses:
        hay = ' '.join([
            str(a.get('remark', '')),
            str(a.get('full_name', '')),
            str(a.get('address', '')),
            str(a.get('contact_number', ''))
        ]).lower()
        if q in hay:
            results.append({
                'remark': a.get('remark', ''),
                'full_name': a.get('full_name', ''),
                'address': a.get('address', ''),
                'contact_number': a.get('contact_number', '')
            })

    return {'addresses': results}


# Convenience compatibility functions used by some agents (lowercase names)

def search_express_products(query: str) -> Dict[str, Any]:
    """Compatibility wrapper: search for available express shipping product options.

    Args:
        query (str): Query string, e.g., 'overnight shipping service'.

    """
    if query is None or not isinstance(query, str):
        raise InvalidRequestException('query is invalid')
    q = query.strip().lower()
    products = []
    # simple keyword matching to surface common shipping methods
    if 'overnight' in q or 'next day' in q:
        products.append({'name': 'overnight', 'description': 'Next-day delivery service', 'supports_signature': True})
    if 'express' in q or 'fast' in q:
        products.append({'name': 'express', 'description': 'Fast express delivery (2 days)', 'supports_signature': True})
    if 'ground' in q or 'standard' in q:
        products.append({'name': 'ground', 'description': 'Economical ground shipping (5 days)', 'supports_signature': True})
    return {'products': products}


def search_express_orders(query: str) -> Dict[str, Any]:
    """Compatibility wrapper: search for express shipments/orders by free-text.

    Args:
        query (str): Free-text query to match against shipments.

    """
    if query is None or not isinstance(query, str) or not query.strip():
        raise InvalidRequestException('search_term is invalid')

    env = _read_env()
    shipments = env.get('shipments', {})

    q = query.strip().lower()
    tokens = [t for t in re.split(r"\s+", q) if t]
    results = []
    for sid, s in shipments.items():
        status = ((s.get('shipment_status') or {}).get('status') or '')
        sender = (s.get('sender_information') or {})
        recipient = (s.get('recipient_information') or {})
        package_desc = (s.get('package_details') or {}).get('description', '')
        hay = ' '.join([
            sid,
            status,
            sender.get('full_name', ''),
            sender.get('address', ''),
            recipient.get('full_name', ''),
            recipient.get('address', ''),
            package_desc
        ]).lower()
        # require that all tokens appear somewhere in hay (simple AND matching)
        if all(tok in hay for tok in tokens):
            results.append({'shipment_id': sid, 'shipment_status': status})

    res = {'shipments': results}
    return {'orders': res.get('shipments', [])}


def get_express_order_details(order_id: str) -> Dict[str, Any]:
    """Compatibility wrapper to get express order/shipment details by id.

    Args:
        order_id (str): Shipment id.

    """
    try:
        details = GetShipmentDetails(order_id)
        return details
    except NotFoundException:
        return {'error': "The 'order_id' does not exist."}
    except InvalidRequestException:
        return {'error': "The 'order_id' is invalid."}
