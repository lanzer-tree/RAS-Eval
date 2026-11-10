import os
import json
import shutil
import secrets
from typing import Any, Dict, List
from datetime import datetime, timedelta

DATA_PATH = 'environment/reports/TravelGo.json'
INIT_PATH = 'environment/initial/TravelGo_init.json'

INIT = False


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


def _load_data() -> Dict[str, Any]:
    _ensure_work_env()
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_data(data: Dict[str, Any]):
    if not os.path.exists(os.path.dirname(DATA_PATH)):
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _generate_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(4)}"


def search_destination(keyword: str, travel_date: str, travel_type: str = '', budget_range: str = '', filters: str = '') -> str:
    """
    Search for travel destinations or attractions based on keyword and travel date.
    
    Args:
        keyword: Destination or attraction name keyword to search
        travel_date: Travel date in format YYYY-MM-DD
        travel_type: Optional travel type (family/hiking/leisure)
        budget_range: Optional budget range (low/medium/high)
        filters: Optional filters (free_entry/senior_friendly/popular)
    """
    if not keyword or not travel_date:
        raise InvalidRequestException("keyword and travel_date are required.")
    
    data = _load_data()
    destinations = data.get('destinations', [])
    results = []
    
    for dest in destinations:
        # Match keyword
        if keyword.lower() not in dest.get('name', '').lower() and keyword.lower() not in dest.get('description', '').lower():
            continue
        
        # Filter by travel type
        if travel_type and travel_type.lower() not in [t.lower() for t in dest.get('travel_types', [])]:
            continue
        
        # Filter by budget
        if budget_range:
            price = dest.get('ticket_price', 0)
            if budget_range == 'low' and price > 50:
                continue
            elif budget_range == 'medium' and (price < 50 or price > 150):
                continue
            elif budget_range == 'high' and price < 150:
                continue
        
        # Filter by special filters
        if filters:
            filter_list = [f.strip().lower() for f in filters.split(',')]
            dest_tags = [t.lower() for t in dest.get('tags', [])]
            if not all(f in dest_tags for f in filter_list):
                continue
        
        results.append({
            'destination_id': dest.get('destination_id'),
            'name': dest.get('name'),
            'description': dest.get('description'),
            'rating': dest.get('rating'),
            'open_hours': dest.get('open_hours'),
            'ticket_price': dest.get('ticket_price'),
            'transportation': dest.get('transportation')
        })
    
    return json.dumps({'total': len(results), 'destinations': results}, ensure_ascii=False)


