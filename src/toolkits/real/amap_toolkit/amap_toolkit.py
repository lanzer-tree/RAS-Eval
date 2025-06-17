from langchain_core.tools import tool
from mcp.server.fastmcp import FastMCP
import os
import requests
from typing import Optional


mcp = FastMCP('amap_toolkit')
def amap_geocode(address: str, city: Optional[str]=None) -> dict:
    """
    Get the latitude and longitude and administrative division of a address.

    Args:
        address (str): The address to get the latitude and longitude of.
        city (str): The city of the address.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    url = 'https://restapi.amap.com/v3/geocode/geo'
    key = os.getenv('AMAP_KEY')
    params = {'key': key, 'address': address, 'output': 'json'}
    if city:
        params['city'] = city
    response = requests.get(url, params=params).json()
    if response['status'] != '1':
        return {'success': False, 'detail': response['info']}
    else:
        result = {'success': True, 'address': response['geocodes'][0]['formatted_address'], 'country': response['geocodes'][0]['country'], 'province': response['geocodes'][0]['province'], 'city': response['geocodes'][0]['city'], 'citycode': response['geocodes'][0]['citycode'], 'address_code': response['geocodes'][0]['adcode'], 'district': response['geocodes'][0]['district'], 'location': response['geocodes'][0]['location']}
        return result


@tool(parse_docstring=True)
def langgraph_amap_geocode(address: str, city: Optional[str]=None) -> dict:
    """
    Get the latitude and longitude and administrative division of a address.

    Args:
        address (str): The address to get the latitude and longitude of.
        city (str): The city of the address.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_geocode(address=address, city=city)


@mcp.tool()
def mcp_amap_geocode(address: str, city: Optional[str]=None) -> dict:
    """
    Get the latitude and longitude and administrative division of a address.

    Args:
        address (str): The address to get the latitude and longitude of.
        city (str): The city of the address.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_geocode(address=address, city=city)


def amap_regeocode(location: str) -> dict:
    """
    Get the address and administrative division of a latitude and longitude.

    Args:
        location (str): The langitude and latitude of the address, separated by a comma. e.g. "120.123612,30.266521".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    url = 'https://restapi.amap.com/v3/geocode/regeo?parameters'
    key = os.getenv('AMAP_KEY')
    params = {'key': key, 'location': location, 'output': 'json'}
    response = requests.get(url, params=params).json()
    if response['status'] != '1':
        return {'success': False, 'detail': response['info']}
    else:
        result = {'success': True, 'address': response['regeocode']['formatted_address'], 'country': response['regeocode']['addressComponent']['country'], 'province': response['regeocode']['addressComponent']['province'], 'city': response['regeocode']['addressComponent']['city'], 'citycode': response['regeocode']['addressComponent']['citycode'], 'district': response['regeocode']['addressComponent']['district'], 'address_code': response['regeocode']['addressComponent']['adcode'], 'township': response['regeocode']['addressComponent']['township'], 'street': response['regeocode']['addressComponent']['streetNumber']['street'], 'street_number': response['regeocode']['addressComponent']['streetNumber']['number']}
        return result


@tool(parse_docstring=True)
def langgraph_amap_regeocode(location: str) -> dict:
    """
    Get the address and administrative division of a latitude and longitude.

    Args:
        location (str): The langitude and latitude of the address, separated by a comma. e.g. "120.123612,30.266521".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_regeocode(location=location)


@mcp.tool()
def mcp_amap_regeocode(location: str) -> dict:
    """
    Get the address and administrative division of a latitude and longitude.

    Args:
        location (str): The langitude and latitude of the address, separated by a comma. e.g. "120.123612,30.266521".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_regeocode(location=location)


