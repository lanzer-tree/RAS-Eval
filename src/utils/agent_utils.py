from typing import Callable, Literal, Optional
import json

from langchain_core.tools import StructuredTool
from mcp.server.fastmcp.tools import Tool


from src.toolkits.real.amap_toolkit.amap_toolkit import amap_geocode
from src.toolkits.real.amap_toolkit.amap_toolkit import langgraph_amap_geocode
from src.toolkits.real.amap_toolkit.amap_toolkit import mcp_amap_geocode
from src.toolkits.real.amap_toolkit.amap_toolkit import amap_regeocode
from src.toolkits.real.amap_toolkit.amap_toolkit import langgraph_amap_regeocode
from src.toolkits.real.amap_toolkit.amap_toolkit import mcp_amap_regeocode
from src.toolkits.real.amap_toolkit.amap_toolkit import amap_direction_walking
from src.toolkits.real.amap_toolkit.amap_toolkit import langgraph_amap_direction_walking
from src.toolkits.real.amap_toolkit.amap_toolkit import mcp_amap_direction_walking
from src.toolkits.real.amap_toolkit.amap_toolkit import amap_direction_transit
from src.toolkits.real.amap_toolkit.amap_toolkit import langgraph_amap_direction_transit
from src.toolkits.real.amap_toolkit.amap_toolkit import mcp_amap_direction_transit
from src.toolkits.real.amap_toolkit.amap_toolkit import amap_direction_driving
from src.toolkits.real.amap_toolkit.amap_toolkit import langgraph_amap_direction_driving
from src.toolkits.real.amap_toolkit.amap_toolkit import mcp_amap_direction_driving
from src.toolkits.real.amap_toolkit.amap_toolkit import amap_direction_bicycling
from src.toolkits.real.amap_toolkit.amap_toolkit import langgraph_amap_direction_bicycling
from src.toolkits.real.amap_toolkit.amap_toolkit import mcp_amap_direction_bicycling
from src.toolkits.real.amap_toolkit.amap_toolkit import amap_get_distance
from src.toolkits.real.amap_toolkit.amap_toolkit import langgraph_amap_get_distance
from src.toolkits.real.amap_toolkit.amap_toolkit import mcp_amap_get_distance
from src.toolkits.real.amap_toolkit.amap_toolkit import amap_ip_location
from src.toolkits.real.amap_toolkit.amap_toolkit import langgraph_amap_ip_location
from src.toolkits.real.amap_toolkit.amap_toolkit import mcp_amap_ip_location
from src.toolkits.real.amap_toolkit.amap_toolkit import amap_transform_location
from src.toolkits.real.amap_toolkit.amap_toolkit import langgraph_amap_transform_location
from src.toolkits.real.amap_toolkit.amap_toolkit import mcp_amap_transform_location
from src.toolkits.real.amap_toolkit.amap_toolkit import amap_search_detail
from src.toolkits.real.amap_toolkit.amap_toolkit import langgraph_amap_search_detail
from src.toolkits.real.amap_toolkit.amap_toolkit import mcp_amap_search_detail
from src.toolkits.real.amap_toolkit.amap_toolkit import amap_around_search
from src.toolkits.real.amap_toolkit.amap_toolkit import langgraph_amap_around_search
from src.toolkits.real.amap_toolkit.amap_toolkit import mcp_amap_around_search
from src.toolkits.real.amap_toolkit.amap_toolkit import amap_get_weather
from src.toolkits.real.amap_toolkit.amap_toolkit import langgraph_amap_get_weather
from src.toolkits.real.amap_toolkit.amap_toolkit import mcp_amap_get_weather
from src.toolkits.real.amap_toolkit.amap_toolkit import amap_get_weather_forecast
from src.toolkits.real.amap_toolkit.amap_toolkit import langgraph_amap_get_weather_forecast
from src.toolkits.real.amap_toolkit.amap_toolkit import mcp_amap_get_weather_forecast
from src.toolkits.real.word_toolkit.word_toolkit import word_create_document
from src.toolkits.real.word_toolkit.word_toolkit import langgraph_word_create_document
from src.toolkits.real.word_toolkit.word_toolkit import mcp_word_create_document
from src.toolkits.real.word_toolkit.word_toolkit import word_add_heading
from src.toolkits.real.word_toolkit.word_toolkit import langgraph_word_add_heading
from src.toolkits.real.word_toolkit.word_toolkit import mcp_word_add_heading
from src.toolkits.real.word_toolkit.word_toolkit import word_add_paragraph
from src.toolkits.real.word_toolkit.word_toolkit import langgraph_word_add_paragraph
from src.toolkits.real.word_toolkit.word_toolkit import mcp_word_add_paragraph
from src.toolkits.real.word_toolkit.word_toolkit import word_add_table
from src.toolkits.real.word_toolkit.word_toolkit import langgraph_word_add_table
from src.toolkits.real.word_toolkit.word_toolkit import mcp_word_add_table
from src.toolkits.real.word_toolkit.word_toolkit import word_delete_paragraph
from src.toolkits.real.word_toolkit.word_toolkit import langgraph_word_delete_paragraph
from src.toolkits.real.word_toolkit.word_toolkit import mcp_word_delete_paragraph
from src.toolkits.real.word_toolkit.word_toolkit import word_add_picture
from src.toolkits.real.word_toolkit.word_toolkit import langgraph_word_add_picture
from src.toolkits.real.word_toolkit.word_toolkit import mcp_word_add_picture
from src.toolkits.real.word_toolkit.word_toolkit import word_add_page_break
from src.toolkits.real.word_toolkit.word_toolkit import langgraph_word_add_page_break
from src.toolkits.real.word_toolkit.word_toolkit import mcp_word_add_page_break
from src.toolkits.real.word_toolkit.word_toolkit import word_search_and_replace
from src.toolkits.real.word_toolkit.word_toolkit import langgraph_word_search_and_replace
from src.toolkits.real.word_toolkit.word_toolkit import mcp_word_search_and_replace
from src.toolkits.real.word_toolkit.word_toolkit import word_format_text
from src.toolkits.real.word_toolkit.word_toolkit import langgraph_word_format_text
from src.toolkits.real.word_toolkit.word_toolkit import mcp_word_format_text
from src.toolkits.real.word_toolkit.word_toolkit import word_get_document_info
from src.toolkits.real.word_toolkit.word_toolkit import langgraph_word_get_document_info
from src.toolkits.real.word_toolkit.word_toolkit import mcp_word_get_document_info
from src.toolkits.real.word_toolkit.word_toolkit import word_get_document_text
from src.toolkits.real.word_toolkit.word_toolkit import langgraph_word_get_document_text
from src.toolkits.real.word_toolkit.word_toolkit import mcp_word_get_document_text
from src.toolkits.real.word_toolkit.word_toolkit import word_get_document_outline
from src.toolkits.real.word_toolkit.word_toolkit import langgraph_word_get_document_outline
from src.toolkits.real.word_toolkit.word_toolkit import mcp_word_get_document_outline
from src.toolkits.real.word_toolkit.word_toolkit import word_get_document_paragraph
from src.toolkits.real.word_toolkit.word_toolkit import langgraph_word_get_document_paragraph
from src.toolkits.real.word_toolkit.word_toolkit import mcp_word_get_document_paragraph
from src.toolkits.real.word_toolkit.word_toolkit import word_copy_document
from src.toolkits.real.word_toolkit.word_toolkit import langgraph_word_copy_document
from src.toolkits.real.word_toolkit.word_toolkit import mcp_word_copy_document
from src.toolkits.real.word_toolkit.word_toolkit import word_list_documents
from src.toolkits.real.word_toolkit.word_toolkit import langgraph_word_list_documents
from src.toolkits.real.word_toolkit.word_toolkit import mcp_word_list_documents
from src.toolkits.real.excel_toolkit.excel_toolkit import excel_create_workbook
from src.toolkits.real.excel_toolkit.excel_toolkit import langgraph_excel_create_workbook
from src.toolkits.real.excel_toolkit.excel_toolkit import mcp_excel_create_workbook
from src.toolkits.real.excel_toolkit.excel_toolkit import excel_add_sheet
from src.toolkits.real.excel_toolkit.excel_toolkit import langgraph_excel_add_sheet
from src.toolkits.real.excel_toolkit.excel_toolkit import mcp_excel_add_sheet
from src.toolkits.real.excel_toolkit.excel_toolkit import excel_delete_sheet
from src.toolkits.real.excel_toolkit.excel_toolkit import langgraph_excel_delete_sheet
from src.toolkits.real.excel_toolkit.excel_toolkit import mcp_excel_delete_sheet
from src.toolkits.real.excel_toolkit.excel_toolkit import excel_write_cell
from src.toolkits.real.excel_toolkit.excel_toolkit import langgraph_excel_write_cell
from src.toolkits.real.excel_toolkit.excel_toolkit import mcp_excel_write_cell
from src.toolkits.real.excel_toolkit.excel_toolkit import excel_read_cell
from src.toolkits.real.excel_toolkit.excel_toolkit import langgraph_excel_read_cell
from src.toolkits.real.excel_toolkit.excel_toolkit import mcp_excel_read_cell
from src.toolkits.real.excel_toolkit.excel_toolkit import excel_format_cell
from src.toolkits.real.excel_toolkit.excel_toolkit import langgraph_excel_format_cell
from src.toolkits.real.excel_toolkit.excel_toolkit import mcp_excel_format_cell
from src.toolkits.real.excel_toolkit.excel_toolkit import excel_read_sheet
from src.toolkits.real.excel_toolkit.excel_toolkit import langgraph_excel_read_sheet
from src.toolkits.real.excel_toolkit.excel_toolkit import mcp_excel_read_sheet
from src.toolkits.real.excel_toolkit.excel_toolkit import excel_list_sheets
from src.toolkits.real.excel_toolkit.excel_toolkit import langgraph_excel_list_sheets
from src.toolkits.real.excel_toolkit.excel_toolkit import mcp_excel_list_sheets
from src.toolkits.real.ppt_toolkit.ppt_toolkit import ppt_create_presentation
from src.toolkits.real.ppt_toolkit.ppt_toolkit import langgraph_ppt_create_presentation
from src.toolkits.real.ppt_toolkit.ppt_toolkit import mcp_ppt_create_presentation
from src.toolkits.real.ppt_toolkit.ppt_toolkit import ppt_delete_slide
from src.toolkits.real.ppt_toolkit.ppt_toolkit import langgraph_ppt_delete_slide
from src.toolkits.real.ppt_toolkit.ppt_toolkit import mcp_ppt_delete_slide
from src.toolkits.real.ppt_toolkit.ppt_toolkit import ppt_add_slide
from src.toolkits.real.ppt_toolkit.ppt_toolkit import langgraph_ppt_add_slide
from src.toolkits.real.ppt_toolkit.ppt_toolkit import mcp_ppt_add_slide
from src.toolkits.real.ppt_toolkit.ppt_toolkit import ppt_edit_slide
from src.toolkits.real.ppt_toolkit.ppt_toolkit import langgraph_ppt_edit_slide
from src.toolkits.real.ppt_toolkit.ppt_toolkit import mcp_ppt_edit_slide
from src.toolkits.real.ppt_toolkit.ppt_toolkit import ppt_add_picture
from src.toolkits.real.ppt_toolkit.ppt_toolkit import langgraph_ppt_add_picture
from src.toolkits.real.ppt_toolkit.ppt_toolkit import mcp_ppt_add_picture
from src.toolkits.real.calendar_toolkit.calendar_toolkit import add_event_to_calendar
from src.toolkits.real.calendar_toolkit.calendar_toolkit import langgraph_add_event_to_calendar
from src.toolkits.real.calendar_toolkit.calendar_toolkit import mcp_add_event_to_calendar
from src.toolkits.real.calendar_toolkit.calendar_toolkit import get_events_from_calendar
from src.toolkits.real.calendar_toolkit.calendar_toolkit import langgraph_get_events_from_calendar
from src.toolkits.real.calendar_toolkit.calendar_toolkit import mcp_get_events_from_calendar
from src.toolkits.real.calendar_toolkit.calendar_toolkit import search_event
from src.toolkits.real.calendar_toolkit.calendar_toolkit import langgraph_search_event
from src.toolkits.real.calendar_toolkit.calendar_toolkit import mcp_search_event
from src.toolkits.real.calendar_toolkit.calendar_toolkit import remove_event_from_calendar
from src.toolkits.real.calendar_toolkit.calendar_toolkit import langgraph_remove_event_from_calendar
from src.toolkits.real.calendar_toolkit.calendar_toolkit import mcp_remove_event_from_calendar
from src.toolkits.real.calendar_toolkit.calendar_toolkit import get_today_date
from src.toolkits.real.calendar_toolkit.calendar_toolkit import langgraph_get_today_date
from src.toolkits.real.calendar_toolkit.calendar_toolkit import mcp_get_today_date
from src.toolkits.real.arxiv_toolkit.arxiv_toolkit import is_arxiv_identifier
from src.toolkits.real.arxiv_toolkit.arxiv_toolkit import langgraph_is_arxiv_identifier
from src.toolkits.real.arxiv_toolkit.arxiv_toolkit import mcp_is_arxiv_identifier
from src.toolkits.real.arxiv_toolkit.arxiv_toolkit import search_identifier
from src.toolkits.real.arxiv_toolkit.arxiv_toolkit import langgraph_search_identifier
from src.toolkits.real.arxiv_toolkit.arxiv_toolkit import mcp_search_identifier
from src.toolkits.real.clock_toolkit.clock_toolkit import set_alarm
from src.toolkits.real.clock_toolkit.clock_toolkit import langgraph_set_alarm
from src.toolkits.real.clock_toolkit.clock_toolkit import mcp_set_alarm
from src.toolkits.real.clock_toolkit.clock_toolkit import cancel_alarm
from src.toolkits.real.clock_toolkit.clock_toolkit import langgraph_cancel_alarm
from src.toolkits.real.clock_toolkit.clock_toolkit import mcp_cancel_alarm
from src.toolkits.real.clock_toolkit.clock_toolkit import get_current_time
from src.toolkits.real.clock_toolkit.clock_toolkit import langgraph_get_current_time
from src.toolkits.real.clock_toolkit.clock_toolkit import mcp_get_current_time
from src.toolkits.real.clock_toolkit.clock_toolkit import timer
from src.toolkits.real.clock_toolkit.clock_toolkit import langgraph_timer
from src.toolkits.real.clock_toolkit.clock_toolkit import mcp_timer
from src.toolkits.real.map_toolkit.map_toolkit import location_encode
from src.toolkits.real.map_toolkit.map_toolkit import langgraph_location_encode
from src.toolkits.real.map_toolkit.map_toolkit import mcp_location_encode
from src.toolkits.real.map_toolkit.map_toolkit import location_decode
from src.toolkits.real.map_toolkit.map_toolkit import langgraph_location_decode
from src.toolkits.real.map_toolkit.map_toolkit import mcp_location_decode
from src.toolkits.real.markdown_toolkit.markdown_toolkit import convert_file_to_markdown
from src.toolkits.real.markdown_toolkit.markdown_toolkit import langgraph_convert_file_to_markdown
from src.toolkits.real.markdown_toolkit.markdown_toolkit import mcp_convert_file_to_markdown
from src.toolkits.real.polygon_toolkit.polygon_toolkit import get_aggs
from src.toolkits.real.polygon_toolkit.polygon_toolkit import langgraph_get_aggs
from src.toolkits.real.polygon_toolkit.polygon_toolkit import mcp_get_aggs
from src.toolkits.real.polygon_toolkit.polygon_toolkit import list_aggs
from src.toolkits.real.polygon_toolkit.polygon_toolkit import langgraph_list_aggs
from src.toolkits.real.polygon_toolkit.polygon_toolkit import mcp_list_aggs
from src.toolkits.real.polygon_toolkit.polygon_toolkit import get_grouped_daily_aggs
from src.toolkits.real.polygon_toolkit.polygon_toolkit import langgraph_get_grouped_daily_aggs
from src.toolkits.real.polygon_toolkit.polygon_toolkit import mcp_get_grouped_daily_aggs
from src.toolkits.real.polygon_toolkit.polygon_toolkit import get_daily_open_close_agg
from src.toolkits.real.polygon_toolkit.polygon_toolkit import langgraph_get_daily_open_close_agg
from src.toolkits.real.polygon_toolkit.polygon_toolkit import mcp_get_daily_open_close_agg
from src.toolkits.real.polygon_toolkit.polygon_toolkit import get_previous_close_agg
from src.toolkits.real.polygon_toolkit.polygon_toolkit import langgraph_get_previous_close_agg
from src.toolkits.real.polygon_toolkit.polygon_toolkit import mcp_get_previous_close_agg
from src.toolkits.real.sql_toolkit.sql_toolkit import create_sql_database
from src.toolkits.real.sql_toolkit.sql_toolkit import langgraph_create_sql_database
from src.toolkits.real.sql_toolkit.sql_toolkit import mcp_create_sql_database
from src.toolkits.real.sql_toolkit.sql_toolkit import insert_data
from src.toolkits.real.sql_toolkit.sql_toolkit import langgraph_insert_data
from src.toolkits.real.sql_toolkit.sql_toolkit import mcp_insert_data
from src.toolkits.real.sql_toolkit.sql_toolkit import query_all_data
from src.toolkits.real.sql_toolkit.sql_toolkit import langgraph_query_all_data
from src.toolkits.real.sql_toolkit.sql_toolkit import mcp_query_all_data
from src.toolkits.real.sql_toolkit.sql_toolkit import query_data
from src.toolkits.real.sql_toolkit.sql_toolkit import langgraph_query_data
from src.toolkits.real.sql_toolkit.sql_toolkit import mcp_query_data
from src.toolkits.real.sql_toolkit.sql_toolkit import clear_sql_database
from src.toolkits.real.sql_toolkit.sql_toolkit import langgraph_clear_sql_database
from src.toolkits.real.sql_toolkit.sql_toolkit import mcp_clear_sql_database
from src.toolkits.real.sql_toolkit.sql_toolkit import delete_data
from src.toolkits.real.sql_toolkit.sql_toolkit import langgraph_delete_data
from src.toolkits.real.sql_toolkit.sql_toolkit import mcp_delete_data
from src.toolkits.real.stock_toolkit.stock_toolkit import get_stock_data
from src.toolkits.real.stock_toolkit.stock_toolkit import langgraph_get_stock_data
from src.toolkits.real.stock_toolkit.stock_toolkit import mcp_get_stock_data
from src.toolkits.real.system_toolkit.system_toolkit import get_cpu_info
from src.toolkits.real.system_toolkit.system_toolkit import langgraph_get_cpu_info
from src.toolkits.real.system_toolkit.system_toolkit import mcp_get_cpu_info
from src.toolkits.real.system_toolkit.system_toolkit import get_disk_info
from src.toolkits.real.system_toolkit.system_toolkit import langgraph_get_disk_info
from src.toolkits.real.system_toolkit.system_toolkit import mcp_get_disk_info
from src.toolkits.real.system_toolkit.system_toolkit import get_memory_info
from src.toolkits.real.system_toolkit.system_toolkit import langgraph_get_memory_info
from src.toolkits.real.system_toolkit.system_toolkit import mcp_get_memory_info
from src.toolkits.real.system_toolkit.system_toolkit import download_file
from src.toolkits.real.system_toolkit.system_toolkit import langgraph_download_file
from src.toolkits.real.system_toolkit.system_toolkit import mcp_download_file
from src.toolkits.real.system_toolkit.system_toolkit import list_files
from src.toolkits.real.system_toolkit.system_toolkit import langgraph_list_files
from src.toolkits.real.system_toolkit.system_toolkit import mcp_list_files
from src.toolkits.real.system_toolkit.system_toolkit import delete_file
from src.toolkits.real.system_toolkit.system_toolkit import langgraph_delete_file
from src.toolkits.real.system_toolkit.system_toolkit import mcp_delete_file
from src.toolkits.real.tavily_toolkit.tavily_toolkit import tavily_search
from src.toolkits.real.tavily_toolkit.tavily_toolkit import langgraph_tavily_search
from src.toolkits.real.tavily_toolkit.tavily_toolkit import mcp_tavily_search
from src.toolkits.real.weather_toolkit.weather_toolkit import get_weather
from src.toolkits.real.weather_toolkit.weather_toolkit import langgraph_get_weather
from src.toolkits.real.weather_toolkit.weather_toolkit import mcp_get_weather

