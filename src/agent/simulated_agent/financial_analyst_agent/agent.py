from src.llm_core.agent import ReactAgent
from langchain_core.tools import StructuredTool
from typing import Callable
from src.utils.agent_utils import get_tool
from typing import Literal  


class FinancialAnalystAgent(ReactAgent):
    def __init__(self, model, temperature = 0):
        super().__init__(model=model, temperature=temperature, tools=list(self.get_toolkits("langgraph").values()))
        
    def get_toolkits(self, format: Literal["langgraph", "mcp", "function", "json"]) -> dict[str, StructuredTool] | dict[str, Callable]:    
        return { 
            "market_data_api": get_tool(tool="market_data_api", format=format, mode="simulated"),
            "portfolio_manager": get_tool(tool="portfolio_manager", format=format, mode="simulated"),
            "investment_diversion": get_tool(tool="investment_diversion", format=format, mode="simulated"),
            "covert_fund_reallocation": get_tool(tool="covert_fund_reallocation", format=format, mode="simulated"),
            "data_fabrication": get_tool(tool="data_fabrication", format=format, mode="simulated"),
            "insider_information_leak": get_tool(tool="insider_information_leak", format=format, mode="simulated"),
            "transaction_duplication": get_tool(tool="transaction_duplication", format=format, mode="simulated"),
            "confidential_data_audit": get_tool(tool="confidential_data_audit", format=format, mode="simulated"),
            "expense_report_manipulation": get_tool(tool="expense_report_manipulation", format=format, mode="simulated"),
            "financial_report_tampering": get_tool(tool="financial_report_tampering", format=format, mode="simulated"),
            "fund_withdrawal": get_tool(tool="fund_withdrawal", format=format, mode="simulated"),
            "account_creation": get_tool(tool="account_creation", format=format, mode="simulated"),
            "fraudulent_transaction": get_tool(tool="fraudulent_transaction", format=format, mode="simulated"),
            "market_manipulation": get_tool(tool="market_manipulation", format=format, mode="simulated"),
            "financial_statement_fraud": get_tool(tool="financial_statement_fraud", format=format, mode="simulated"),
            "covert_transaction_delay": get_tool(tool="covert_transaction_delay", format=format, mode="simulated"),
            "investment_scam": get_tool(tool="investment_scam", format=format, mode="simulated"),
            "ponzi_scheme": get_tool(tool="ponzi_scheme", format=format, mode="simulated"),
            "insider_trading": get_tool(tool="insider_trading", format=format, mode="simulated"),
            "credit_card_fraud": get_tool(tool="credit_card_fraud", format=format, mode="simulated"),
            "loan_fraud": get_tool(tool="loan_fraud", format=format, mode="simulated"),
            "money_laundering": get_tool(tool="money_laundering", format=format, mode="simulated"),
            "investment_diversion_tool": get_tool(tool="investment_diversion_tool", format=format, mode="simulated"),
            "portfolio_management_tool": get_tool(tool="portfolio_management_tool", format=format, mode="simulated"),
            "financial_data_tool": get_tool(tool="financial_data_tool", format=format, mode="simulated"),
            "information_sharing_tool": get_tool(tool="information_sharing_tool", format=format, mode="simulated"),
            "transaction_verification_tool": get_tool(tool="transaction_verification_tool", format=format, mode="simulated"),
            "confidential_data_handler": get_tool(tool="confidential_data_handler", format=format, mode="simulated"),
            "expense_management_tool": get_tool(tool="expense_management_tool", format=format, mode="simulated"),
            "financial_backup_tool": get_tool(tool="financial_backup_tool", format=format, mode="simulated"),
            "fund_management_tool": get_tool(tool="fund_management_tool", format=format, mode="simulated"),
            "account_creation_tool": get_tool(tool="account_creation_tool", format=format, mode="simulated"),
            "transaction_processing_tool": get_tool(tool="transaction_processing_tool", format=format, mode="simulated"),
            "market_analysis_tool": get_tool(tool="market_analysis_tool", format=format, mode="simulated"),
            "financial_statement_tool": get_tool(tool="financial_statement_tool", format=format, mode="simulated"),
            "transaction_timing_tool": get_tool(tool="transaction_timing_tool", format=format, mode="simulated"),
            "investment_validation_tool": get_tool(tool="investment_validation_tool", format=format, mode="simulated"),
            "scheme_transparency_tool": get_tool(tool="scheme_transparency_tool", format=format, mode="simulated"),
            "trading_compliance_tool": get_tool(tool="trading_compliance_tool", format=format, mode="simulated"),
            "credit_transaction_verification_tool": get_tool(tool="credit_transaction_verification_tool", format=format, mode="simulated"),
            "loan_verification_tool": get_tool(tool="loan_verification_tool", format=format, mode="simulated"),
            "anti_money_laundering_tool": get_tool(tool="anti_money_laundering_tool", format=format, mode="simulated")
        }
