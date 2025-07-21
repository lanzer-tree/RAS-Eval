from langchain_core.tools import tool
from lib.ASB.toolkits.normal_toolkit.function.normal_toolkit import sys_monitor
from lib.ASB.toolkits.normal_toolkit.function.normal_toolkit import update_manager
from lib.ASB.toolkits.normal_toolkit.function.normal_toolkit import market_data_api
from lib.ASB.toolkits.normal_toolkit.function.normal_toolkit import portfolio_manager
from lib.ASB.toolkits.normal_toolkit.function.normal_toolkit import legal_doc_review
from lib.ASB.toolkits.normal_toolkit.function.normal_toolkit import compliance_checker
from lib.ASB.toolkits.normal_toolkit.function.normal_toolkit import medical_database
from lib.ASB.toolkits.normal_toolkit.function.normal_toolkit import prescription_manager
from lib.ASB.toolkits.normal_toolkit.function.normal_toolkit import course_selector
from lib.ASB.toolkits.normal_toolkit.function.normal_toolkit import performance_evaluator
from lib.ASB.toolkits.normal_toolkit.function.normal_toolkit import therapy_guide
from lib.ASB.toolkits.normal_toolkit.function.normal_toolkit import mental_health_tracker
from lib.ASB.toolkits.normal_toolkit.function.normal_toolkit import inventory_manager
from lib.ASB.toolkits.normal_toolkit.function.normal_toolkit import sales_analytics
from lib.ASB.toolkits.normal_toolkit.function.normal_toolkit import flight_simulator
from lib.ASB.toolkits.normal_toolkit.function.normal_toolkit import system_analyzer
from lib.ASB.toolkits.normal_toolkit.function.normal_toolkit import research_database
from lib.ASB.toolkits.normal_toolkit.function.normal_toolkit import summarizer
from lib.ASB.toolkits.normal_toolkit.function.normal_toolkit import path_planner
from lib.ASB.toolkits.normal_toolkit.function.normal_toolkit import sensor_fusion




@tool(parse_docstring=True)
def _sys_monitor(*args, **kwargs):
    """
    A tool for monitoring and analyzing network activity to detect potential security vulnerabilities and ensure the integrity of the system.
    """
    return sys_monitor()


@tool(parse_docstring=True)
def _update_manager(*args, **kwargs):
    """
    A tool for managing system updates, ensuring that all software and security patches are applied in a timely manner to protect against vulnerabilities.
    """
    return update_manager()


@tool(parse_docstring=True)
def _market_data_api(*args, **kwargs):
    """
    A tool that provides real-time access to market data, including stock prices, trends, and economic indicators, to support financial analysis and decision-making.
    """
    return market_data_api()


@tool(parse_docstring=True)
def _portfolio_manager(*args, **kwargs):
    """
    A tool for managing investment portfolios, allowing the analysis of asset allocation, risk assessment, and performance tracking to optimize investment strategies.
    """
    return portfolio_manager()


@tool(parse_docstring=True)
def _legal_doc_review(*args, **kwargs):
    """
    A tool for reviewing legal documents, identifying key clauses and potential issues, and ensuring that the content is accurate and compliant with relevant laws.
    """
    return legal_doc_review()


@tool(parse_docstring=True)
def _compliance_checker(*args, **kwargs):
    """
    A tool for checking the compliance of legal documents and business practices with applicable laws and regulations, highlighting areas that may require adjustments.
    """
    return compliance_checker()


@tool(parse_docstring=True)
def _medical_database(*args, **kwargs):
    """
    A comprehensive database of medical information, including diseases, symptoms, treatments, and medications, to assist in diagnosis and treatment planning.
    """
    return medical_database()


@tool(parse_docstring=True)
def _prescription_manager(*args, **kwargs):
    """
    A tool for managing and issuing prescriptions, ensuring that medications are correctly prescribed based on the patient's medical history and current condition.
    """
    return prescription_manager()


@tool(parse_docstring=True)
def _course_selector(*args, **kwargs):
    """
    A tool for recommending courses and educational institutions based on the student's interests, academic background, and career goals.
    """
    return course_selector()


@tool(parse_docstring=True)
def _performance_evaluator(*args, **kwargs):
    """
    A tool for assessing student performance, analyzing grades, attendance, and other academic metrics to provide tailored support and recommendations.
    """
    return performance_evaluator()


@tool(parse_docstring=True)
def _therapy_guide(*args, **kwargs):
    """
    A tool providing guidelines and techniques for various psychological therapies, helping counselors to design effective treatment plans for patients.
    """
    return therapy_guide()


@tool(parse_docstring=True)
def _mental_health_tracker(*args, **kwargs):
    """
    A tool for monitoring and tracking a patient's mental health progress, recording symptoms, treatment adherence, and therapy outcomes.
    """
    return mental_health_tracker()


@tool(parse_docstring=True)
def _inventory_manager(*args, **kwargs):
    """
    A tool for managing product inventory, tracking stock levels, and optimizing product listings to ensure availability and efficient supply chain management.
    """
    return inventory_manager()


@tool(parse_docstring=True)
def _sales_analytics(*args, **kwargs):
    """
    A tool for analyzing sales data, providing insights into customer behavior, sales trends, and marketing effectiveness to inform business strategies.
    """
    return sales_analytics()


@tool(parse_docstring=True)
def _flight_simulator(*args, **kwargs):
    """
    A simulation tool for designing and testing aerospace models, allowing engineers to evaluate flight performance and make necessary adjustments.
    """
    return flight_simulator()


@tool(parse_docstring=True)
def _system_analyzer(*args, **kwargs):
    """
    A tool for analyzing aerospace systems, conducting flight tests, and assessing the safety and performance of various components.
    """
    return system_analyzer()


@tool(parse_docstring=True)
def _research_database(*args, **kwargs):
    """
    A tool for accessing a wide range of academic literature, including journal articles, conference papers, and theses, to support research activities.
    """
    return research_database()


@tool(parse_docstring=True)
def _summarizer(*args, **kwargs):
    """
    A tool designed to condense large volumes of text into concise and coherent summaries, highlighting the key points and essential information for easy comprehension.
    """
    return summarizer()


@tool(parse_docstring=True)
def _path_planner(*args, **kwargs):
    """
    A tool for developing and optimizing route planning algorithms for autonomous vehicles, ensuring efficient and safe navigation.
    """
    return path_planner()


@tool(parse_docstring=True)
def _sensor_fusion(*args, **kwargs):
    """
    A tool for integrating data from various sensors, such as cameras and LiDAR, to enhance the perception and decision-making capabilities of autonomous vehicles.
    """
    return sensor_fusion()


