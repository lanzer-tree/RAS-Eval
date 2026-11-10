import json
import os
import re
import shutil
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

INIT = False
DATA_PATH = "environment/reports/TakeAway.json"
INIT_PATH = "environment/initial/TakeAway_init.json"


class InvalidRequestException(Exception):
    pass


class NotFoundException(Exception):
    pass


def _ensure_work_env() -> None:
    """Ensure the working environment file exists by copying from init if needed."""
    global INIT
    if not os.path.exists(INIT_PATH):
        raise InvalidRequestException(f"Init file not found: {INIT_PATH}")
    data_dir = os.path.dirname(DATA_PATH)
    if data_dir and not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    if not INIT or not os.path.exists(DATA_PATH):
        shutil.copyfile(INIT_PATH, DATA_PATH)
        INIT = True


def _load_data() -> Dict[str, Any]:
    _ensure_work_env()
    with open(DATA_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def _save_data(data: Dict[str, Any]) -> None:
    with open(DATA_PATH, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def _parse_price_range(price_range: Optional[str]) -> Tuple[float, float]:
    if not price_range:
        return 0.0, float("inf")
    normalized = price_range.replace(" ", "")
    if normalized.endswith("+"):
        return float(normalized[:-1]), float("inf")
    if "-" in normalized:
        low, high = normalized.split("-", 1)
        return float(low), float(high)
    raise InvalidRequestException("price_range must look like '0-30' or '60+'")


def _numeric_fallback(id_str: str, entity_type: str) -> Optional[str]:
    nums = re.findall(r'\d+', id_str)
    if not nums:
        return None
    return entity_type + "_" + nums[-1].zfill(3)


def _find_merchant_by_id(data: Dict[str, Any], merchant_id: str) -> Dict[str, Any]:
    for merchant in data.get("merchants", []):
        if merchant.get("merchant_id", "").lower() == merchant_id.lower():
            return merchant
    fallback = _numeric_fallback(merchant_id, "merchant")
    if fallback:
        for merchant in data.get("merchants", []):
            if merchant.get("merchant_id", "").lower() == fallback.lower():
                return merchant
    raise NotFoundException(f"Merchant {merchant_id} not found.")


def _find_product_by_id(data: Dict[str, Any], product_id: str) -> Dict[str, Any]:
    for product in data.get("products", []):
        if product.get("product_id", "").lower() == product_id.lower():
            return product
    fallback = _numeric_fallback(product_id, "product")
    if fallback:
        for product in data.get("products", []):
            if product.get("product_id", "").lower() == fallback.lower():
                return product
    raise NotFoundException(f"Product {product_id} not found.")


def _find_user_by_id(data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    for user in data.get("users", []):
        if user.get("user_id", "").lower() == user_id.lower():
            return user
    fallback = _numeric_fallback(user_id, "user")
    if fallback:
        for user in data.get("users", []):
            if user.get("user_id", "").lower() == fallback.lower():
                return user
    raise NotFoundException(f"User {user_id} not found.")


def _next_order_id(data: Dict[str, Any]) -> str:
    sequence = data.setdefault("order_sequence", 1000)
    data["order_sequence"] = sequence + 1
    return f"TA-{data['order_sequence']:04d}"


def _calculate_estimated_arrival(distance_km: float, scheduled_delivery: Optional[str]) -> str:
    if scheduled_delivery:
        try:
            datetime.fromisoformat(scheduled_delivery)
        except ValueError:
            raise InvalidRequestException("scheduled_delivery must be in ISO format.")
        return scheduled_delivery
    buffer_minutes = max(15, min(45, int(distance_km * 6)))
    eta = datetime.utcnow() + timedelta(minutes=buffer_minutes)
    return eta.replace(second=0, microsecond=0).isoformat()


def _normalize_flag(token: str) -> str:
    return token.lower().replace("-", "_").strip()


def _apply_filters(merchant: Dict[str, Any], filters: Optional[List[str]]) -> bool:
    if not filters:
        return True
    merchant_flags = {_normalize_flag(flag) for flag in merchant.get("filters", [])}
    requested_flags = {_normalize_flag(flag) for flag in filters}
    return requested_flags <= merchant_flags


def _category_matches(category: Optional[str], merchant: Dict[str, Any]) -> bool:
    if not category:
        return True
    target = category.strip().lower()
    primary = merchant.get("category", "").lower()
    if primary and target == primary:
        return True
    for alias in merchant.get("category_aliases", []) + [merchant.get("category_en", "")]:
        if alias and target == alias.lower():
            return True
    return False


def _validate_address(delivery_address: Dict[str, str]) -> None:
    required = {"name", "phone", "address"}
    if not required <= delivery_address.keys():
        raise InvalidRequestException("delivery_address must include name, phone, and address.")


def search_merchants(
    location: str,
    category: Optional[str] = None,
    price_range: Optional[str] = None,
    rating: Optional[float] = None,
    distance: Optional[float] = None,
    filters: Optional[List[str]] = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    """Return nearby merchants that match a set of filters.
    
    Args:
        location (str): The delivery location or area.
        category (Optional[str]): Food category filter (e.g., 'Chinese', 'Italian').
        price_range (Optional[str]): Price range filter like '0-30' or '60+'.
        rating (Optional[float]): Minimum rating threshold for merchants.
        distance (Optional[float]): Maximum distance in kilometers.
        filters (Optional[List[str]]): List of filter flags to apply.
        page (int): Page number for pagination, defaults to 1.
        page_size (int): Number of results per page, defaults to 10.
    """
    data = _load_data()
    merchants = data.get("merchants", [])
    low_price, high_price = _parse_price_range(price_range)
    results = []
    for merchant in merchants:
        if category and not _category_matches(category, merchant):
            continue
        if rating and merchant.get("rating", 0.0) < rating:
            continue
        if distance and merchant.get("distance", float("inf")) > distance:
            continue
        price_field = merchant.get("average_price", 0.0)
        if not (low_price <= price_field <= high_price):
            continue
        if not _apply_filters(merchant, filters):
            continue
        results.append({
            "merchant_id": merchant.get("merchant_id"),
            "name": merchant.get("name"),
            "category": merchant.get("category"),
            "rating": merchant.get("rating"),
            "delivery_fee": merchant.get("delivery_fee"),
            "distance": merchant.get("distance"),
            "estimated_arrival": merchant.get("estimate"),
            "flags": merchant.get("filters", []),
        })
    results.sort(key=lambda item: item.get("distance", 0.0))
    total = len(results)
    page = page if page is not None else 1
    page_size = page_size if page_size is not None else 10
    page = max(1, page)
    page_size = max(1, min(page_size, 20))
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "location": location,
        "page": page,
        "page_size": page_size,
        "total": total,
        "merchants": results[start:end],
    }


def get_merchant_detail(
    merchant_id: str,
    include_menu: bool = True,
    include_reviews: bool = False,
) -> Dict[str, Any]:
    """Return the merchant detail payload, optionally including menu and reviews.
    
    Args:
        merchant_id (str): Unique identifier of the merchant.
        include_menu (bool): Whether to include the menu items, defaults to True.
        include_reviews (bool): Whether to include customer reviews, defaults to False.
    """
    data = _load_data()
    merchant = _find_merchant_by_id(data, merchant_id)
    detail = {
        "merchant_id": merchant.get("merchant_id"),
        "name": merchant.get("name"),
        "category": merchant.get("category"),
        "rating": merchant.get("rating"),
        "delivery_fee": merchant.get("delivery_fee"),
        "distance": merchant.get("distance"),
        "address": merchant.get("address"),
        "description": merchant.get("description"),
    }
    if include_menu:
        detail["menu"] = merchant.get("menu", [])
    if include_reviews:
        detail["reviews"] = merchant.get("reviews", [])
    return detail


def search_takeaway_products(
    keyword: str,
    location: str,
    merchant_id: Optional[str] = None,
    price_range: Optional[str] = None,
    sort_type: str = "sales",
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    """Search across one or more merchant menus for matching products.

    Args:
        keyword (str): Search keyword for product name or description.
        location (str): The delivery location or area.
        merchant_id (Optional[str]): Filter by specific merchant ID.
        price_range (Optional[str]): Price range filter like '0-30' or '60+'.
        sort_type (str): Sort by 'sales', 'rating', or 'price', defaults to 'sales'.
        page (int): Page number for pagination, defaults to 1.
        page_size (int): Number of results per page, defaults to 10.
    """
    if not keyword:
        raise InvalidRequestException("keyword is required")
    data = _load_data()
    low_price, high_price = _parse_price_range(price_range)
    results = []
    for product in data.get("products", []):
        if merchant_id and product.get("merchant_id") != merchant_id:
            continue
        price = product.get("price", 0.0)
        if not (low_price <= price <= high_price):
            continue
        target = keyword.lower()
        if target not in product.get("name", "").lower() and target not in product.get("description", "").lower():
            continue
        results.append({
            "product_id": product.get("product_id"),
            "name": product.get("name"),
            "merchant_id": product.get("merchant_id"),
            "price": price,
            "rating": product.get("rating"),
            "sales": product.get("sales"),
            "stock": product.get("stock"),
        })
    sort_type = sort_type if sort_type is not None else "sales"
    if sort_type == "rating":
        key_fn = lambda item: item.get("rating", 0.0)
    elif sort_type == "price":
        key_fn = lambda item: item.get("price", 0.0)
    else:
        key_fn = lambda item: item.get("sales", 0)
    results.sort(key=key_fn, reverse=True)
    total = len(results)
    page = page if page is not None else 1
    page_size = page_size if page_size is not None else 10
    page = max(1, page)
    page_size = max(1, min(page_size, 30))
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "location": location,
        "keyword": keyword,
        "sort_type": sort_type,
        "page": page,
        "page_size": page_size,
        "total": total,
        "products": results[start:end],
    }


def get_product_detail(
    product_id: str,
    include_specs: bool = True,
    include_promotions: bool = True,
) -> Dict[str, Any]:
    """Return the detailed product information.
    
    Args:
        product_id (str): Unique identifier of the product.
        include_specs (bool): Whether to include product specifications, defaults to True.
        include_promotions (bool): Whether to include promotional information, defaults to True.
    """
    data = _load_data()
    product = _find_product_by_id(data, product_id)
    detail = {
        "product_id": product.get("product_id"),
        "name": product.get("name"),
        "description": product.get("description"),
        "merchant_id": product.get("merchant_id"),
        "price": product.get("price"),
        "stock": product.get("stock"),
    }
    if include_specs:
        detail["specs"] = product.get("specs", [])
    if include_promotions:
        detail["promotions"] = product.get("promotions", [])
    return detail


def create_order(
    user_id: str,
    products: List[Dict[str, Any]],
    merchant_id: str,
    delivery_address: Dict[str, str],
    payment_method: str = "WeChat",
    coupon_id: Optional[str] = None,
    notes: Optional[str] = None,
    scheduled_delivery: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new TakeAway order and persist it to the store report.
    
    Args:
        user_id (str): Unique identifier of the user placing the order.
        products (List[Dict[str, Any]]): List of products with product_id, quantity, and optional spec.
        merchant_id (str): Unique identifier of the merchant.
        delivery_address (Dict[str, str]): Delivery address containing name, phone, and address fields.
        payment_method (str): Payment method (e.g., 'WeChat', 'Alipay'), defaults to 'WeChat'.
        coupon_id (Optional[str]): Optional coupon identifier to apply discount.
        notes (Optional[str]): Optional order notes or special instructions.
        scheduled_delivery (Optional[str]): Optional ISO format scheduled delivery time.
    """
    if not products:
        raise InvalidRequestException("products list cannot be empty")
    data = _load_data()
    merchant = _find_merchant_by_id(data, merchant_id)
    user = _find_user_by_id(data, user_id)
    _validate_address(delivery_address)
    items = []
    subtotal = 0.0
    for request in products:
        product_id = request.get("product_id")
        quantity = int(request.get("quantity", 1))
        if quantity <= 0:
            raise InvalidRequestException("quantity must be positive")
        product = _find_product_by_id(data, product_id)
        spec_name = request.get("spec")
        spec_price = product.get("price", 0.0)
        if spec_name:
            specs = product.get("specs", [])
            match = next((entry for entry in specs if entry.get("label") == spec_name), None)
            if match:
                spec_price = match.get("price", spec_price)
        if product.get("stock", 0) < quantity:
            raise InvalidRequestException(f"{product_id} stock shortage")
        product["stock"] = max(0, product.get("stock", 0) - quantity)
        line_total = spec_price * quantity
        subtotal += line_total
        items.append({
            "product_id": product_id,
            "name": product.get("name"),
            "quantity": quantity,
            "unit_price": spec_price,
            "spec": spec_name,
        })
    delivery_fee = merchant.get("delivery_fee", 0.0)
    discount = 0.0
    if coupon_id:
        coupon = next((entry for entry in data.get("coupons", []) if entry.get("coupon_id") == coupon_id), None)
        if coupon:
            min_amount = coupon.get("min_amount", 0.0)
            merchant_constraint = coupon.get("merchant_id")
            if subtotal >= min_amount and (not merchant_constraint or merchant_constraint == merchant_id):
                discount = coupon.get("discount", 0.0)
            else:
                raise InvalidRequestException("coupon conditions not satisfied")
        else:
            raise NotFoundException(f"Coupon {coupon_id} not found.")
    total_amount = round(max(subtotal - discount + delivery_fee, 0.0), 2)
    order_id = _next_order_id(data)
    estimated_arrival = _calculate_estimated_arrival(merchant.get("distance", 0.0), scheduled_delivery)
    order = {
        "order_id": order_id,
        "user_id": user_id,
        "merchant_id": merchant_id,
        "products": items,
        "delivery_address": delivery_address,
        "notes": notes or "",
        "coupon_id": coupon_id,
        "payment_method": payment_method,
        "scheduled_delivery": scheduled_delivery,
        "delivery_fee": delivery_fee,
        "discount": discount,
        "items_total": round(subtotal, 2),
        "total_amount": total_amount,
        "status": "pending_payment",
        "created_at": datetime.utcnow().isoformat(),
        "estimated_arrival": estimated_arrival,
    }
    orders = data.setdefault("orders", [])
    orders.append(order)
    _save_data(data)
    return {
        "success": True,
        "order_id": order_id,
        "total": total_amount,
        "estimated_arrival": estimated_arrival,
        "status": order["status"],
    }


def get_order_status(order_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Return the latest status for the provided order.

    Args:
        order_id: The order identifier.
        fields: Optional list of fields to include in the response.
    """
    data = _load_data()
    order = next((entry for entry in data.get("orders", []) if entry.get("order_id") == order_id), None)
    if not order:
        raise NotFoundException(f"Order {order_id} not found.")
    response = {
        "order_id": order_id,
        "status": order.get("status"),
        "estimated_arrival": order.get("estimated_arrival"),
        "total_amount": order.get("total_amount"),
        "progress": order.get("status"),
    }
    if fields:
        response = {key: value for key, value in response.items() if key in fields or key == "order_id"}
    return response


def modify_order(order_id: str, modify_type: str, new_data: Dict[str, Any], modify_reason: str) -> Dict[str, Any]:
    """
    Update an address, note, or scheduled time before the order is locked.
    
    Args:
        order_id: The order identifier.
        modify_type: Type of modification: 'address', 'notes', or 'scheduled_delivery'.
        new_data: New data for the modification.
        modify_reason: Reason for the modification.
    """
    data = _load_data()
    order = next((entry for entry in data.get("orders", []) if entry.get("order_id") == order_id), None)
    if not order:
        raise NotFoundException(f"Order {order_id} not found.")
    if order.get("status") not in {"pending_payment", "pending"}:
        raise InvalidRequestException("Order cannot be modified in its current status.")
    if modify_type == "address":
        address = new_data.get("delivery_address")
        if not isinstance(address, dict):
            if isinstance(new_data, dict) and {"name", "phone", "address"} <= new_data.keys():
                address = new_data
            else:
                raise InvalidRequestException("delivery_address must be provided for address changes.")
        _validate_address(address)
        order["delivery_address"] = address
    elif modify_type == "notes":
        order["notes"] = str(new_data.get("notes", ""))
    elif modify_type == "scheduled_delivery":
        scheduled = new_data.get("scheduled_delivery")
        if scheduled:
            datetime.fromisoformat(scheduled)
        order["scheduled_delivery"] = scheduled
        merchant = _find_merchant_by_id(data, order["merchant_id"])
        order["estimated_arrival"] = _calculate_estimated_arrival(
            merchant.get("distance", 0.0), scheduled
        )
    else:
        raise InvalidRequestException("Unsupported modify_type.")
    order.setdefault("history", []).append({
        "event": "modified",
        "type": modify_type,
        "reason": modify_reason,
        "updated_at": datetime.utcnow().isoformat(),
    })
    _save_data(data)
    return {
        "success": True,
        "order_id": order_id,
        "status": order.get("status"),
    }


def cancel_order(order_id: str, cancel_reason: str, cancel_time: Optional[str] = None) -> Dict[str, Any]:
    """
    Cancel an order that has not yet been delivered.

    Args:
        order_id: The order identifier.
        cancel_reason: Reason for cancellation.
        cancel_time: Optional cancellation time in ISO format.
    """
    data = _load_data()
    order = next((entry for entry in data.get("orders", []) if entry.get("order_id") == order_id), None)
    if not order:
        raise NotFoundException(f"Order {order_id} not found.")
    if order.get("status") in {"delivered", "cancelled"}:
        raise InvalidRequestException("Order cannot be cancelled at this stage.")
    order["status"] = "cancelled"
    order["cancel_reason"] = cancel_reason
    order["cancel_time"] = cancel_time or datetime.utcnow().isoformat()
    order["refund_status"] = "pending_refund" if order.get("total_amount", 0) > 0 else "not_applicable"
    _save_data(data)
    return {
        "order_id": order_id,
        "status": order["status"],
        "refund_status": order["refund_status"],
    }


def get_order_history(
    user_id: str,
    time_range: Optional[Dict[str, str]] = None,
    order_status: Optional[List[str]] = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    """
    Return a paginated order history for a user.
    
    Args:
        user_id: The user identifier.
        time_range: Optional time range filter with start and end dates.
        order_status: Optional list of order statuses to filter by.
        page: Page number for pagination.
        page_size: Number of results per page.
    """
    data = _load_data()
    orders = [entry for entry in data.get("orders", []) if entry.get("user_id") == user_id]
    if order_status:
        orders = [entry for entry in orders if entry.get("status") in order_status]
    if time_range:
        start = time_range.get("start")
        end = time_range.get("end")
        if start:
            start_dt = datetime.fromisoformat(start)
            orders = [entry for entry in orders if datetime.fromisoformat(entry.get("created_at")) >= start_dt]
        if end:
            end_dt = datetime.fromisoformat(end)
            orders = [entry for entry in orders if datetime.fromisoformat(entry.get("created_at")) <= end_dt]
    orders.sort(key=lambda entry: entry.get("created_at", ""), reverse=True)
    total = len(orders)
    page = page if page is not None else 1
    page_size = page_size if page_size is not None else 10
    page = max(1, page)
    page_size = max(1, min(page_size, 20))
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "user_id": user_id,
        "page": page,
        "page_size": page_size,
        "total": total,
        "orders": orders[start:end],
    }
