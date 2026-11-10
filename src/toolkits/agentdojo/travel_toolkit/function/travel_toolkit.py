from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any

from src.toolkits.agentdojo.common import (
    CalendarEvent,
    CalendarState,
    CarRental,
    Email,
    EmailStatus,
    Flights,
    Hotels,
    InboxState,
    Reservation,
    ReservationType,
    Restaurants,
    User,
    EventStatus,
    parse_datetime,
)


@dataclass
class TravelEnvironment:
    hotels: Hotels
    restaurants: Restaurants
    car_rental: CarRental
    flights: Flights
    user: User
    calendar: CalendarState
    reservation: Reservation
    inbox: InboxState

    def snapshot(self) -> dict[str, Any]:
        return {
            "hotels": self.hotels.snapshot(),
            "restaurants": self.restaurants.snapshot(),
            "car_rental": self.car_rental.snapshot(),
            "flights": self.flights.snapshot(),
            "user": self.user.snapshot(),
            "calendar": self.calendar.snapshot(),
            "reservation": self.reservation.snapshot(),
            "inbox": self.inbox.snapshot(),
        }


def _send_email(inbox: InboxState, recipients: list[str], subject: str, body: str, attachments: list[Any] | None = None) -> Email:
    email = Email(
        id_=inbox.next_id(),
        sender=inbox.account_email,
        recipients=recipients,
        subject=subject,
        body=body,
        status=EmailStatus.sent,
        timestamp=dt.datetime.now(),
        attachments=[] if attachments is None else attachments,
        read=True,
    )
    inbox.emails[email.id_] = email
    return email


def get_user_information(environment: TravelEnvironment) -> dict[str, str]:
    """Get user information used for travel bookings.

    Returns:
        User information fields.
    """
    user = environment.user
    return {
        "First Name": user.first_name,
        "Last Name": user.last_name,
        "ID Number": user.ID_number,
        "Email": user.email,
        "Phone Number": user.phone_number,
        "Address": user.address,
        "Passport Number": user.passport_number,
        "Bank Account Number": user.bank_account_number,
        "Credit Card Number": user.credit_card_number,
    }


def get_all_hotels_in_city(environment: TravelEnvironment, city: str) -> str:
    """Get all hotels in the given city.

    Args:
        city: City to get hotels from.

    Returns:
        A newline-separated hotel name string.
    """
    names = [hotel.name for hotel in environment.hotels.hotel_list if hotel.city == city]
    return "Hotel Names: " + "\n".join(names) + "\n"


def get_hotels_prices(environment: TravelEnvironment, hotel_names: list[str]) -> dict[str, str]:
    """Get price ranges for hotels.

    Args:
        hotel_names: Hotel names to inspect.

    Returns:
        Hotel price ranges.
    """
    return {hotel.name: f"Price range: {hotel.price_min} - {hotel.price_max}" for hotel in environment.hotels.hotel_list if hotel.name in hotel_names}


def get_hotels_address(environment: TravelEnvironment, hotel_name: str) -> dict[str, str]:
    """Get the address of a hotel.

    Args:
        hotel_name: Hotel name.

    Returns:
        Matching hotel address.
    """
    return {hotel.name: hotel.address for hotel in environment.hotels.hotel_list if hotel.name == hotel_name}


def get_rating_reviews_for_hotels(environment: TravelEnvironment, hotel_names: list[str]) -> dict[str, str]:
    """Get rating and reviews for hotels.

    Args:
        hotel_names: Hotel names.

    Returns:
        Rating and review strings.
    """
    return {hotel.name: "Rating: " + str(hotel.rating) + "\n" + "Reviews: " + "\n".join(hotel.reviews) for hotel in environment.hotels.hotel_list if hotel.name in hotel_names}


def get_all_restaurants_in_city(environment: TravelEnvironment, city: str) -> str:
    """Get all restaurants in a city.

    Args:
        city: City to search.

    Returns:
        A newline-separated restaurant name string.
    """
    names = [restaurant.name for restaurant in environment.restaurants.restaurant_list if restaurant.city == city]
    return "Restaurant in " + city + ": " + "\n".join(names) + "\n"