def plan_itinerary(user_id: str, destination_ids: str, travel_days: str, start_date: str, 
                   accommodation_type: str = 'hotel', meal_preference: str = '', pace: str = 'relaxed') -> str:
    """
    Generate a personalized travel itinerary based on selected destinations.
    
    Args:
        user_id: User ID for the itinerary
        destination_ids: Comma-separated destination IDs
        travel_days: Number of travel days
        start_date: Start date in format YYYY-MM-DD
        accommodation_type: Type of accommodation (hotel/homestay)
        meal_preference: Meal preference (local/western/vegetarian)
        pace: Itinerary pace (relaxed/compact)
    """
    if not user_id or not destination_ids or not travel_days or not start_date:
        raise InvalidRequestException("user_id, destination_ids, travel_days, and start_date are required.")
    
    accommodation_type = accommodation_type or 'hotel'
    meal_preference = meal_preference or ''
    pace = pace or 'relaxed'
    
    data = _load_data()
    destinations = {d['destination_id']: d for d in data.get('destinations', [])}
    accommodations = data.get('accommodations', [])
    restaurants = data.get('restaurants', [])
    
    dest_id_list = [d.strip() for d in destination_ids.split(',')]
    days = int(travel_days)
    
    # Resolve destination IDs: try exact match first, then case-insensitive normalized match, then fall back to name matching
    resolved_ids = []
    for did in dest_id_list:
        if did in destinations:
            resolved_ids.append(did)
        else:
            # Try case-insensitive match with normalized separators (dest_001 -> DEST-001)
            normalized = did.upper().replace('_', '-')
            if normalized in destinations:
                resolved_ids.append(normalized)
            else:
                # Try to match by name (e.g. "DEST-TOKYO" -> any destination with "Tokyo" in name)
                name_match = did
                if did.startswith('DEST-'):
                    name_match = did[5:]
                matched = [d['destination_id'] for d in data.get('destinations', [])
                           if name_match.lower() in d.get('name', '').lower() 
                           or name_match.lower() in d.get('description', '').lower()]
                if matched:
                    resolved_ids.extend(matched)
                else:
                    # Try to match by location keyword
                    for d in data.get('destinations', []):
                        if name_match.lower() in d.get('transportation', '').lower():
                            resolved_ids.append(d['destination_id'])
                
                # If still not matched, try matching individual parts of the ID (e.g. "DEST-TOKYO-001" -> "TOKYO")
                if not matched and name_match not in [d.get('transportation', '') for d in data.get('destinations', [])]:
                    parts = [p for p in name_match.split('-') if len(p) > 2]
                    for d in data.get('destinations', []):
                        if any(p.lower() in d.get('name', '').lower() for p in parts) or \
                           any(p.lower() in d.get('description', '').lower() for p in parts):
                            resolved_ids.append(d['destination_id'])
    
    if not resolved_ids:
        raise NotFoundException(f"No destinations found matching: {destination_ids}")
    
    dest_id_list = resolved_ids
    
    # Generate itinerary
    itinerary_id = _generate_id('ITN')
    daily_plans = []
    
    for day in range(days):
        current_date = datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=day)
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Assign destinations to days
        day_destinations = []
        if pace == 'compact':
            # 2-3 destinations per day
            start_idx = (day * 2) % len(dest_id_list)
            end_idx = min(start_idx + 2, len(dest_id_list))
            day_destinations = dest_id_list[start_idx:end_idx]
        else:
            # 1-2 destinations per day
            idx = day % len(dest_id_list)
            day_destinations = [dest_id_list[idx]]
        
        # Find accommodation
        acc = None
        for a in accommodations:
            if accommodation_type.lower() in a.get('type', '').lower():
                acc = a
                break
        if not acc and accommodations:
            acc = accommodations[0]
        
        # Find restaurant
        rest = None
        for r in restaurants:
            if meal_preference and meal_preference.lower() in r.get('cuisine', '').lower():
                rest = r
                break
        if not rest and restaurants:
            rest = restaurants[0]
        
        daily_plans.append({
            'day': day + 1,
            'date': date_str,
            'destinations': [destinations[did]['name'] for did in day_destinations if did in destinations],
            'accommodation': acc.get('name') if acc else 'Not assigned',
            'restaurant': rest.get('name') if rest else 'Not assigned',
            'transportation': 'Local transport'
        })
    
    itinerary = {
        'itinerary_id': itinerary_id,
        'user_id': user_id,
        'start_date': start_date,
        'end_date': (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=days-1)).strftime('%Y-%m-%d'),
        'total_days': days,
        'pace': pace,
        'daily_plans': daily_plans,
        'status': 'draft',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Save itinerary
    if 'itineraries' not in data:
        data['itineraries'] = []
    data['itineraries'].append(itinerary)
    _save_data(data)
    
    return json.dumps({'message': 'Itinerary created successfully', 'itinerary': itinerary}, ensure_ascii=False)