def amap_direction_walking(origin: str, destination: str) -> dict:
    """
    Get the walking route from origin to destination.

    Args:
        origin (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521".
        destination (str): The langitude and latitude of the destination, separated by a comma. e.g. "120.123700,30.266501".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    url = 'https://restapi.amap.com/v3/direction/walking?parameters'
    key = os.getenv('AMAP_KEY')
    params = {'key': key, 'origin': origin, 'destination': destination, 'output': 'json'}
    response = requests.get(url, params=params).json()
    if response['status'] != '1':
        return {'success': False, 'detail': response['info']}
    else:
        result = {'success': True, 'steps': []}
        for step in response['route']['paths'][0]['steps']:
            result['steps'].append(step['instruction'])
        return result


@tool(parse_docstring=True)
def langgraph_amap_direction_walking(origin: str, destination: str) -> dict:
    """
    Get the walking route from origin to destination.

    Args:
        origin (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521".
        destination (str): The langitude and latitude of the destination, separated by a comma. e.g. "120.123700,30.266501".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_direction_walking(origin=origin, destination=destination)


@mcp.tool()
def mcp_amap_direction_walking(origin: str, destination: str) -> dict:
    """
    Get the walking route from origin to destination.

    Args:
        origin (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521".
        destination (str): The langitude and latitude of the destination, separated by a comma. e.g. "120.123700,30.266501".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_direction_walking(origin=origin, destination=destination)


def amap_direction_transit(origin: str, destination: str, city: str, cityd: Optional[str]=None) -> dict:
    """
    Get the transit route from origin to destination.

    Args:
        origin (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521".
        destination (str): The langitude and latitude of the destination, separated by a comma. e.g. "120.123700,30.266501".
        city (str): The city of the origin.
        cityd (str): The city of the destination.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    url = 'https://restapi.amap.com/v3/direction/transit/integrated?parameters'
    key = os.getenv('AMAP_KEY')
    params = {'key': key, 'origin': origin, 'destination': destination, 'city': city, 'strategy': 0, 'output': 'json'}
    if cityd:
        params['cityd'] = cityd
    response = requests.get(url, params=params).json()
    if response['status'] != '1':
        return {'success': False, 'detail': response['info']}
    else:
        result = {'success': True, 'transits': []}
        for transit in response['route']['transits'][0]['segments']:
            if transit['bus']['buslines']:
                result['transits'].append({'departure_stop': transit['bus']['buslines'][0]['departure_stop'], 'arrival_stop': transit['bus']['buslines'][0]['arrival_stop'], 'name': transit['bus']['buslines'][0]['name']})
        return result


@tool(parse_docstring=True)
def langgraph_amap_direction_transit(origin: str, destination: str, city: str, cityd: Optional[str]=None) -> dict:
    """
    Get the transit route from origin to destination.

    Args:
        origin (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521".
        destination (str): The langitude and latitude of the destination, separated by a comma. e.g. "120.123700,30.266501".
        city (str): The city of the origin.
        cityd (str): The city of the destination.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_direction_transit(origin=origin, destination=destination, city=city, cityd=cityd)


@mcp.tool()
def mcp_amap_direction_transit(origin: str, destination: str, city: str, cityd: Optional[str]=None) -> dict:
    """
    Get the transit route from origin to destination.

    Args:
        origin (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521".
        destination (str): The langitude and latitude of the destination, separated by a comma. e.g. "120.123700,30.266501".
        city (str): The city of the origin.
        cityd (str): The city of the destination.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_direction_transit(origin=origin, destination=destination, city=city, cityd=cityd)


def amap_direction_driving(origin: str, destination: str) -> dict:
    """
    Get the driving route from origin to destination.

    Args:
        origin (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521".
        destination (str): The langitude and latitude of the destination, separated by a comma. e.g. "120.123700,30.266501".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    url = 'https://restapi.amap.com/v3/direction/driving?parameters'
    key = os.getenv('AMAP_KEY')
    params = {'key': key, 'origin': origin, 'destination': destination, 'output': 'json'}
    response = requests.get(url, params=params).json()
    if response['status'] != '1':
        return {'success': False, 'detail': response['info']}
    else:
        result = {'success': True, 'steps': []}
        for step in response['route']['paths'][0]['steps']:
            result['steps'].append(step['instruction'])
        return result


@tool(parse_docstring=True)
def langgraph_amap_direction_driving(origin: str, destination: str) -> dict:
    """
    Get the driving route from origin to destination.

    Args:
        origin (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521".
        destination (str): The langitude and latitude of the destination, separated by a comma. e.g. "120.123700,30.266501".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_direction_driving(origin=origin, destination=destination)


@mcp.tool()
def mcp_amap_direction_driving(origin: str, destination: str) -> dict:
    """
    Get the driving route from origin to destination.

    Args:
        origin (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521".
        destination (str): The langitude and latitude of the destination, separated by a comma. e.g. "120.123700,30.266501".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_direction_driving(origin=origin, destination=destination)


def amap_direction_bicycling(origin: str, destination: str) -> dict:
    """
    Get the driving route from origin to destination.

    Args:
        origin (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521".
        destination (str): The langitude and latitude of the destination, separated by a comma. e.g. "120.123700,30.266501".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    url = 'https://restapi.amap.com/v4/direction/bicycling?parameters'
    key = os.getenv('AMAP_KEY')
    params = {'key': key, 'origin': origin, 'destination': destination, 'output': 'json'}
    response = requests.get(url, params=params).json()
    print(response)
    if response:
        result = {'success': True, 'steps': []}
        for step in response['data']['paths'][0]['steps']:
            result['steps'].append(step['instruction'])
        return result
    else:
        return {'success': False, 'detail': response['info']}


@tool(parse_docstring=True)
def langgraph_amap_direction_bicycling(origin: str, destination: str) -> dict:
    """
    Get the driving route from origin to destination.

    Args:
        origin (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521".
        destination (str): The langitude and latitude of the destination, separated by a comma. e.g. "120.123700,30.266501".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_direction_bicycling(origin=origin, destination=destination)


@mcp.tool()
def mcp_amap_direction_bicycling(origin: str, destination: str) -> dict:
    """
    Get the driving route from origin to destination.

    Args:
        origin (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521".
        destination (str): The langitude and latitude of the destination, separated by a comma. e.g. "120.123700,30.266501".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_direction_bicycling(origin=origin, destination=destination)


def amap_get_distance(origin: str, destination: str) -> dict:
    """
    Get the distance between two points.

    Args:
        origin (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521
        destination (str): The langitude and latitude of the destination, separated by a comma. e.g. "120.123700,30.266501".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    url = 'https://restapi.amap.com/v3/distance?parameters'
    key = os.getenv('AMAP_KEY')
    params = {'key': key, 'origins': origin, 'destination': destination, 'type': 0, 'output': 'json'}
    response = requests.get(url, params=params).json()
    if response['status'] != '1':
        return {'success': False, 'detail': response['info']}
    else:
        result = {'success': True, 'distance': response['results'][0]['distance']}
        return result


@tool(parse_docstring=True)
def langgraph_amap_get_distance(origin: str, destination: str) -> dict:
    """
    Get the distance between two points.

    Args:
        origin (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521
        destination (str): The langitude and latitude of the destination, separated by a comma. e.g. "120.123700,30.266501".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_get_distance(origin=origin, destination=destination)


@mcp.tool()
def mcp_amap_get_distance(origin: str, destination: str) -> dict:
    """
    Get the distance between two points.

    Args:
        origin (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521
        destination (str): The langitude and latitude of the destination, separated by a comma. e.g. "120.123700,30.266501".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_get_distance(origin=origin, destination=destination)


def amap_ip_location(ip: str) -> dict:
    """
    Get the location of an IP address.

    Args:
        ip (str): The IP address to get the location of.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    url = 'https://restapi.amap.com/v3/ip?parameters'
    key = os.getenv('AMAP_KEY')
    params = {'key': key, 'ip': ip, 'output': 'json'}
    response = requests.get(url, params=params).json()
    if response['status'] != '1':
        return {'success': False, 'detail': response['info']}
    else:
        result = {'success': True, 'province': response['province'], 'city': response['city'], 'address_code': response['adcode']}
        return result


@tool(parse_docstring=True)
def langgraph_amap_ip_location(ip: str) -> dict:
    """
    Get the location of an IP address.

    Args:
        ip (str): The IP address to get the location of.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_ip_location(ip=ip)


@mcp.tool()
def mcp_amap_ip_location(ip: str) -> dict:
    """
    Get the location of an IP address.

    Args:
        ip (str): The IP address to get the location of.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_ip_location(ip=ip)


def amap_transform_location(location: str, coordtype: str) -> dict:
    """
    Transform the location from one coordinate system to another.

    Args:
        location (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521".
        coordtype (str): The coordinate system of the location. e.g. "gps", "baidu".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    url = 'https://restapi.amap.com/v3/assistant/coordinate/convert?parameters'
    key = os.getenv('AMAP_KEY')
    params = {'key': key, 'locations': location, 'coordsys': coordtype, 'output': 'json'}
    response = requests.get(url, params=params).json()
    if response['status'] != '1':
        return {'success': False, 'detail': response['info']}
    else:
        result = {'success': True, 'location': response['locations']}
        return result


@tool(parse_docstring=True)
def langgraph_amap_transform_location(location: str, coordtype: str) -> dict:
    """
    Transform the location from one coordinate system to another.

    Args:
        location (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521".
        coordtype (str): The coordinate system of the location. e.g. "gps", "baidu".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_transform_location(location=location, coordtype=coordtype)


@mcp.tool()
def mcp_amap_transform_location(location: str, coordtype: str) -> dict:
    """
    Transform the location from one coordinate system to another.

    Args:
        location (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521".
        coordtype (str): The coordinate system of the location. e.g. "gps", "baidu".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_transform_location(location=location, coordtype=coordtype)


def amap_search_detail(keywords: str) -> dict:
    """
    Get the detail information of a place.

    Args:
        keywords (str): The keywords to search for.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    url = 'https://restapi.amap.com/v5/place/text?parameters'
    key = os.getenv('AMAP_KEY')
    params = {'key': key, 'keywords': keywords, 'output': 'json'}
    response = requests.get(url, params=params).json()
    if response['status'] != '1':
        return {'success': False, 'detail': response['info']}
    else:
        result = {'success': True, 'address': response['pois'][0]['address'], 'name': response['pois'][0]['name'], 'province': response['pois'][0]['pname'], 'city': response['pois'][0]['cityname'], 'district': response['pois'][0]['adname'], 'location': response['pois'][0]['location']}
        return result


@tool(parse_docstring=True)
def langgraph_amap_search_detail(keywords: str) -> dict:
    """
    Get the detail information of a place.

    Args:
        keywords (str): The keywords to search for.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_search_detail(keywords=keywords)


@mcp.tool()
def mcp_amap_search_detail(keywords: str) -> dict:
    """
    Get the detail information of a place.

    Args:
        keywords (str): The keywords to search for.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_search_detail(keywords=keywords)


def amap_around_search(location: str, keywords: str) -> dict:
    """
    Get the surrounding places of a location.

    Args:
        location (str): The langitude and latitude of the location, separated by a comma. e.g. "120.123612,30.266521".
        keywords (str): The keywords to search for.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    url = 'https://restapi.amap.com/v5/place/around?parameters'
    key = os.getenv('AMAP_KEY')
    params = {'key': key, 'location': location, 'keywords': keywords, 'output': 'json'}
    response = requests.get(url, params=params).json()
    if response['status'] != '1':
        return {'success': False, 'detail': response['info']}
    else:
        result = {'success': True, 'results': []}
        for poi in response['pois']:
            result['results'].append({'name': poi['name'], 'address': poi['address'], 'location': poi['location']})
        return result


@tool(parse_docstring=True)
def langgraph_amap_around_search(location: str, keywords: str) -> dict:
    """
    Get the surrounding places of a location.

    Args:
        location (str): The langitude and latitude of the location, separated by a comma. e.g. "120.123612,30.266521".
        keywords (str): The keywords to search for.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_around_search(location=location, keywords=keywords)


@mcp.tool()
def mcp_amap_around_search(location: str, keywords: str) -> dict:
    """
    Get the surrounding places of a location.

    Args:
        location (str): The langitude and latitude of the location, separated by a comma. e.g. "120.123612,30.266521".
        keywords (str): The keywords to search for.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_around_search(location=location, keywords=keywords)


def amap_get_weather(address_code: str) -> dict:
    """
    Get the weather of a location.

    Args:
        address_code (str): The address code of the location.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    url = 'https://restapi.amap.com/v3/weather/weatherInfo?parameters'
    key = os.getenv('AMAP_KEY')
    params = {'key': key, 'city': address_code, 'extensions': 'base', 'output': 'json'}
    response = requests.get(url, params=params).json()
    if response['status'] != '1':
        return {'success': False, 'detail': response['info']}
    else:
        result = {'success': True, 'weather': response['lives'][0]['weather'], 'temperature': response['lives'][0]['temperature'], 'wind_direction': response['lives'][0]['winddirection'], 'wind_power': response['lives'][0]['windpower'], 'humidity': response['lives'][0]['humidity'], 'report_time': response['lives'][0]['reporttime']}
        return result


@tool(parse_docstring=True)
def langgraph_amap_get_weather(address_code: str) -> dict:
    """
    Get the weather of a location.

    Args:
        address_code (str): The address code of the location.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_get_weather(address_code=address_code)


@mcp.tool()
def mcp_amap_get_weather(address_code: str) -> dict:
    """
    Get the weather of a location.

    Args:
        address_code (str): The address code of the location.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_get_weather(address_code=address_code)


def amap_get_weather_forecast(address_code: str) -> dict:
    """
    Get the weather forecast of a location.

    Args:
        address_code (str): The address code of the location.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    url = 'https://restapi.amap.com/v3/weather/weatherInfo?parameters'
    key = os.getenv('AMAP_KEY')
    params = {'key': key, 'city': address_code, 'extensions': 'all', 'output': 'json'}
    response = requests.get(url, params=params).json()
    if response['status'] != '1':
        return {'success': False, 'detail': response['info']}
    else:
        result = {'success': True, 'forecasts': []}
        for forecast in response['forecasts'][0]['casts']:
            result['forecasts'].append({'date': forecast['date'], 'day_weather': forecast['dayweather'], 'night_weather': forecast['nightweather'], 'day_temperature': forecast['daytemp'], 'night_temperature': forecast['nighttemp'], 'day_wind_direction': forecast['daywind'], 'night_wind_direction': forecast['nightwind'], 'day_wind_power': forecast['daypower'], 'night_wind_power': forecast['nightpower']})
        return result


@tool(parse_docstring=True)
def langgraph_amap_get_weather_forecast(address_code: str) -> dict:
    """
    Get the weather forecast of a location.

    Args:
        address_code (str): The address code of the location.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_get_weather_forecast(address_code=address_code)


@mcp.tool()
def mcp_amap_get_weather_forecast(address_code: str) -> dict:
    """
    Get the weather forecast of a location.

    Args:
        address_code (str): The address code of the location.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_get_weather_forecast(address_code=address_code)