def get_restaurants_address(environment: TravelEnvironment, restaurant_names: list[str]) -> dict[str, str]:
    """Get addresses for restaurants.

    Args:
        restaurant_names: Restaurant names.

    Returns:
        Restaurant addresses.
    """
    return {restaurant.name: restaurant.address for restaurant in environment.restaurants.restaurant_list if restaurant.name in restaurant_names}


def get_rating_reviews_for_restaurants(environment: TravelEnvironment, restaurant_names: list[str]) -> dict[str, str]:
    """Get rating and reviews for restaurants.

    Args:
        restaurant_names: Restaurant names.

    Returns:
        Rating and review strings.
    """
    return {restaurant.name: "Rating: " + str(restaurant.rating) + "\n" + "Reviews: " + "\n".join(restaurant.reviews) for restaurant in environment.restaurants.restaurant_list if restaurant.name in restaurant_names}


def get_cuisine_type_for_restaurants(environment: TravelEnvironment, restaurant_names: list[str]) -> dict[str, str]:
    """Get cuisine types for restaurants.

    Args:
        restaurant_names: Restaurant names.

    Returns:
        Cuisine type by restaurant.
    """
    return {restaurant.name: restaurant.cuisine_type for restaurant in environment.restaurants.restaurant_list if restaurant.name in restaurant_names}


def get_dietary_restrictions_for_all_restaurants(environment: TravelEnvironment, restaurant_names: list[str]) -> dict[str, str]:
    """Get dietary restrictions for restaurants.

    Args:
        restaurant_names: Restaurant names.

    Returns:
        Dietary restriction by restaurant.
    """
    joined_names = ", ".join(restaurant_names)
    return {restaurant.name: restaurant.dietary_restrictions for restaurant in environment.restaurants.restaurant_list if restaurant.name in joined_names}


def get_contact_information_for_restaurants(environment: TravelEnvironment, restaurant_names: list[str]) -> dict[str, str]:
    """Get restaurant contact information.

    Args:
        restaurant_names: Restaurant names.

    Returns:
        Contact information by restaurant.
    """
    return {restaurant.name: restaurant.contact_information for restaurant in environment.restaurants.restaurant_list if restaurant.name in restaurant_names}


def get_price_for_restaurants(environment: TravelEnvironment, restaurant_names: list[str]) -> dict[str, float]:
    """Get price per person for restaurants.

    Args:
        restaurant_names: Restaurant names.

    Returns:
        Price per person by restaurant.
    """
    return {restaurant.name: restaurant.price_per_person for restaurant in environment.restaurants.restaurant_list if restaurant.name in restaurant_names}


def check_restaurant_opening_hours(environment: TravelEnvironment, restaurant_names: list[str]) -> dict[str, str]:
    """Get operating hours for restaurants.

    Args:
        restaurant_names: Restaurant names.

    Returns:
        Operating hours by restaurant.
    """
    return {restaurant.name: restaurant.operating_hours for restaurant in environment.restaurants.restaurant_list if restaurant.name in restaurant_names}


def get_all_car_rental_companies_in_city(environment: TravelEnvironment, city: str) -> str:
    """Get all car rental companies in a city.

    Args:
        city: City to search.

    Returns:
        A newline-separated company name string.
    """
    names = [company.name for company in environment.car_rental.company_list if company.city == city]
    return "Car Rental Companies in " + city + ": " + "\n".join(names) + "\n"


def get_car_types_available(environment: TravelEnvironment, company_name: list[str]) -> dict[str, list]:
    """Get car types for rental companies.

    Args:
        company_name: Company names.

    Returns:
        Available car types.
    """
    return {company.name: company.car_types_available for company in environment.car_rental.company_list if company.name in company_name}


def get_rating_reviews_for_car_rental(environment: TravelEnvironment, company_name: list[str]) -> dict[str, str]:
    """Get rating and reviews for car rental companies.

    Args:
        company_name: Company names.

    Returns:
        Rating and review strings.
    """
    return {company.name: "Rating: " + str(company.rating) + "\n" + "Reviews: " + "\n".join(company.reviews) for company in environment.car_rental.company_list if company.name in company_name}


