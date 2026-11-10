import json
import os
import shutil
import uuid
from datetime import datetime

DATA_PATH = os.path.join('environment', 'reports', 'storage.json')
INIT_PATH = os.path.join('environment', 'initial', 'storage_init.json')

INIT = False


class InvalidRequestException(Exception):
    """Exception raised for invalid request parameters."""
    pass


class NotFoundException(Exception):
    """Exception raised when requested resource is not found."""
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


def _read_env():
    """Read the current environment data."""
    _ensure_work_env()
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _write_env(data):
    """Write data to the environment file."""
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _find_item_by_id(items, item_id):
    """Find an item by its ID."""
    for item in items:
        if item.get('item_id') == item_id:
            return item
    return None


def _find_alert_by_id(alerts, alert_id):
    """Find an alert by its ID."""
    for alert in alerts:
        if alert.get('alert_id') == alert_id:
            return alert
    return None


def AddItem(item_name: str, category: str, quantity: int, supplier: str | None = None, description: str | None = None) -> dict:
    """
    Add a new item to the inventory.

    Args:
        item_name (str): The name of the item, must be a non-empty string.
        category (str): The category of the item, must be a non-empty string.
        quantity (int): The quantity of the item, must be a positive integer.
        supplier (str, optional): The supplier of the item, must be a non-empty string if provided.
        description (str, optional): The description of the item, must be a non-empty string if provided.

    Returns:
        dict: A dictionary containing the unique identifier of the added item.
            {
                "item_id": str
            }

    Raises:
        InvalidRequestException: If 'item_name', 'category', or 'quantity' parameter is invalid.
    """
    if not item_name or not isinstance(item_name, str) or not item_name.strip():
        raise InvalidRequestException("'item_name' must be a non-empty string")
    if not category or not isinstance(category, str) or not category.strip():
        raise InvalidRequestException("'category' must be a non-empty string")
    if not isinstance(quantity, int) or quantity <= 0:
        raise InvalidRequestException("'quantity' must be a positive integer")
    if supplier is not None and (not isinstance(supplier, str) or not supplier.strip()):
        raise InvalidRequestException("'supplier' must be a non-empty string if provided")
    if description is not None and (not isinstance(description, str) or not description.strip()):
        raise InvalidRequestException("'description' must be a non-empty string if provided")

    env = _read_env()
    items = env.setdefault('items', [])
    
    item_id = uuid.uuid4().hex
    item = {
        'item_id': item_id,
        'item_name': item_name,
        'category': category,
        'quantity': quantity,
        'supplier': supplier or '',
        'description': description or '',
        'created_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }
    items.append(item)
    _write_env(env)
    return {'item_id': item_id}


def UpdateItem(item_id: str, item_name: str | None = None, category: str | None = None, quantity: int | None = None, supplier: str | None = None, description: str | None = None) -> dict:
    """
    Update an existing item in the inventory.

    Args:
        item_id (str): The unique identifier of the item, must be a non-empty string.
        item_name (str, optional): The new name of the item, must be a non-empty string if provided.
        category (str, optional): The new category of the item, must be a non-empty string if provided.
        quantity (int, optional): The new quantity of the item, must be a positive integer if provided.
        supplier (str, optional): The new supplier of the item, must be a non-empty string if provided.
        description (str, optional): The new description of the item, must be a non-empty string if provided.

    Returns:
        dict: A dictionary indicating whether the item update was successful.
            {
                "success": bool
            }

    Raises:
        InvalidRequestException: If 'item_id' parameter is invalid.
        NotFoundException: If 'item_id' does not exist.
    """
    if item_id is None:
        raise InvalidRequestException("'item_id' must be a non-empty string")
    if not isinstance(item_id, str) or not item_id.strip():
        raise InvalidRequestException("'item_id' must be a non-empty string")

    env = _read_env()
    items = env.get('items', [])
    item = _find_item_by_id(items, item_id)
    
    if not item:
        raise NotFoundException(f"Item with id '{item_id}' does not exist")

    if item_name is not None:
        if not isinstance(item_name, str) or not item_name.strip():
            raise InvalidRequestException("'item_name' must be a non-empty string if provided")
        item['item_name'] = item_name
    
    if category is not None:
        if not isinstance(category, str) or not category.strip():
            raise InvalidRequestException("'category' must be a non-empty string if provided")
        item['category'] = category
    
    if quantity is not None:
        if isinstance(quantity, str):
            try:
                quantity = int(quantity)
            except (ValueError, TypeError):
                raise InvalidRequestException("'quantity' must be a positive integer if provided")
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
            raise InvalidRequestException("'quantity' must be a positive integer if provided")
        item['quantity'] = quantity
    
    if supplier is not None:
        if not isinstance(supplier, str) or not supplier.strip():
            raise InvalidRequestException("'supplier' must be a non-empty string if provided")
        item['supplier'] = supplier
    
    if description is not None:
        if not isinstance(description, str) or not description.strip():
            raise InvalidRequestException("'description' must be a non-empty string if provided")
        item['description'] = description

    _write_env(env)
    return {'success': True}


def DeleteItem(item_id: str) -> dict:
    """
    Delete an item from the inventory.

    Args:
        item_id (str): The unique identifier of the item, must be a non-empty string.

    Returns:
        dict: A dictionary indicating whether the item deletion was successful.
            {
                "success": bool
            }

    Raises:
        InvalidRequestException: If 'item_id' parameter is invalid.
        NotFoundException: If 'item_id' does not exist.
    """
    if not item_id or not isinstance(item_id, str) or not item_id.strip():
        raise InvalidRequestException("'item_id' must be a non-empty string")

    env = _read_env()
    items = env.get('items', [])
    item = _find_item_by_id(items, item_id)
    
    if not item:
        raise NotFoundException(f"Item with id '{item_id}' does not exist")

    items.remove(item)
    _write_env(env)
    return {'success': True}


def SearchItems(keyword: str | None = None, category: str | None = None, page: int = 1, results_per_page: int = 10) -> dict:
    """
    Search for items in the inventory by keyword or category.

    Args:
        keyword (str, optional): The keyword to search for in the item name, must be a non-empty string if provided.
        category (str, optional): The category to search for, must be a non-empty string if provided.
        page (int, optional): The page number to retrieve, must be a positive integer if provided. Default is 1.
        results_per_page (int, optional): The maximum number of results per page, must be a positive integer if provided. Default is 10.

    Returns:
        dict: A dictionary containing a list of matching items.
            {
                "items": [
                    {
                        "item_id": str,
                        "item_name": str,
                        "category": str,
                        "quantity": int
                    }
                ]
            }

    Raises:
        InvalidRequestException: If 'page' or 'results_per_page' parameter is not a positive integer.
        NotFoundException: If no items are found.
    """
    if page is None:
        page = 1
    if isinstance(page, bool):
        raise InvalidRequestException("'page' must be a positive integer")
    if not isinstance(page, int):
        try:
            page = int(page)
        except (ValueError, TypeError):
            raise InvalidRequestException("'page' must be a positive integer")
    if page <= 0:
        raise InvalidRequestException("'page' must be a positive integer")
    if results_per_page is None:
        results_per_page = 10
    if isinstance(results_per_page, bool):
        raise InvalidRequestException("'results_per_page' must be a positive integer")
    if not isinstance(results_per_page, int):
        try:
            results_per_page = int(results_per_page)
        except (ValueError, TypeError):
            raise InvalidRequestException("'results_per_page' must be a positive integer")
    if results_per_page <= 0:
        raise InvalidRequestException("'results_per_page' must be a positive integer")
    if keyword is not None and (not isinstance(keyword, str) or not keyword.strip()):
        raise InvalidRequestException("'keyword' must be a non-empty string if provided")
    if category is not None and (not isinstance(category, str) or not category.strip()):
        raise InvalidRequestException("'category' must be a non-empty string if provided")

    env = _read_env()
    items = env.get('items', [])
    
    filtered_items = []
    for item in items:
        match = True
        if keyword and keyword.lower() not in item['item_name'].lower():
            match = False
        if category and category.lower() != item['category'].lower():
            match = False
        if match:
            filtered_items.append({
                'item_id': item['item_id'],
                'item_name': item['item_name'],
                'category': item['category'],
                'quantity': item['quantity']
            })
    
    if not filtered_items:
        raise NotFoundException("No items are found")
    
    start_idx = (page - 1) * results_per_page
    end_idx = start_idx + results_per_page
    paginated_items = filtered_items[start_idx:end_idx]
    
    return {'items': paginated_items}


def GetItemDetails(item_id: str) -> dict:
    """
    Get detailed information about an item in the inventory.

    Args:
        item_id (str): The unique identifier of the item, must be a non-empty string.

    Returns:
        dict: A dictionary containing detailed information about the item.
            {
                "item_name": str,
                "category": str,
                "quantity": int,
                "supplier": str,
                "description": str
            }

    Raises:
        InvalidRequestException: If 'item_id' parameter is invalid.
        NotFoundException: If 'item_id' does not exist.
    """
    if not item_id or not isinstance(item_id, str) or not item_id.strip():
        raise InvalidRequestException("'item_id' must be a non-empty string")

    env = _read_env()
    items = env.get('items', [])
    item = _find_item_by_id(items, item_id)
    
    if not item:
        raise NotFoundException(f"Item with id '{item_id}' does not exist")

    return {
        'item_name': item['item_name'],
        'category': item['category'],
        'quantity': item['quantity'],
        'supplier': item['supplier'],
        'description': item['description']
    }


def TrackInventory(threshold: int) -> dict:
    """
    Track inventory levels and receive notifications when stock levels are low.

    Args:
        threshold (int): The stock level threshold, must be a positive integer.

    Returns:
        dict: A dictionary containing a list of items with stock levels below the threshold.
            {
                "low_stock_items": [
                    {
                        "item_id": str,
                        "item_name": str,
                        "category": str,
                        "quantity": int
                    }
                ]
            }

    Raises:
        InvalidRequestException: If 'threshold' parameter is not a positive integer.
    """
    if not isinstance(threshold, int) or threshold <= 0:
        raise InvalidRequestException("'threshold' must be a positive integer")

    env = _read_env()
    items = env.get('items', [])
    
    low_stock_items = []
    for item in items:
        if item['quantity'] < threshold:
            low_stock_items.append({
                'item_id': item['item_id'],
                'item_name': item['item_name'],
                'category': item['category'],
                'quantity': item['quantity']
            })
    
    return {'low_stock_items': low_stock_items}


def SetupAlert(threshold: int, operation: str, alert_id: str | None = None, item_id: str | None = None, category: str | None = None) -> dict:
    """
    Set up an alert for a specific item or category when the stock reaches a certain threshold.

    Args:
        threshold (int): The stock level threshold, must be a positive integer.
        operation (str): The operation to perform on the alert, must be one of ['add', 'update', 'delete'].
        alert_id (str, optional): The unique identifier of the alert, must be a non-empty string if provided.
        item_id (str, optional): The unique identifier of the item, must be a non-empty string if provided.
        category (str, optional): The category of the item, must be a non-empty string if provided.

    Returns:
        dict: A dictionary indicating whether the alert setup was successful and the alert_id.
            {
                "success": bool,
                "alert_id": str
            }

    Raises:
        InvalidRequestException: If 'operation' parameter is not one of the allowed values or 'threshold' parameter is not a positive integer.
        NotFoundException: If 'alert_id' does not exist (for update and delete operations).
    """
    if not isinstance(threshold, int) or threshold <= 0:
        raise InvalidRequestException("'threshold' must be a positive integer")
    if operation not in ['add', 'update', 'delete']:
        raise InvalidRequestException("'operation' must be one of ['add', 'update', 'delete']")

    env = _read_env()
    alerts = env.setdefault('alerts', [])

    if operation == 'add':
        if item_id is not None and (not isinstance(item_id, str) or not item_id.strip()):
            raise InvalidRequestException("'item_id' must be a non-empty string if provided")
        if category is not None and (not isinstance(category, str) or not category.strip()):
            raise InvalidRequestException("'category' must be a non-empty string if provided")
        
        new_alert_id = uuid.uuid4().hex
        alert = {
            'alert_id': new_alert_id,
            'item_id': item_id or '',
            'category': category or '',
            'threshold': threshold,
            'created_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }
        alerts.append(alert)
        _write_env(env)
        return {'success': True, 'alert_id': new_alert_id}

    elif operation == 'update':
        if not alert_id or not isinstance(alert_id, str) or not alert_id.strip():
            raise InvalidRequestException("'alert_id' must be provided for update operation")
        
        alert = _find_alert_by_id(alerts, alert_id)
        if not alert:
            raise NotFoundException(f"Alert with id '{alert_id}' does not exist")
        
        if item_id is not None:
            if not isinstance(item_id, str) or not item_id.strip():
                raise InvalidRequestException("'item_id' must be a non-empty string if provided")
            alert['item_id'] = item_id
        if category is not None:
            if not isinstance(category, str) or not category.strip():
                raise InvalidRequestException("'category' must be a non-empty string if provided")
            alert['category'] = category
        alert['threshold'] = threshold
        
        _write_env(env)
        return {'success': True, 'alert_id': alert_id}

    elif operation == 'delete':
        if not alert_id or not isinstance(alert_id, str) or not alert_id.strip():
            raise InvalidRequestException("'alert_id' must be provided for delete operation")
        
        alert = _find_alert_by_id(alerts, alert_id)
        if not alert:
            raise NotFoundException(f"Alert with id '{alert_id}' does not exist")
        
        alerts.remove(alert)
        _write_env(env)
        return {'success': True, 'alert_id': alert_id}


def SearchSuppliers(keyword: str | None = None, page: int = 1, results_per_page: int = 10) -> dict:
    """
    Search for suppliers by keyword.

    Args:
        keyword (str, optional): The keyword to search for in the supplier name, must be a non-empty string if provided.
        page (int, optional): The page number to retrieve, must be a positive integer if provided. Default is 1.
        results_per_page (int, optional): The maximum number of results per page, must be a positive integer if provided. Default is 10.

    Returns:
        dict: A dictionary containing a list of matching suppliers.
            {
                "suppliers": [
                    {
                        "supplier_id": str,
                        "supplier_name": str,
                        "item_count": int
                    }
                ]
            }

    Raises:
        InvalidRequestException: If 'page' or 'results_per_page' parameter is not a positive integer.
        NotFoundException: If no suppliers are found.
    """
    if page is None:
        page = 1
    if isinstance(page, bool):
        raise InvalidRequestException("'page' must be a positive integer")
    if not isinstance(page, int):
        try:
            page = int(page)
        except (ValueError, TypeError):
            raise InvalidRequestException("'page' must be a positive integer")
    if page <= 0:
        raise InvalidRequestException("'page' must be a positive integer")
    if results_per_page is None:
        results_per_page = 10
    if isinstance(results_per_page, bool):
        raise InvalidRequestException("'results_per_page' must be a positive integer")
    if not isinstance(results_per_page, int):
        try:
            results_per_page = int(results_per_page)
        except (ValueError, TypeError):
            raise InvalidRequestException("'results_per_page' must be a positive integer")
    if results_per_page <= 0:
        raise InvalidRequestException("'results_per_page' must be a positive integer")
    if keyword is not None and (not isinstance(keyword, str) or not keyword.strip()):
        raise InvalidRequestException("'keyword' must be a non-empty string if provided")

    env = _read_env()
    items = env.get('items', [])
    
    # Build supplier statistics
    supplier_stats = {}
    for item in items:
        supplier = item.get('supplier', '')
        if supplier:
            if supplier not in supplier_stats:
                supplier_stats[supplier] = {'count': 0, 'categories': set()}
            supplier_stats[supplier]['count'] += 1
            supplier_stats[supplier]['categories'].add(item.get('category', ''))
    
    # Filter by keyword
    filtered_suppliers = []
    for supplier_name, stats in supplier_stats.items():
        if keyword is None or keyword.lower() in supplier_name.lower() or any(keyword.lower() in cat.lower() for cat in stats['categories']):
            filtered_suppliers.append({
                'supplier_id': supplier_name.replace(' ', '_').lower(),
                'supplier_name': supplier_name,
                'item_count': stats['count']
            })
    
    if not filtered_suppliers:
        raise NotFoundException("No suppliers are found")
    
    # Sort by name for consistency
    filtered_suppliers.sort(key=lambda x: x['supplier_name'])
    
    start_idx = (page - 1) * results_per_page
    end_idx = start_idx + results_per_page
    paginated_suppliers = filtered_suppliers[start_idx:end_idx]
    
    return {'suppliers': paginated_suppliers}


def ListCategories(page: int = 1, results_per_page: int = 10) -> dict:
    """
    List available categories in the inventory.

    Args:
        page (int, optional): The page number to retrieve, must be a positive integer if provided. Default is 1.
        results_per_page (int, optional): The maximum number of results per page, must be a positive integer if provided. Default is 10.

    Returns:
        dict: A dictionary containing a list of available categories.
            {
                "categories": [
                    {
                        "category_id": str,
                        "category_name": str,
                        "item_count": int
                    }
                ]
            }

    Raises:
        InvalidRequestException: If 'page' or 'results_per_page' parameter is not a positive integer.
        NotFoundException: If no categories are found.
    """
    if page is None:
        page = 1
    if isinstance(page, bool):
        raise InvalidRequestException("'page' must be a positive integer")
    if not isinstance(page, int):
        try:
            page = int(page)
        except (ValueError, TypeError):
            raise InvalidRequestException("'page' must be a positive integer")
    if page <= 0:
        raise InvalidRequestException("'page' must be a positive integer")
    if results_per_page is None:
        results_per_page = 10
    if isinstance(results_per_page, bool):
        raise InvalidRequestException("'results_per_page' must be a positive integer")
    if not isinstance(results_per_page, int):
        try:
            results_per_page = int(results_per_page)
        except (ValueError, TypeError):
            raise InvalidRequestException("'results_per_page' must be a positive integer")
    if results_per_page <= 0:
        raise InvalidRequestException("'results_per_page' must be a positive integer")

    env = _read_env()
    items = env.get('items', [])
    
    # Build category statistics
    category_stats = {}
    for item in items:
        category = item.get('category', '')
        if category:
            if category not in category_stats:
                category_stats[category] = 0
            category_stats[category] += 1
    
    if not category_stats:
        raise NotFoundException("No categories are found")
    
    categories = []
    for category_name, count in category_stats.items():
        categories.append({
            'category_id': category_name.replace(' ', '_').lower(),
            'category_name': category_name,
            'item_count': count
        })
    
    # Sort by name for consistency
    categories.sort(key=lambda x: x['category_name'])
    
    start_idx = (page - 1) * results_per_page
    end_idx = start_idx + results_per_page
    paginated_categories = categories[start_idx:end_idx]
    
    return {'categories': paginated_categories}
