import os
import json
import shutil
import secrets
import string
from typing import Any, Dict, List

DATA_PATH = 'environment/reports/IdentitySafe.json'
INIT_PATH = 'environment/initial/IdentitySafe_init.json'

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


def StorePassword(password: str, website: str, username: str) -> Dict[str, Any]:
    """Store a password entry for a specific website and username.
    
    Args:
        password (str): The password to store.
        website (str): The website URL or name associated with the password.
        username (str): The username associated with the password.
    """
    if not password or not website or not username:
        raise InvalidRequestException("The 'password', 'website', or 'username' parameter is not provided or invalid.")
    data = _load_data()
    entry = {'website': website, 'username': username, 'password': password}
    data.setdefault('passwords', [])
    # avoid duplicates for same website+username
    for e in data['passwords']:
        if e.get('website') == website and e.get('username') == username:
            e['password'] = password
            _save_data(data)
            return {'success': True}
    data['passwords'].append(entry)
    _save_data(data)
    return {'success': True}


def CheckPasswordStrength(password: str) -> Dict[str, Any]:
    """Check the strength of a password based on length and character variety.
    
    Args:
        password (str): The password to check for strength.
    """
    if not password:
        raise InvalidRequestException("The 'password' parameter is not provided or invalid.")
    length = len(password)
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(c in string.punctuation for c in password)
    score = sum([has_lower, has_upper, has_digit, has_symbol])
    if length >= 12 and score >= 3:
        strength = 'strong'
    elif length >= 8 and score >= 2:
        strength = 'medium'
    else:
        strength = 'weak'
    return {'strength': strength}


def GeneratePassword(length: int = 12, include_symbols: bool = True, include_numbers: bool = True,
                     include_uppercase: bool = True, include_lowercase: bool = True,
                     strength: str = 'strong') -> Dict[str, Any]:
    """Generate a random password with specified character types and strength level.
    
    Args:
        length (int): The desired length of the generated password.
        include_symbols (bool): Whether to include special symbols in the password.
        include_numbers (bool): Whether to include numeric digits in the password.
        include_uppercase (bool): Whether to include uppercase letters in the password.
        include_lowercase (bool): Whether to include lowercase letters in the password.
        strength (str): The password strength level, must be 'weak', 'medium', or 'strong'.
    """
    if strength not in ['weak', 'medium', 'strong']:
        if strength is None:
            strength = 'strong'
        else:
            raise InvalidRequestException("The 'strength' parameter is not one of ['weak', 'medium', 'strong'].")
    # adjust defaults per strength
    if strength == 'weak':
        length = max(6, length)
    elif strength == 'medium':
        length = max(10, length)
    else:
        length = max(12, length)

    charset = ''
    if include_lowercase:
        charset += string.ascii_lowercase
    if include_uppercase:
        charset += string.ascii_uppercase
    if include_numbers:
        charset += string.digits
    if include_symbols:
        charset += string.punctuation
    if not charset:
        raise InvalidRequestException('No character sets selected to generate password.')

    # ensure at least one character from each selected set
    pw_chars = []
    if include_lowercase:
        pw_chars.append(secrets.choice(string.ascii_lowercase))
    if include_uppercase:
        pw_chars.append(secrets.choice(string.ascii_uppercase))
    if include_numbers:
        pw_chars.append(secrets.choice(string.digits))
    if include_symbols:
        pw_chars.append(secrets.choice(string.punctuation))

    while len(pw_chars) < length:
        pw_chars.append(secrets.choice(charset))
    secrets.SystemRandom().shuffle(pw_chars)
    generated = ''.join(pw_chars[:length])
    return {'generated_password': generated}


def AutoFillPassword(website: str) -> Dict[str, Any]:
    """Auto-fill password for a specified website.
    
    Args:
        website (str): The website URL or name to retrieve password for.
    """
    if not website:
        raise InvalidRequestException("The 'website' parameter is not provided or invalid.")
    data = _load_data()
    for e in data.get('passwords', []):
        if e.get('website') == website:
            return {'success': True}
    raise NotFoundException('The password for the specified website is not found.')


def SearchPasswords(query: str, max_results: int = 10) -> Dict[str, Any]:
    """Search for stored passwords by website or username.
    
    Args:
        query (str): The search query to match against website or username.
        max_results (int): The maximum number of results to return.
    """
    if query is None:
        raise InvalidRequestException("The 'query' parameter is not provided or invalid.")
    if max_results is None:
        max_results = 10
    data = _load_data()
    results = []
    for e in data.get('passwords', []):
        if query.lower() in e.get('website', '').lower() or query.lower() in e.get('username', '').lower():
            results.append({'website': e.get('website'), 'username': e.get('username'), 'password': e.get('password')})
            if len(results) >= max_results:
                break
    return {'passwords': results}