def get_car_rental_address(environment: TravelEnvironment, company_name: list[str]) -> dict[str, str]:
    """Get addresses for car rental companies.

    Args:
        company_name: Company names.

    Returns:
        Addresses by company.
    """
    return {company.name: company.address for company in environment.car_rental.company_list if company.name in company_name}


def get_car_fuel_options(environment: TravelEnvironment, company_name: list[str]) -> dict[str, list]:
    """Get fuel options for car rental companies.

    Args:
        company_name: Company names.

    Returns:
        Fuel options by company.
    """
    return {company.name: company.fuel_options for company in environment.car_rental.company_list if company.name in company_name}


def get_car_price_per_day(environment: TravelEnvironment, company_name: list[str]) -> dict[str, float]:
    """Get price per day for car rental companies.

    Args:
        company_name: Company names.

    Returns:
        Price per day by company.
    """
    return {company.name: company.price_per_day for company in environment.car_rental.company_list if company.name in company_name}


def create_calendar_event(
    environment: TravelEnvironment,
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    participants: list[str] | None = None,
    location: str | None = None,
) -> CalendarEvent:
    """Create a calendar event and send an invitation email.

    Args:
        title: Event title.
        start_time: Start time in YYYY-MM-DD HH:MM format.
        end_time: End time in YYYY-MM-DD HH:MM format.
        description: Event description.
        participants: Participant emails.
        location: Optional event location.

    Returns:
        Created event.
    """
    participants = [] if participants is None else list(participants)
    participants.append(environment.calendar.account_email)
    unique_participants = list(set(participants))
    event = CalendarEvent(
        id_=environment.calendar.next_id(),
        title=title,
        description=description,
        start_time=parse_datetime(start_time),
        end_time=parse_datetime(end_time),
        location=location,
        participants=unique_participants,
    )
    environment.calendar.events[event.id_] = event
    _send_email(environment.inbox, unique_participants, f"Invitation: {title}", description, [event])
    return event


def search_calendar_events(environment: TravelEnvironment, query: str, date: str | None = None) -> list[CalendarEvent]:
    """Search calendar events by title or description.

    Args:
        query: Query string.
        date: Optional YYYY-MM-DD date.

    Returns:
        Matching events.
    """
    events = environment.calendar.events.values()
    if date is not None:
        parsed_date = dt.datetime.strptime(date, "%Y-%m-%d").date()
        events = [event for event in events if event.start_time.date() == parsed_date]
    matches = [event for event in events if query.lower() in event.title.lower() or query.lower() in event.description.lower()]
    if not matches:
        raise ValueError("No events found. Try with a different query.")
    return matches


def get_day_calendar_events(environment: TravelEnvironment, day: str) -> list[CalendarEvent]:
    """Return appointments for a day.

    Args:
        day: Day in YYYY-MM-DD format.

    Returns:
        Calendar events on the day.
    """
    parsed_day = dt.datetime.strptime(day, "%Y-%m-%d").date()
    return [event for event in environment.calendar.events.values() if event.start_time.date() == parsed_day]


def cancel_calendar_event(environment: TravelEnvironment, event_id: str) -> str:
    """Cancel a calendar event and notify participants.

    Args:
        event_id: Event ID.

    Returns:
        A confirmation message.
    """
    if event_id not in environment.calendar.events:
        raise ValueError(f"Event with ID '{event_id}' not found.")
    event = environment.calendar.events[event_id]
    event.status = EventStatus.canceled
    _send_email(environment.inbox, event.participants, f"Canceled: '{event.title}'", "The event has been canceled.", [event])
    return f"Event with ID {event_id} has been canceled and participants have been notified."


def reserve_hotel(environment: TravelEnvironment, hotel: str, start_day: str, end_day: str) -> str:
    """Make a hotel reservation.

    Args:
        hotel: Hotel name.
        start_day: Check-in day in YYYY-MM-DD format.
        end_day: Check-out day in YYYY-MM-DD format.

    Returns:
        A confirmation message.
    """
    environment.reservation.contact_information = get_user_information(environment)["Phone Number"]
    environment.reservation.reservation_type = ReservationType.HOTEL
    environment.reservation.title = hotel
    environment.reservation.start_time = dt.datetime.fromisoformat(start_day)
    environment.reservation.end_time = dt.datetime.fromisoformat(end_day)
    return f"Reservation for {hotel} from {start_day} to {end_day} has been made successfully."


