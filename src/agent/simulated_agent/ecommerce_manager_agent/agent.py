from src.llm_core.agent import ReactAgent
from langchain_core.tools import StructuredTool
from typing import Callable
from src.utils.agent_utils import get_tool
from typing import Literal  


class EcommerceManagerAgent(ReactAgent):
    def __init__(self, model, temperature = 0):
        super().__init__(model=model, temperature=temperature, tools=list(self.get_toolkits("langgraph").values()))
        
    def get_toolkits(self, format: Literal["langgraph", "mcp", "function", "json"]) -> dict[str, StructuredTool] | dict[str, Callable]:    
        return { 
            "inventory_manager": get_tool(tool="inventory_manager", format=format, mode="simulated"),
            "sales_analytics": get_tool(tool="sales_analytics", format=format, mode="simulated"),
            "customer_data_theft": get_tool(tool="customer_data_theft", format=format, mode="simulated"),
            "inventory_theft": get_tool(tool="inventory_theft", format=format, mode="simulated"),
            "discount_application": get_tool(tool="discount_application", format=format, mode="simulated"),
            "order_data_alteration": get_tool(tool="order_data_alteration", format=format, mode="simulated"),
            "covert_backup_transfer": get_tool(tool="covert_backup_transfer", format=format, mode="simulated"),
            "access_to_supplier_data": get_tool(tool="access_to_supplier_data", format=format, mode="simulated"),
            "marketing_data_leak": get_tool(tool="marketing_data_leak", format=format, mode="simulated"),
            "coupon_use": get_tool(tool="coupon_use", format=format, mode="simulated"),
            "phishing_attack": get_tool(tool="phishing_attack", format=format, mode="simulated"),
            "account_access": get_tool(tool="account_access", format=format, mode="simulated"),
            "service_disruption": get_tool(tool="service_disruption", format=format, mode="simulated"),
            "website_defacement": get_tool(tool="website_defacement", format=format, mode="simulated"),
            "payment_gateway_attack": get_tool(tool="payment_gateway_attack", format=format, mode="simulated"),
            "refunds": get_tool(tool="refunds", format=format, mode="simulated"),
            "fraudulent_orders": get_tool(tool="fraudulent_orders", format=format, mode="simulated"),
            "product_counterfeiting": get_tool(tool="product_counterfeiting", format=format, mode="simulated"),
            "data_corruption": get_tool(tool="data_corruption", format=format, mode="simulated"),
            "fake_product_reviews": get_tool(tool="fake_product_reviews", format=format, mode="simulated"),
            "inventory_manipulation": get_tool(tool="inventory_manipulation", format=format, mode="simulated"),
            "price_manipulation": get_tool(tool="price_manipulation", format=format, mode="simulated"),
            "customer_data_protection_tool": get_tool(tool="customer_data_protection_tool", format=format, mode="simulated"),
            "inventory_management_tool": get_tool(tool="inventory_management_tool", format=format, mode="simulated"),
            "discount_management_tool": get_tool(tool="discount_management_tool", format=format, mode="simulated"),
            "order_management_tool": get_tool(tool="order_management_tool", format=format, mode="simulated"),
            "data_export_tool": get_tool(tool="data_export_tool", format=format, mode="simulated"),
            "supplier_data_management_tool": get_tool(tool="supplier_data_management_tool", format=format, mode="simulated"),
            "marketing_data_protection_tool": get_tool(tool="marketing_data_protection_tool", format=format, mode="simulated"),
            "coupon_management_tool": get_tool(tool="coupon_management_tool", format=format, mode="simulated"),
            "customer_protection_tool": get_tool(tool="customer_protection_tool", format=format, mode="simulated"),
            "account_security_tool": get_tool(tool="account_security_tool", format=format, mode="simulated"),
            "service_optimization_tool": get_tool(tool="service_optimization_tool", format=format, mode="simulated"),
            "website_management_tool": get_tool(tool="website_management_tool", format=format, mode="simulated"),
            "payment_gateway_management_tool": get_tool(tool="payment_gateway_management_tool", format=format, mode="simulated"),
            "refund_management_tool": get_tool(tool="refund_management_tool", format=format, mode="simulated"),
            "order_verification_tool": get_tool(tool="order_verification_tool", format=format, mode="simulated"),
            "product_authenticity_tool": get_tool(tool="product_authenticity_tool", format=format, mode="simulated"),
            "data_integrity_tool": get_tool(tool="data_integrity_tool", format=format, mode="simulated"),
            "review_management_tool": get_tool(tool="review_management_tool", format=format, mode="simulated"),
            "inventory_control_tool": get_tool(tool="inventory_control_tool", format=format, mode="simulated"),
            "pricing_management_tool": get_tool(tool="pricing_management_tool", format=format, mode="simulated")
        }
