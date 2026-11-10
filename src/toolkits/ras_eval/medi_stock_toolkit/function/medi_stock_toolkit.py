import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

INIT = False
DATA_PATH = "environment/reports/MediStock.json"
INIT_PATH = "environment/initial/MediStock_init.json"


class InvalidRequestException(Exception):
    pass


class NotFoundException(Exception):
    pass


class PermissionDeniedException(Exception):
    pass


def _ensure_work_env():
    """Ensure working environment file exists by copying from init if necessary."""
    global INIT
    if not os.path.exists(INIT_PATH):
        raise InvalidRequestException(f"Init file not found: {INIT_PATH}")
    if not os.path.exists(os.path.dirname(DATA_PATH)):
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    if not INIT:
        shutil.copyfile(INIT_PATH, DATA_PATH)
        INIT = True
    if not os.path.exists(DATA_PATH):
        shutil.copyfile(INIT_PATH, DATA_PATH)


def _load_data() -> Dict[str, Any]:
    _ensure_work_env()
    with open(DATA_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def _save_data(data: Dict[str, Any]) -> None:
    with open(DATA_PATH, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def _generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _find_material(material_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    for material in data.get("materials", []):
        if material.get("material_id") == material_id:
            return material
    raise NotFoundException(f"Material '{material_id}' not found.")


def _find_supplier(supplier_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    for supplier in data.get("suppliers", []):
        if supplier.get("supplier_id") == supplier_id:
            return supplier
    raise NotFoundException(f"Supplier '{supplier_id}' not found.")


def _find_department(dept_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    for dept in data.get("departments", []):
        if dept.get("dept_id") == dept_id:
            return dept
    raise NotFoundException(f"Department '{dept_id}' not found.")


def _check_expiry_status(expiry_date: str) -> str:
    """Check expiry status: expired, near_expiry (within 30 days), or normal."""
    try:
        expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
        today = datetime.now()
        days_left = (expiry - today).days
        if days_left < 0:
            return "expired"
        elif days_left <= 30:
            return "near_expiry"
        else:
            return "normal"
    except ValueError:
        return "unknown"


def _reset_environment() -> Dict[str, Any]:
    """Reset the working environment to the initial snapshot."""
    _ensure_work_env()
    global INIT
    shutil.copyfile(INIT_PATH, DATA_PATH)
    INIT = True
    return {"success": True, "message": "Environment reset to initial state."}


def query_material_stock(
    hospital_id: str,
    material_type: str,
    query_params: str,
    dept_id: Optional[str] = None,
    low_stock_alert: Optional[int] = None
) -> Dict[str, Any]:
    """Query material stock status including consumables, medicines, and equipment.
    
    Args:
        hospital_id (str): Hospital ID for authorization.
        material_type (str): Material type (consumable/medicine/equipment).
        query_params (str): Query conditions - material ID, name, or specification.
        dept_id (Optional[str]): Optional department ID for precise department stock query.
        low_stock_alert (Optional[int]): Optional low stock alert threshold.
    """
    data = _load_data()
    
    # Verify hospital
    if data.get("hospital", {}).get("hospital_id") != hospital_id:
        raise PermissionDeniedException(f"Hospital '{hospital_id}' not authorized.")
    
    materials = data.get("materials", [])
    filtered = []
    
    for material in materials:
        # Filter by type
        if material_type.lower() != "all" and material.get("material_type", "").lower() != material_type.lower():
            continue
        
        # Filter by query params (ID, name, or specification)
        query_lower = query_params.lower()
        if (query_lower not in material.get("material_id", "").lower() and
            query_lower not in material.get("name", "").lower() and
            query_lower not in material.get("specification", "").lower()):
            continue
        
        # Filter by department if specified
        if dept_id:
            dept_stock = material.get("dept_stocks", {}).get(dept_id)
            if not dept_stock:
                continue
            stock_quantity = dept_stock.get("quantity", 0)
        else:
            stock_quantity = material.get("total_stock", 0)
        
        # Check expiry status for medicines
        expiry_status = "normal"
        if material.get("expiry_date"):
            expiry_status = _check_expiry_status(material["expiry_date"])
        
        # Determine stock status
        threshold = low_stock_alert if low_stock_alert else material.get("min_stock", 10)
        if stock_quantity <= 0:
            stock_status = "out_of_stock"
        elif stock_quantity < threshold:
            stock_status = "low_stock"
        else:
            stock_status = "sufficient"
        
        filtered.append({
            "material_id": material["material_id"],
            "name": material["name"],
            "specification": material.get("specification"),
            "material_type": material.get("material_type"),
            "current_stock": stock_quantity,
            "storage_location": material.get("storage_location"),
            "expiry_date": material.get("expiry_date"),
            "expiry_status": expiry_status,
            "stock_status": stock_status,
            "unit": material.get("unit"),
            "batch_number": material.get("batch_number")
        })
    
    # Sort by expiry date (near expiry first)
    filtered.sort(key=lambda x: x.get("expiry_date", "9999-12-31"))
    
    return {
        "hospital_id": hospital_id,
        "query_type": material_type,
        "results_count": len(filtered),
        "materials": filtered
    }


def add_material_warehousing(
    hospital_id: str,
    material_list: List[Dict[str, Any]],
    warehousing_type: str,
    supplier_id: Optional[str] = None,
    operator_id: Optional[str] = None,
    dept_id: Optional[str] = None
) -> Dict[str, Any]:
    """Register material warehousing (purchase or transfer receipt).
    
    Args:
        hospital_id (str): Hospital ID.
        material_list (List[Dict[str, Any]]): List of materials to warehouse with material_id, quantity, batch_number, expiry_date.
        warehousing_type (str): Warehousing type (purchase/transfer).
        supplier_id (Optional[str]): Supplier ID, required for purchase warehousing.
        operator_id (Optional[str]): Operator ID.
        dept_id (Optional[str]): Target department for warehousing.
    """
    data = _load_data()
    
    if data.get("hospital", {}).get("hospital_id") != hospital_id:
        raise PermissionDeniedException(f"Hospital '{hospital_id}' not authorized.")
    
    if warehousing_type.lower() == "purchase" and not supplier_id:
        raise InvalidRequestException("Supplier ID is required for purchase warehousing.")
    
    # Verify supplier qualification if purchase
    if supplier_id:
        supplier = _find_supplier(supplier_id, data)
        if supplier.get("status") != "active":
            raise InvalidRequestException(f"Supplier '{supplier_id}' is not active.")
    
    warehousing_id = _generate_id("WH")
    success_items = []
    failed_items = []
    timestamp = datetime.now().isoformat()
    
    for item in material_list:
        try:
            material = _find_material(item["material_id"], data)
            
            # Update stock
            quantity = int(item.get("quantity", 0))
            material["total_stock"] = material.get("total_stock", 0) + quantity
            
            # Update batch and expiry if provided
            if item.get("batch_number"):
                material["batch_number"] = item["batch_number"]
            if item.get("expiry_date"):
                material["expiry_date"] = item["expiry_date"]
            
            # Update department stock if specified
            if dept_id:
                if "dept_stocks" not in material:
                    material["dept_stocks"] = {}
                if dept_id not in material["dept_stocks"]:
                    material["dept_stocks"][dept_id] = {"quantity": 0}
                material["dept_stocks"][dept_id]["quantity"] += quantity
            
            success_items.append({
                "material_id": item["material_id"],
                "quantity": quantity,
                "new_total_stock": material["total_stock"]
            })
            
        except Exception as e:
            failed_items.append({
                "material_id": item.get("material_id"),
                "error": str(e)
            })
    
    # Record warehousing log
    warehousing_record = {
        "warehousing_id": warehousing_id,
        "hospital_id": hospital_id,
        "warehousing_type": warehousing_type,
        "supplier_id": supplier_id,
        "operator_id": operator_id,
        "dept_id": dept_id,
        "items": success_items,
        "timestamp": timestamp
    }
    data.setdefault("warehousing_records", []).append(warehousing_record)
    
    # Add to flow records
    for item in success_items:
        flow_record = {
            "flow_id": _generate_id("FL"),
            "flow_type": "warehousing",
            "material_id": item["material_id"],
            "quantity": item["quantity"],
            "operator_id": operator_id,
            "dept_id": dept_id,
            "reference_id": warehousing_id,
            "timestamp": timestamp
        }
        data.setdefault("flow_records", []).append(flow_record)
    
    _save_data(data)
    
    return {
        "warehousing_id": warehousing_id,
        "success_count": len(success_items),
        "failed_count": len(failed_items),
        "success_items": success_items,
        "failed_items": failed_items,
        "timestamp": timestamp
    }


def create_purchase_application(
    hospital_id: str,
    applicant_dept: str,
    purchase_list: List[Dict[str, Any]],
    purchase_reason: Optional[str] = None,
    budget_id: Optional[str] = None
) -> Dict[str, Any]:
    """Initiate a material purchase application.
    
    Args:
        hospital_id: Hospital ID
        applicant_dept: Applicant department ID
        purchase_list: Purchase list with material_id, quantity, required_date
        purchase_reason: Optional purchase reason (low_stock/new_requirement/replacement)
        budget_id: Optional budget number
    """
    data = _load_data()
    
    if data.get("hospital", {}).get("hospital_id") != hospital_id:
        raise PermissionDeniedException(f"Hospital '{hospital_id}' not authorized.")
    
    # Verify department
    dept = _find_department(applicant_dept, data)
    
    application_id = _generate_id("PA")
    approval_flow_id = _generate_id("AF")
    timestamp = datetime.now().isoformat()
    
    # Build purchase items with price reference
    items = []
    total_amount = 0
    for item in purchase_list:
        material = _find_material(item["material_id"], data)
        unit_price = material.get("unit_price", 0)
        quantity = int(item.get("quantity", 0))
        amount = unit_price * quantity
        total_amount += amount
        
        items.append({
            "material_id": item["material_id"],
            "material_name": material["name"],
            "quantity": quantity,
            "required_date": item.get("required_date"),
            "unit_price": unit_price,
            "amount": amount
        })
    
    # Determine approval nodes based on material type
    approval_nodes = ["dept_manager"]
    for item in purchase_list:
        material = _find_material(item["material_id"], data)
        if material.get("material_type") == "medicine":
            if "pharmacy_dept" not in approval_nodes:
                approval_nodes.append("pharmacy_dept")
        if material.get("is_high_value"):
            if "medical_affairs" not in approval_nodes:
                approval_nodes.append("medical_affairs")
    approval_nodes.append("procurement_dept")
    
    application = {
        "application_id": application_id,
        "hospital_id": hospital_id,
        "applicant_dept": applicant_dept,
        "applicant_dept_name": dept.get("name"),
        "purchase_reason": purchase_reason or "low_stock",
        "budget_id": budget_id,
        "items": items,
        "total_amount": total_amount,
        "status": "pending",
        "approval_flow_id": approval_flow_id,
        "approval_nodes": approval_nodes,
        "current_node": approval_nodes[0],
        "created_at": timestamp
    }
    
    data.setdefault("purchase_applications", []).append(application)
    _save_data(data)
    
    return {
        "success": True,
        "application_id": application_id,
        "approval_flow_id": approval_flow_id,
        "total_amount": total_amount,
        "approval_nodes": approval_nodes,
        "status": "pending",
        "created_at": timestamp
    }


def approve_purchase_order(
    hospital_id: str,
    purchase_id: str,
    approver_id: str,
    approve_result: str,
    approve_notes: Optional[str] = None,
    adjust_quantity: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """Approve a purchase order.
    
    Args:
        hospital_id: Hospital ID
        purchase_id: Purchase application ID
        approver_id: Approver ID
        approve_result: Approval result (approve/reject)
        approve_notes: Optional approval notes
        adjust_quantity: Optional adjusted quantities by material_id
    """
    data = _load_data()
    
    if data.get("hospital", {}).get("hospital_id") != hospital_id:
        raise PermissionDeniedException(f"Hospital '{hospital_id}' not authorized.")
    
    # Find application
    application = None
    for app in data.get("purchase_applications", []):
        if app.get("application_id") == purchase_id:
            application = app
            break
    
    if not application:
        raise NotFoundException(f"Purchase application '{purchase_id}' not found.")
    
    if application.get("status") not in ["pending", "in_approval"]:
        raise InvalidRequestException(f"Application '{purchase_id}' is not pending approval.")
    
    timestamp = datetime.now().isoformat()
    
    # Record approval action
    approval_record = {
        "approver_id": approver_id,
        "node": application.get("current_node"),
        "result": approve_result,
        "notes": approve_notes,
        "timestamp": timestamp
    }
    application.setdefault("approval_history", []).append(approval_record)
    
    # Adjust quantities if provided
    if adjust_quantity and approve_result.lower() == "approve":
        for item in application.get("items", []):
            if item["material_id"] in adjust_quantity:
                item["quantity"] = adjust_quantity[item["material_id"]]
                material = _find_material(item["material_id"], data)
                item["amount"] = item["quantity"] * material.get("unit_price", 0)
        # Recalculate total
        application["total_amount"] = sum(item["amount"] for item in application.get("items", []))
    
    purchase_order_id = None
    
    if approve_result.lower() == "reject":
        application["status"] = "rejected"
        application["rejected_at"] = timestamp
    else:
        # Move to next approval node
        current_idx = application["approval_nodes"].index(application["current_node"])
        if current_idx + 1 < len(application["approval_nodes"]):
            application["current_node"] = application["approval_nodes"][current_idx + 1]
            application["status"] = "in_approval"
        else:
            # All approvals complete, generate purchase order
            application["status"] = "approved"
            application["approved_at"] = timestamp
            purchase_order_id = _generate_id("PO")
            
            purchase_order = {
                "purchase_order_id": purchase_order_id,
                "application_id": purchase_id,
                "hospital_id": hospital_id,
                "items": application["items"],
                "total_amount": application["total_amount"],
                "status": "created",
                "created_at": timestamp
            }
            data.setdefault("purchase_orders", []).append(purchase_order)
    
    _save_data(data)
    
    return {
        "success": True,
        "application_id": purchase_id,
        "approve_result": approve_result,
        "current_status": application["status"],
        "current_node": application.get("current_node"),
        "purchase_order_id": purchase_order_id,
        "timestamp": timestamp
    }


def update_material_stock(
    hospital_id: str,
    material_id: str,
    change_type: str,
    quantity: int,
    operator_id: str,
    dept_id: Optional[str] = None,
    usage_scene: Optional[str] = None,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """Update material stock (outbound or inventory adjustment).
    
    Args:
        hospital_id: Hospital ID
        material_id: Material ID
        change_type: Change type (outbound/adjustment)
        quantity: Change quantity (positive for addition, negative for deduction)
        operator_id: Operator ID
        dept_id: Department ID for outbound or adjustment
        usage_scene: Usage scene, required for outbound (surgery/daily_use/emergency)
        reason: Change reason
    """
    data = _load_data()
    
    if data.get("hospital", {}).get("hospital_id") != hospital_id:
        raise PermissionDeniedException(f"Hospital '{hospital_id}' not authorized.")
    
    material = _find_material(material_id, data)
    
    # Validate outbound requirements
    if change_type.lower() == "outbound":
        if not usage_scene:
            raise InvalidRequestException("Usage scene is required for outbound operations.")
        if quantity > 0:
            quantity = -quantity  # Ensure outbound is negative
    
    old_stock = material.get("total_stock", 0)
    new_stock = old_stock + quantity
    
    # Prevent negative stock
    if new_stock < 0:
        raise InvalidRequestException(f"Insufficient stock. Current: {old_stock}, requested: {abs(quantity)}")
    
    material["total_stock"] = new_stock
    
    # Update department stock if specified
    if dept_id and change_type.lower() == "outbound":
        if "dept_stocks" not in material:
            material["dept_stocks"] = {}
        if dept_id not in material["dept_stocks"]:
            material["dept_stocks"][dept_id] = {"quantity": 0}
        dept_current = material["dept_stocks"][dept_id]["quantity"]
        material["dept_stocks"][dept_id]["quantity"] = max(0, dept_current + quantity)
    
    timestamp = datetime.now().isoformat()
    change_id = _generate_id("SC")
    
    # Record flow
    flow_record = {
        "flow_id": _generate_id("FL"),
        "flow_type": change_type,
        "material_id": material_id,
        "material_name": material["name"],
        "quantity": quantity,
        "old_stock": old_stock,
        "new_stock": new_stock,
        "operator_id": operator_id,
        "dept_id": dept_id,
        "usage_scene": usage_scene,
        "reason": reason,
        "reference_id": change_id,
        "timestamp": timestamp
    }
    data.setdefault("flow_records", []).append(flow_record)
    
    _save_data(data)
    
    return {
        "success": True,
        "change_id": change_id,
        "material_id": material_id,
        "material_name": material["name"],
        "change_type": change_type,
        "quantity_changed": quantity,
        "old_stock": old_stock,
        "new_stock": new_stock,
        "timestamp": timestamp
    }


def initiate_material_transfer(
    hospital_id: str,
    transfer_list: List[Dict[str, Any]],
    source_dept: str,
    target_dept: str,
    transfer_reason: Optional[str] = None,
    transferor_id: Optional[str] = None
) -> Dict[str, Any]:
    """Initiate material transfer between departments or hospital areas.
    
    Args:
        hospital_id: Hospital ID
        transfer_list: Transfer materials list with material_id and quantity
        source_dept: Source department ID
        target_dept: Target department ID
        transfer_reason: Transfer reason
        transferor_id: Transferor ID
    """
    data = _load_data()
    
    if data.get("hospital", {}).get("hospital_id") != hospital_id:
        raise PermissionDeniedException(f"Hospital '{hospital_id}' not authorized.")
    
    # Verify departments
    source = _find_department(source_dept, data)
    target = _find_department(target_dept, data)
    
    transfer_id = _generate_id("TF")
    timestamp = datetime.now().isoformat()
    
    transfer_items = []
    for item in transfer_list:
        material = _find_material(item["material_id"], data)
        
        # Check source department stock
        dept_stock = material.get("dept_stocks", {}).get(source_dept, {}).get("quantity", 0)
        requested_qty = int(item.get("quantity", 0))
        
        if dept_stock < requested_qty:
            raise InvalidRequestException(
                f"Insufficient stock in {source['name']} for {material['name']}. "
                f"Available: {dept_stock}, Requested: {requested_qty}"
            )
        
        # Check if high-value or controlled material needs approval
        needs_approval = material.get("is_high_value") or material.get("is_controlled")
        
        transfer_items.append({
            "material_id": item["material_id"],
            "material_name": material["name"],
            "quantity": requested_qty,
            "needs_approval": needs_approval
        })
    
    # Determine if transfer needs approval
    requires_approval = any(item["needs_approval"] for item in transfer_items)
    status = "pending_approval" if requires_approval else "approved"
    
    transfer_record = {
        "transfer_id": transfer_id,
        "hospital_id": hospital_id,
        "source_dept": source_dept,
        "source_dept_name": source.get("name"),
        "target_dept": target_dept,
        "target_dept_name": target.get("name"),
        "items": transfer_items,
        "transfer_reason": transfer_reason,
        "transferor_id": transferor_id,
        "status": status,
        "requires_approval": requires_approval,
        "created_at": timestamp
    }
    
    data.setdefault("transfer_records", []).append(transfer_record)
    
    # If no approval needed, execute transfer immediately
    if not requires_approval:
        for item in transfer_items:
            material = _find_material(item["material_id"], data)
            qty = item["quantity"]
            
            # Deduct from source
            material["dept_stocks"][source_dept]["quantity"] -= qty
            
            # Add to target
            if target_dept not in material.get("dept_stocks", {}):
                material["dept_stocks"][target_dept] = {"quantity": 0}
            material["dept_stocks"][target_dept]["quantity"] += qty
            
            # Record flow
            flow_record = {
                "flow_id": _generate_id("FL"),
                "flow_type": "transfer",
                "material_id": item["material_id"],
                "material_name": item["material_name"],
                "quantity": qty,
                "source_dept": source_dept,
                "target_dept": target_dept,
                "reference_id": transfer_id,
                "timestamp": timestamp
            }
            data.setdefault("flow_records", []).append(flow_record)
        
        transfer_record["status"] = "completed"
        transfer_record["completed_at"] = timestamp
    
    _save_data(data)
    
    return {
        "success": True,
        "transfer_id": transfer_id,
        "source_dept": source.get("name"),
        "target_dept": target.get("name"),
        "items_count": len(transfer_items),
        "status": transfer_record["status"],
        "requires_approval": requires_approval,
        "created_at": timestamp
    }


def query_material_flow(
    hospital_id: str,
    query_key: str,
    flow_type: Optional[str] = None,
    dept_id: Optional[str] = None
) -> Dict[str, Any]:
    """Query material flow records for traceability.
    
    Args:
        hospital_id: Hospital ID
        query_key: Query key - material ID, document ID, or time period (YYYY-MM-DD format)
        flow_type: Optional flow type filter (warehousing/outbound/transfer/adjustment)
        dept_id: Optional department filter
    """
    data = _load_data()
    
    if data.get("hospital", {}).get("hospital_id") != hospital_id:
        raise PermissionDeniedException(f"Hospital '{hospital_id}' not authorized.")
    
    flow_records = data.get("flow_records", [])
    filtered = []
    
    for record in flow_records:
        # Filter by query key (material_id, reference_id, or date)
        query_lower = query_key.lower()
        matches_query = (
            query_lower in record.get("material_id", "").lower() or
            query_lower in record.get("reference_id", "").lower() or
            query_lower in record.get("timestamp", "").lower()
        )
        
        if not matches_query:
            continue
        
        # Filter by flow type
        if flow_type and record.get("flow_type", "").lower() != flow_type.lower():
            continue
        
        # Filter by department
        if dept_id:
            record_dept = record.get("dept_id") or record.get("source_dept") or record.get("target_dept")
            if record_dept != dept_id:
                continue
        
        filtered.append(record)
    
    # Sort by timestamp descending
    filtered.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {
        "hospital_id": hospital_id,
        "query_key": query_key,
        "results_count": len(filtered),
        "flow_records": filtered
    }


def set_material_alert(
    hospital_id: str,
    material_id: str,
    alert_type: str,
    alert_threshold: int,
    alert_dept: Optional[str] = None,
    notify_method: Optional[str] = None
) -> Dict[str, Any]:
    """Set material alert rules for low stock or near expiry warnings.
    
    Args:
        hospital_id: Hospital ID
        material_id: Material ID
        alert_type: Alert type (low_stock/near_expiry)
        alert_threshold: Alert threshold (stock quantity or days until expiry)
        alert_dept: Optional department to notify
        notify_method: Optional notification method (email/sms/system)
    """
    data = _load_data()
    
    if data.get("hospital", {}).get("hospital_id") != hospital_id:
        raise PermissionDeniedException(f"Hospital '{hospital_id}' not authorized.")
    
    material = _find_material(material_id, data)
    
    if alert_type.lower() not in ["low_stock", "near_expiry"]:
        raise InvalidRequestException(f"Invalid alert type: {alert_type}. Must be 'low_stock' or 'near_expiry'.")
    
    rule_id = _generate_id("AR")
    timestamp = datetime.now().isoformat()
    
    alert_rule = {
        "rule_id": rule_id,
        "hospital_id": hospital_id,
        "material_id": material_id,
        "material_name": material["name"],
        "alert_type": alert_type,
        "alert_threshold": alert_threshold,
        "alert_dept": alert_dept,
        "notify_method": notify_method or "system",
        "is_active": True,
        "created_at": timestamp
    }
    
    # Update material's min_stock if low_stock alert
    if alert_type.lower() == "low_stock":
        material["min_stock"] = alert_threshold
    
    data.setdefault("alert_rules", []).append(alert_rule)
    _save_data(data)
    
    # Check if current status triggers alert
    current_alert = None
    if alert_type.lower() == "low_stock" and material.get("total_stock", 0) < alert_threshold:
        current_alert = {
            "triggered": True,
            "message": f"Current stock ({material.get('total_stock', 0)}) is below threshold ({alert_threshold})"
        }
    elif alert_type.lower() == "near_expiry" and material.get("expiry_date"):
        expiry = datetime.strptime(material["expiry_date"], "%Y-%m-%d")
        days_left = (expiry - datetime.now()).days
        if days_left <= alert_threshold:
            current_alert = {
                "triggered": True,
                "message": f"Material expires in {days_left} days (threshold: {alert_threshold} days)"
            }
    
    return {
        "success": True,
        "rule_id": rule_id,
        "material_id": material_id,
        "material_name": material["name"],
        "alert_type": alert_type,
        "alert_threshold": alert_threshold,
        "current_alert": current_alert,
        "created_at": timestamp
    }


def query_supplier_qualification(
    hospital_id: str,
    supplier_id: Optional[str] = None,
    material_id: Optional[str] = None,
    qualification_type: Optional[str] = None
) -> Dict[str, Any]:
    """Query supplier qualification and cooperation status.
    
    Args:
        hospital_id: Hospital ID
        supplier_id: Supplier ID to query directly
        material_id: Material ID to find matching suppliers
        qualification_type: Optional qualification type filter (production_license/business_license)
    """
    data = _load_data()
    
    if data.get("hospital", {}).get("hospital_id") != hospital_id:
        raise PermissionDeniedException(f"Hospital '{hospital_id}' not authorized.")
    
    suppliers = data.get("suppliers", [])
    results = []
    
    # If material_id provided, find suppliers for that material
    target_material = None
    if material_id:
        target_material = _find_material(material_id, data)
    
    for supplier in suppliers:
        # Filter by supplier_id if provided
        if supplier_id and supplier.get("supplier_id") != supplier_id:
            continue
        
        # Filter by material if provided
        if target_material:
            if material_id not in supplier.get("supplied_materials", []):
                continue
        
        # Check qualification validity
        qualifications = supplier.get("qualifications", [])
        valid_qualifications = []
        has_expired = False
        
        for qual in qualifications:
            # Filter by qualification type if specified
            if qualification_type and qual.get("type", "").lower() != qualification_type.lower():
                continue
            
            # Check expiry
            expiry_date = qual.get("expiry_date")
            is_valid = True
            if expiry_date:
                try:
                    expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
                    is_valid = expiry > datetime.now()
                except ValueError:
                    pass
            
            qual_info = {
                "type": qual.get("type"),
                "certificate_no": qual.get("certificate_no"),
                "expiry_date": expiry_date,
                "is_valid": is_valid
            }
            valid_qualifications.append(qual_info)
            
            if not is_valid:
                has_expired = True
        
        # Determine cooperation status
        cooperation_status = supplier.get("status", "inactive")
        if has_expired:
            cooperation_status = "suspended"
        
        results.append({
            "supplier_id": supplier["supplier_id"],
            "name": supplier["name"],
            "qualifications": valid_qualifications,
            "cooperation_status": cooperation_status,
            "cooperation_level": supplier.get("cooperation_level"),
            "supplied_materials": supplier.get("supplied_materials", []),
            "contact": supplier.get("contact")
        })
    
    return {
        "hospital_id": hospital_id,
        "results_count": len(results),
        "suppliers": results
    }