def reserve_restaurant(environment: TravelEnvironment, restaurant: str, start_time: str) -> str:
    """Make a restaurant reservation.

    Args:
        restaurant: Restaurant name.
        start_time: Reservation start time in YYYY-MM-DD HH:MM format.

    Returns:
        A confirmation message.
    """
    environment.reservation.contact_information = get_user_information(environment)["Phone Number"]
    environment.reservation.reservation_type = ReservationType.RESTAURANT
    environment.reservation.title = restaurant
    environment.reservation.start_time = dt.datetime.fromisoformat(start_time)
    environment.reservation.end_time = dt.datetime.fromisoformat(start_time) + dt.timedelta(hours=2)
    date = environment.reservation.start_time.date().isoformat()
    start_clock = environment.reservation.start_time.strftime("%H:%M")
    end_clock = environment.reservation.end_time.strftime("%H:%M")
    return f"Reservation for {restaurant} from {start_clock} to {end_clock} on {date} has been made successfully."


def reserve_car_rental(environment: TravelEnvironment, company: str, start_time: str, end_time: str | None) -> str:
    """Make a car rental reservation.

    Args:
        company: Car rental company.
        start_time: Reservation start time in YYYY-MM-DD HH:MM format.
        end_time: Reservation end time in YYYY-MM-DD HH:MM format.

    Returns:
        A confirmation message.
    """
    environment.reservation.contact_information = get_user_information(environment)["Phone Number"]
    environment.reservation.reservation_type = ReservationType.CAR
    environment.reservation.title = company
    environment.reservation.start_time = dt.datetime.fromisoformat(start_time)
    environment.reservation.end_time = dt.datetime.fromisoformat(start_time)
    return f"Reservation for a car at {company} from {start_time} to {end_time} has been made successfully."


def get_flight_information(environment: TravelEnvironment, departure_city: str, arrival_city: str) -> str:
    """Get flight information for a route.

    Args:
        departure_city: City to depart from.
        arrival_city: City to arrive at.

    Returns:
        Matching flight information.
    """
    info = [
        f"Airline: {flight.airline}, Flight Number: {flight.flight_number}, Departure Time: {flight.departure_time}, Arrival Time: {flight.arrival_time}, Price: {flight.price}, Contact Information: {flight.contact_information}"
        for flight in environment.flights.flight_list
        if flight.departure_city == departure_city and flight.arrival_city == arrival_city
    ]
    return "\n".join(info)


def send_email(environment: TravelEnvironment, recipients: list[str], subject: str, body: str, attachments: list[dict] | None = None) -> Email:
    """Send an email from the travel inbox.

    Args:
        recipients: Recipient email addresses.
        subject: Email subject.
        body: Email body.
        attachments: Optional attachment dictionaries.

    Returns:
        Created sent email.
    """
    return _send_email(environment.inbox, recipients, subject, body, [] if attachments is None else attachments)


TOOLS = [
    get_user_information,
    get_all_hotels_in_city,
    get_hotels_prices,
    get_rating_reviews_for_hotels,
    get_hotels_address,
    get_all_restaurants_in_city,
    get_cuisine_type_for_restaurants,
    get_restaurants_address,
    get_rating_reviews_for_restaurants,
    get_dietary_restrictions_for_all_restaurants,
    get_contact_information_for_restaurants,
    get_price_for_restaurants,
    check_restaurant_opening_hours,
    get_all_car_rental_companies_in_city,
    get_car_types_available,
    get_rating_reviews_for_car_rental,
    get_car_fuel_options,
    get_car_rental_address,
    get_car_price_per_day,
    create_calendar_event,
    search_calendar_events,
    get_day_calendar_events,
    cancel_calendar_event,
    reserve_hotel,
    reserve_car_rental,
    reserve_restaurant,
    get_flight_information,
    send_email,
]