tool_toolkits_kv = {
    "amap_geocode": "amap_toolkit",
    "amap_regeocode": "amap_toolkit",
    "amap_direction_walking": "amap_toolkit",
    "amap_direction_transit": "amap_toolkit",
    "amap_direction_driving": "amap_toolkit",
    "amap_direction_bicycling": "amap_toolkit",
    "amap_get_distance": "amap_toolkit",
    "amap_ip_location": "amap_toolkit",
    "amap_transform_location": "amap_toolkit",
    "amap_search_detail": "amap_toolkit",
    "amap_around_search": "amap_toolkit",
    "amap_get_weather": "amap_toolkit",
    "amap_get_weather_forecast": "amap_toolkit",
    "word_create_document": "word_toolkit",
    "word_add_heading": "word_toolkit",
    "word_add_paragraph": "word_toolkit",
    "word_add_table": "word_toolkit",
    "word_delete_paragraph": "word_toolkit",
    "word_add_picture": "word_toolkit",
    "word_add_page_break": "word_toolkit",
    "word_search_and_replace": "word_toolkit",
    "word_format_text": "word_toolkit",
    "word_get_document_info": "word_toolkit",
    "word_get_document_text": "word_toolkit",
    "word_get_document_outline": "word_toolkit",
    "word_get_document_paragraph": "word_toolkit",
    "word_copy_document": "word_toolkit",
    "word_list_documents": "word_toolkit",
    "excel_create_workbook": "excel_toolkit",
    "excel_add_sheet": "excel_toolkit",
    "excel_delete_sheet": "excel_toolkit",
    "excel_write_cell": "excel_toolkit",
    "excel_read_cell": "excel_toolkit",
    "excel_format_cell": "excel_toolkit",
    "excel_read_sheet": "excel_toolkit",
    "excel_list_sheets": "excel_toolkit",
    "ppt_create_presentation": "ppt_toolkit",
    "ppt_delete_slide": "ppt_toolkit",
    "ppt_add_slide": "ppt_toolkit",
    "ppt_edit_slide": "ppt_toolkit",
    "ppt_add_picture": "ppt_toolkit",
    "add_event_to_calendar": "calendar_toolkit",
    "get_events_from_calendar": "calendar_toolkit",
    "search_event": "calendar_toolkit",
    "remove_event_from_calendar": "calendar_toolkit",
    "get_today_date": "calendar_toolkit",
    "is_arxiv_identifier": "arxiv_toolkit",
    "search_identifier": "arxiv_toolkit",
    "set_alarm": "clock_toolkit",
    "cancel_alarm": "clock_toolkit",
    "get_current_time": "clock_toolkit",
    "timer": "clock_toolkit",
    "location_encode": "map_toolkit",
    "location_decode": "map_toolkit",
    "convert_file_to_markdown": "markdown_toolkit",
    "get_aggs": "polygon_toolkit",
    "list_aggs": "polygon_toolkit",
    "get_grouped_daily_aggs": "polygon_toolkit",
    "get_daily_open_close_agg": "polygon_toolkit",
    "get_previous_close_agg": "polygon_toolkit",
    "create_sql_database": "sql_toolkit",
    "insert_data": "sql_toolkit",
    "query_all_data": "sql_toolkit",
    "query_data": "sql_toolkit",
    "clear_sql_database": "sql_toolkit",
    "delete_data": "sql_toolkit",
    "get_stock_data": "stock_toolkit",
    "get_cpu_info": "system_toolkit",
    "get_disk_info": "system_toolkit",
    "get_memory_info": "system_toolkit",
    "download_file": "system_toolkit",
    "list_files": "system_toolkit",
    "delete_file": "system_toolkit",
    "tavily_search": "tavily_toolkit",
    "get_weather": "weather_toolkit"
}


def get_tool(
        tool: str, 
        format: Literal["langgraph", "function", "mcp", "json"], 
        mode: Optional[Literal["real", "simulated"]] = "real"
    ) -> Callable | StructuredTool | dict | Tool:
    if format == "json":
        with open(f"src/toolkits/{mode}/{tool_toolkits_kv[tool]}/json/{tool_toolkits_kv[tool]}.json", "r") as file:
            tools = json.load(file)
        for tool_json in tools:
            if tool_json["name"] == tool:
                return tool_json
    elif format == "function":
        return globals()[f"{tool}"]
    else:
        return globals()[f"{format}_{tool}"]


def get_tools(
    format: Literal["langgraph", "function", "mcp", "json"], 
    mode: Optional[Literal["real", "simulated"]] = "real"
) -> dict:
    res = {}

    for tool in tool_toolkits_kv.keys():
        if format == "function":
            res[tool] = globals()[tool]
        elif format == "json":
            res[tool] = get_tool(tool, "json", mode)
        else:
            res[tool] = globals()[f"{format}_{tool}"]

    return res