def StorePersonalInfo(info_type: str, info_data: Dict[str, Any]) -> Dict[str, Any]:
    """Store personal information of a specific type.
    
    Args:
        info_type (str): The type of personal information, must be 'address' or 'payment'.
        info_data (Dict[str, Any]): The personal information data to store.
    """
    if isinstance(info_data, str):
        try:
            info_data = json.loads(info_data)
        except json.JSONDecodeError:
            raise InvalidRequestException("The 'info_data' parameter is not provided or invalid.")
    if info_type not in ['address', 'payment'] or not isinstance(info_data, dict):
        raise InvalidRequestException("The 'info_type' parameter is not one of ['address', 'payment'] or the 'info_data' parameter is not provided or invalid.")
    if info_type == 'address':
        if 'zip' in info_data and 'zip_code' not in info_data:
            info_data['zip_code'] = info_data.pop('zip')
        required = ['street', 'city', 'state', 'zip_code']
    else:
        if 'expiry' in info_data and 'expiry_date' not in info_data:
            info_data['expiry_date'] = info_data.pop('expiry')
        required = []
    for k in required:
        if k not in info_data:
            raise InvalidRequestException(f'Missing field in info_data: {k}')
    data = _load_data()
    data.setdefault('personal_info', {})
    data['personal_info'][info_type] = info_data
    _save_data(data)
    return {'success': True}


def AutoFillPersonalInfo(website: str, info_type: str) -> Dict[str, Any]:
    """Auto-fill personal information for a specified website.
    
    Args:
        website (str): The website URL or name to fill information for.
        info_type (str): The type of personal information, must be 'address' or 'payment'.
    """
    if not website or info_type not in ['address', 'payment']:
        raise InvalidRequestException("The 'website' or 'info_type' parameter is not provided or invalid.")
    data = _load_data()
    info = data.get('personal_info', {}).get(info_type)
    if not info:
        raise NotFoundException('The personal information for the specified info_type is not found.')
    return {'success': True}


def RetrievePersonalInfo(info_type: str) -> Dict[str, Any]:
    """Retrieve stored personal information of a specific type.
    
    Args:
        info_type (str): The type of personal information to retrieve, must be 'address' or 'payment'.
    """
    if not info_type or info_type not in ['address', 'payment']:
        raise InvalidRequestException("The 'info_type' parameter is not provided or invalid.")
    data = _load_data()
    info = data.get('personal_info', {}).get(info_type)
    if not info:
        raise NotFoundException('The personal information for the specified info_type is not found.')
    return {'info_data': info}


def SharePassword(website: str, username: str, contact_email: str) -> Dict[str, Any]:
    """Share a password entry with another contact.
    
    Args:
        website (str): The website URL or name associated with the password.
        username (str): The username associated with the password.
        contact_email (str): The email address of the contact to share with.
    """
    if not website or not username or not contact_email:
        raise InvalidRequestException("The 'website', 'username', or 'contact_email' parameter is not provided or invalid.")
    data = _load_data()
    for e in data.get('passwords', []):
        if e.get('website') == website and e.get('username') == username:
            data.setdefault('shared', [])
            data['shared'].append({'website': website, 'username': username, 'shared_with': contact_email})
            _save_data(data)
            return {'success': True}
    raise NotFoundException('The password for the specified website and username is not found.')


def ImportPasswords(file_path: str) -> Dict[str, Any]:
    """Import passwords from a JSON file.
    
    Args:
        file_path (str): The path to the JSON file containing password entries.
    """
    if not file_path or not os.path.exists(file_path):
        raise InvalidRequestException("The 'file_path' parameter is not provided or invalid.")
    with open(file_path, 'r', encoding='utf-8') as f:
        imported = json.load(f)
    if not isinstance(imported, list):
        raise InvalidRequestException('Imported file must contain a list of password objects.')
    data = _load_data()
    data.setdefault('passwords', [])
    for e in imported:
        if 'website' in e and 'username' in e and 'password' in e:
            data['passwords'].append({'website': e['website'], 'username': e['username'], 'password': e['password']})
    _save_data(data)
    return {'success': True}


def ExportPasswords(file_path: str) -> Dict[str, Any]:
    """Export all stored passwords to a JSON file.
    
    Args:
        file_path (str): The path to save the exported password entries.
    """
    if not file_path:
        raise InvalidRequestException("The 'file_path' parameter is not provided or invalid.")
    data = _load_data()
    to_export = data.get('passwords', [])
    dir_path = os.path.dirname(file_path)
    try:
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(to_export, f, indent=2)
    except PermissionError:
        fallback_dir = os.path.dirname(DATA_PATH)
        if fallback_dir:
            os.makedirs(fallback_dir, exist_ok=True)
        fallback_path = os.path.join(fallback_dir, os.path.basename(file_path))
        with open(fallback_path, 'w', encoding='utf-8') as f:
            json.dump(to_export, f, indent=2)
    return {'success': True}


def EnableTwoFactorAuthentication(phone_number: str) -> Dict[str, Any]:
    """Enable two-factor authentication with a phone number.
    
    Args:
        phone_number (str): The phone number to use for two-factor authentication.
    """
    if not phone_number:
        raise InvalidRequestException("The 'phone_number' parameter is not provided or invalid.")
    data = _load_data()
    data.setdefault('two_factor', {})
    data['two_factor']['enabled'] = True
    data['two_factor']['phone_number'] = phone_number
    _save_data(data)
    return {'success': True}


def DisableTwoFactorAuthentication() -> Dict[str, Any]:
    """Disable two-factor authentication."""
    data = _load_data()
    data.setdefault('two_factor', {})
    data['two_factor']['enabled'] = False
    data['two_factor']['phone_number'] = ''
    _save_data(data)
    return {'success': True}