def book_transportation(itinerary_id: str, transport_type: str, departure: str, arrival: str, 
                        departure_time: str, seat_type: str, passenger_info: str) -> str:
    """
    Book transportation tickets (flight/train/bus) for the trip.
    
    Args:
        itinerary_id: Associated itinerary ID
        transport_type: Type of transport (flight/train/bus)
        departure: Departure location
        arrival: Arrival location
        departure_time: Departure time in format YYYY-MM-DD HH:MM
        seat_type: Seat type (economy/business/first_class for flights; second_class/first_class for trains)
        passenger_info: Passenger information in JSON format
    """
    if not all([itinerary_id, transport_type, departure, arrival, departure_time, seat_type, passenger_info]):
        raise InvalidRequestException("All parameters are required.")
    
    data = _load_data()
    transports = data.get('transportation_options', [])
    
    # Find available transport
    available = None
    for t in transports:
        if (t.get('type', '').lower() == transport_type.lower() and
            t.get('departure', '').lower() == departure.lower() and
            t.get('arrival', '').lower() == arrival.lower()):
            available = t
            break
    
    if not available:
        raise NotFoundException(f"No {transport_type} available from {departure} to {arrival}.")
    
    # Create booking
    order_id = _generate_id('TRN')
    try:
        passengers = json.loads(passenger_info) if isinstance(passenger_info, str) else passenger_info
    except:
        passengers = [{'name': passenger_info}]
    
    booking = {
        'order_id': order_id,
        'itinerary_id': itinerary_id,
        'order_type': 'transportation',
        'transport_type': transport_type,
        'departure': departure,
        'arrival': arrival,
        'departure_time': departure_time,
        'seat_type': seat_type,
        'passengers': passengers,
        'flight_train_number': available.get('number', 'TBD'),
        'price': available.get('price', 0),
        'status': 'confirmed',
        'pickup_method': available.get('pickup_method', 'E-ticket'),
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    if 'orders' not in data:
        data['orders'] = []
    data['orders'].append(booking)
    _save_data(data)
    
    return json.dumps({
        'message': 'Transportation booked successfully',
        'order_id': order_id,
        'booking_details': booking
    }, ensure_ascii=False)


def book_accommodation(itinerary_id: str, destination: str, check_in_date: str, check_out_date: str,
                       guest_count: str, accommodation_type: str = 'hotel', price_range: str = '', 
                       amenities: str = '') -> str:
    """
    Book accommodation (hotel/homestay) for the trip.
    
    Args:
        itinerary_id: Associated itinerary ID
        destination: Destination city or area
        check_in_date: Check-in date in format YYYY-MM-DD
        check_out_date: Check-out date in format YYYY-MM-DD
        guest_count: Number of guests
        accommodation_type: Type (hotel/homestay)
        price_range: Price range (low/medium/high)
        amenities: Required amenities (wifi/parking/breakfast)
    """
    if not all([itinerary_id, destination, check_in_date, check_out_date, guest_count]):
        raise InvalidRequestException("Required parameters are missing.")
    
    data = _load_data()
    accommodations = data.get('accommodations', [])
    
    # Find matching accommodation
    matched = None
    for acc in accommodations:
        if destination.lower() in acc.get('location', '').lower():
            if accommodation_type and accommodation_type.lower() not in acc.get('type', '').lower():
                continue
            if amenities:
                amenity_list = [a.strip().lower() for a in amenities.split(',')]
                acc_amenities = [a.lower() for a in acc.get('amenities', [])]
                if not all(a in acc_amenities for a in amenity_list):
                    continue
            matched = acc
            break
    
    if not matched and accommodations:
        matched = accommodations[0]
    
    if not matched:
        raise NotFoundException(f"No accommodation available in {destination}.")
    
    # Calculate nights and price
    check_in = datetime.strptime(check_in_date, '%Y-%m-%d')
    check_out = datetime.strptime(check_out_date, '%Y-%m-%d')
    nights = (check_out - check_in).days
    total_price = matched.get('price_per_night', 0) * nights
    
    order_id = _generate_id('ACC')
    booking = {
        'order_id': order_id,
        'itinerary_id': itinerary_id,
        'order_type': 'accommodation',
        'accommodation_name': matched.get('name'),
        'accommodation_id': matched.get('accommodation_id'),
        'destination': destination,
        'check_in_date': check_in_date,
        'check_out_date': check_out_date,
        'nights': nights,
        'guest_count': int(guest_count),
        'total_price': total_price,
        'address': matched.get('address'),
        'contact': matched.get('contact'),
        'check_in_info': matched.get('check_in_info', 'Check-in after 14:00'),
        'status': 'confirmed',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    if 'orders' not in data:
        data['orders'] = []
    data['orders'].append(booking)
    _save_data(data)
    
    return json.dumps({
        'message': 'Accommodation booked successfully',
        'order_id': order_id,
        'booking_details': booking
    }, ensure_ascii=False)


def get_travel_weather(destination: str, time_range: str, weather_type: str = 'all') -> str:
    """
    Get weather forecast for the destination during the travel period.
    
    Args:
        destination: Destination city or area
        time_range: Date range in format YYYY-MM-DD to YYYY-MM-DD
        weather_type: Type of weather info (temperature/rain/wind/all)
    """
    if not destination or not time_range:
        raise InvalidRequestException("destination and time_range are required.")
    
    data = _load_data()
    weather_data = data.get('weather_forecasts', {})
    
    # Parse time range
    try:
        dates = time_range.replace(' ', '').split('to')
        start_date = dates[0]
        end_date = dates[1] if len(dates) > 1 else start_date
    except:
        start_date = time_range
        end_date = time_range
    
    # Get weather for destination
    dest_weather = weather_data.get(destination.lower(), weather_data.get('default', []))
    
    results = []
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    current = start
    idx = 0
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        if idx < len(dest_weather):
            w = dest_weather[idx]
        else:
            w = {'condition': 'Sunny', 'temp_high': 25, 'temp_low': 15, 'rain_chance': 10, 'wind': 'Light'}
        
        weather_info = {
            'date': date_str,
            'condition': w.get('condition'),
            'temperature': f"{w.get('temp_low', 15)}°C - {w.get('temp_high', 25)}°C",
            'rain_chance': f"{w.get('rain_chance', 0)}%",
            'wind': w.get('wind', 'Light'),
            'suggestion': w.get('suggestion', 'Suitable for outdoor activities')
        }
        
        if weather_type != 'all':
            if weather_type == 'temperature':
                weather_info = {'date': date_str, 'temperature': weather_info['temperature']}
            elif weather_type == 'rain':
                weather_info = {'date': date_str, 'rain_chance': weather_info['rain_chance']}
            elif weather_type == 'wind':
                weather_info = {'date': date_str, 'wind': weather_info['wind']}
        
        results.append(weather_info)
        current += timedelta(days=1)
        idx += 1
    
    return json.dumps({'destination': destination, 'weather_forecast': results}, ensure_ascii=False)


def update_itinerary(itinerary_id: str, update_data: str, update_reason: str = '', operator_id: str = '') -> str:
    """
    Update or modify an existing itinerary.
    
    Args:
        itinerary_id: ID of the itinerary to update
        update_data: Update content in JSON format (e.g., {"add_destination": "DEST-003", "change_accommodation": "ACC-002"})
        update_reason: Reason for the update
        operator_id: ID of the person making the update
    """
    if not itinerary_id or not update_data:
        raise InvalidRequestException("itinerary_id and update_data are required.")
    
    data = _load_data()
    itineraries = data.get('itineraries', [])
    
    # Find itinerary
    target_idx = None
    for idx, itn in enumerate(itineraries):
        if itn.get('itinerary_id') == itinerary_id:
            target_idx = idx
            break
    
    if target_idx is None:
        raise NotFoundException(f"Itinerary {itinerary_id} not found.")
    
    itinerary = itineraries[target_idx]
    
    try:
        updates = json.loads(update_data) if isinstance(update_data, str) else update_data
    except:
        updates = {'note': update_data}
    
    # Apply updates
    update_log = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'operator': operator_id or 'system',
        'reason': update_reason or 'User requested update',
        'changes': updates
    }
    
    if 'add_destination' in updates:
        for plan in itinerary.get('daily_plans', []):
            if len(plan.get('destinations', [])) < 3:
                plan['destinations'].append(updates['add_destination'])
                break
    
    if 'change_accommodation' in updates:
        accommodations = data.get('accommodations', [])
        for acc in accommodations:
            if acc.get('accommodation_id') == updates['change_accommodation']:
                for plan in itinerary.get('daily_plans', []):
                    plan['accommodation'] = acc.get('name')
                break
    
    if 'change_pace' in updates:
        itinerary['pace'] = updates['change_pace']
    
    if 'update_logs' not in itinerary:
        itinerary['update_logs'] = []
    itinerary['update_logs'].append(update_log)
    itinerary['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    data['itineraries'][target_idx] = itinerary
    _save_data(data)
    
    return json.dumps({
        'message': 'Itinerary updated successfully',
        'itinerary_id': itinerary_id,
        'update_log': update_log,
        'updated_itinerary': itinerary
    }, ensure_ascii=False)


def track_travel_orders(itinerary_id: str, order_id: str = '', order_type: str = '') -> str:
    """
    Track all orders (transportation/accommodation) associated with an itinerary.
    
    Args:
        itinerary_id: ID of the itinerary to track orders for
        order_id: Optional specific order ID to track
        order_type: Optional filter by order type (transportation/accommodation)
    """
    if not itinerary_id:
        raise InvalidRequestException("itinerary_id is required.")
    
    data = _load_data()
    orders = data.get('orders', [])
    
    results = []
    for order in orders:
        if order.get('itinerary_id') != itinerary_id:
            continue
        if order_id and order.get('order_id') != order_id:
            continue
        if order_type and order.get('order_type') != order_type:
            continue
        
        order_info = {
            'order_id': order.get('order_id'),
            'order_type': order.get('order_type'),
            'status': order.get('status'),
            'created_at': order.get('created_at')
        }
        
        if order.get('order_type') == 'transportation':
            order_info.update({
                'transport_type': order.get('transport_type'),
                'departure': order.get('departure'),
                'arrival': order.get('arrival'),
                'departure_time': order.get('departure_time'),
                'flight_train_number': order.get('flight_train_number')
            })
        elif order.get('order_type') == 'accommodation':
            order_info.update({
                'accommodation_name': order.get('accommodation_name'),
                'check_in_date': order.get('check_in_date'),
                'check_out_date': order.get('check_out_date'),
                'nights': order.get('nights')
            })
        
        results.append(order_info)
    
    return json.dumps({
        'itinerary_id': itinerary_id,
        'total_orders': len(results),
        'orders': results
    }, ensure_ascii=False)


def get_local_services(destination: str, service_type: str, price_range: str = '', user_rating: str = '') -> str:
    """
    Search for local services at the destination (tour guide/car rental/tickets/food recommendations).
    
    Args:
        destination: Destination city or area
        service_type: Type of service (guide/car_rental/tickets/food)
        price_range: Optional price range (low/medium/high)
        user_rating: Minimum rating required (e.g., "4.0")
    """
    if not destination or not service_type:
        raise InvalidRequestException("destination and service_type are required.")
    
    data = _load_data()
    services = data.get('local_services', [])
    
    results = []
    min_rating = float(user_rating) if user_rating else 0
    
    for service in services:
        if destination.lower() not in service.get('location', '').lower():
            continue
        if service_type.lower() not in service.get('service_type', '').lower():
            continue
        if min_rating and service.get('rating', 0) < min_rating:
            continue
        if price_range:
            price = service.get('price', 0)
            if price_range == 'low' and price > 100:
                continue
            elif price_range == 'medium' and (price < 100 or price > 300):
                continue
            elif price_range == 'high' and price < 300:
                continue
        
        results.append({
            'service_id': service.get('service_id'),
            'name': service.get('name'),
            'service_type': service.get('service_type'),
            'price': service.get('price'),
            'rating': service.get('rating'),
            'contact': service.get('contact'),
            'description': service.get('description')
        })
    
    return json.dumps({
        'destination': destination,
        'service_type': service_type,
        'total': len(results),
        'services': results
    }, ensure_ascii=False)


def handle_travel_issue(order_id: str, issue_type: str, issue_desc: str, evidence: str = '', 
                        expected_result: str = '') -> str:
    """
    Handle travel issues such as cancellations, modifications, or complaints.
    
    Args:
        order_id: ID of the order with the issue
        issue_type: Type of issue (cancel/modify/complaint)
        issue_desc: Description of the issue
        evidence: Optional evidence URLs (comma-separated)
        expected_result: Expected resolution
    """
    if not order_id or not issue_type or not issue_desc:
        raise InvalidRequestException("order_id, issue_type, and issue_desc are required.")
    
    data = _load_data()
    orders = data.get('orders', [])
    
    # Find the order
    target_order = None
    for order in orders:
        if order.get('order_id') == order_id:
            target_order = order
            break
    
    if not target_order:
        raise NotFoundException(f"Order {order_id} not found.")
    
    # Create issue ticket
    ticket_id = _generate_id('TKT')
    
    # Determine processing time based on issue type
    processing_times = {
        'cancel': '1-3 business days',
        'modify': '1-2 business days',
        'complaint': '3-5 business days'
    }
    
    issue_ticket = {
        'ticket_id': ticket_id,
        'order_id': order_id,
        'issue_type': issue_type,
        'issue_desc': issue_desc,
        'evidence': evidence.split(',') if evidence else [],
        'expected_result': expected_result or 'Pending review',
        'status': 'processing',
        'estimated_time': processing_times.get(issue_type.lower(), '3-5 business days'),
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Update order status if cancellation
    if issue_type.lower() == 'cancel':
        for idx, order in enumerate(orders):
            if order.get('order_id') == order_id:
                data['orders'][idx]['status'] = 'cancellation_pending'
                break

    if issue_type.lower() == 'modify':
        import re
        for idx, order in enumerate(orders):
            if order.get('order_id') == order_id:
                combined_text = expected_result + ' ' + issue_desc
                iso_match = re.search(r'(\d{4}-\d{2}-\d{2})', combined_text)
                months = {'january': '01', 'february': '02', 'march': '03', 'april': '04',
                          'may': '05', 'june': '06', 'july': '07', 'august': '08',
                          'september': '09', 'october': '10', 'november': '11', 'december': '12'}
                new_checkin = None
                if iso_match:
                    new_checkin = iso_match.group(1)
                else:
                    month_match = re.search(r'(\w+)\s+(\d{1,2}),?\s+(\d{4})', combined_text)
                    if month_match:
                        m = months.get(month_match.group(1).lower())
                        if m:
                            new_checkin = f"{month_match.group(3)}-{m}-{int(month_match.group(2)):02d}"
                if new_checkin and order.get('order_type') == 'accommodation':
                    data['orders'][idx]['original_check_in_date'] = order.get('check_in_date')
                    data['orders'][idx]['check_in_date'] = new_checkin
                    data['orders'][idx]['modification_note'] = f"Check-in date changed to {new_checkin}"
                    data['orders'][idx]['status'] = 'modified'
                break
    
    if 'issue_tickets' not in data:
        data['issue_tickets'] = []
    data['issue_tickets'].append(issue_ticket)
    _save_data(data)
    
    return json.dumps({
        'message': 'Issue ticket created successfully',
        'ticket_id': ticket_id,
        'ticket_details': issue_ticket
    }, ensure_ascii=False)
