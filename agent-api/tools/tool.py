from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import requests
import json

from agno.tools import Toolkit
from agno.utils.log import logger

from tools.components import api_for_all
from tools.utils import TimeConverter
from datetime import datetime

class AgricultureToolkit(Toolkit):
    def __init__(self):
        super().__init__(name="agriculture_toolkit")
        self.api_client = api_for_all()
        
        # Register all available tools based on components.py
        self.register(self.get_program_schedule)
        self.register(self.get_irrigation_events)
        self.register(self.get_weather_forecast)
        self.register(self.create_irrigation_event)

    def get_program_schedule(self, program_id: Optional[str] = "4c17ad40-54d6-11f0-83a2-b5dfc26d8446", before_days: int = 1, after_days: int = 1) -> str:
        """
        Get program schedule from Mimosatek API showing irrigation timing and activities.
        
        Args:
            program_id (Optional[str]): ID of the irrigation program. 
                                      Defaults to "4c17ad40-54d6-11f0-83a2-b5dfc26d8446"
            before_days (int): Number of days before the current date to include in the schedule
            after_days (int): Number of days after the current date to include in the schedule

        Returns:
            str: Program schedule data with timing, duration, and area information
        """
        try:
            logger.info(f"Getting program schedule for: {program_id or 'default'}")
            
            if program_id:
                result = self.api_client.get_program_schedule(program_id=program_id)
            else:
                result = self.api_client.get_program_schedule()
            
            return str(result) if result else "No schedule data available"
            
        except Exception as e:
            logger.error(f"Error getting program schedule: {e}")
            return f"Error retrieving program schedule: {str(e)}"
    
    def get_irrigation_events(self, program_id: Optional[str] = None) -> str:
        """
        Get list of irrigation events and their configuration from Mimosatek API.
        
        Args:
            program_id (Optional[str]): ID of the irrigation program.
                                      Defaults to "4c17ad40-54d6-11f0-83a2-b5dfc26d8446"
        
        Returns:
            str: Irrigation events data with nutrients, timing, and configuration details
        """
        try:
            logger.info(f"Getting irrigation events for: {program_id or 'default'}")
            
            if program_id:
                result = self.api_client.get_irrigation_events(program_id)
            else:
                result = self.api_client.get_irrigation_events()
            
            return str(result) if result else "No irrigation events available"
            
        except Exception as e:
            logger.error(f"Error getting irrigation events: {e}")
            return f"Error retrieving irrigation events: {str(e)}"
    
    def get_weather_forecast(self) -> str:
        """
        Get weather forecast for a specific crop with irrigation recommendations.
            
        Returns:
            str: Weather forecast information for the specified crop
        """
        try:
            logger.info(f"Getting weather forecast")
            result = self.api_client.get_weather_forecast()
            return str(result) if result else f"No weather forecast"
        except Exception as e:
            logger.error(f"Error getting weather forecast: {e}")
            return f"Error retrieving weather forecast: {str(e)}"
    
    def create_irrigation_event(self, program_id: str, area_id: str, event_name: str, 
                                dtstart: int, irrigation_method: int = 0, quantity: Optional[List[int]] = None, 
                                strict_time: bool = False, nutrients_mixing_program: dict = None, 
                                recurrence: str = None, stored_as_template: bool = False, 
                                template_name: str = "") -> str:
        """
        Create a new irrigation event in the Mimosatek API.

        Args:
            program_id (str): ID of the irrigation program (default: "4c17ad40-54d6-11f0-83a2-b5dfc26d8446")
            area_id (str): ID of the area (default: "16106380-f811-11ef-8831-112b9cc8d9f8")
            event_name (str): Name of the irrigation event (default: "KV2")
            dtstart (int): Start time of the event (timestamp in ms).
            irrigation_method (int, optional): Irrigation method (default: 0).
            quantity (Optional[List[int]], optional): List of quantities (default: [200, 0, 0]).
            strict_time (bool, optional): Whether to use strict timing (default: False).
            nutrients_mixing_program (dict, optional): Nutrients mixing program details (default: None).
            recurrence (str, optional): Recurrence rule (default: None).
            stored_as_template (bool, optional): Whether to store as template (default: False).
            template_name (str, optional): Name of the template (default: "").

        Returns:
            str: Result message.
        """
        try:
            # Đảm bảo quantity luôn là danh sách hợp lệ
            if quantity is None or not isinstance(quantity, list):
                quantity = [200, 0, 0]  # Giá trị mặc định

            logger.info(f"Creating irrigation event: {event_name}")
            result = self.api_client.create_irrigation_event(
                program_id=program_id,
                area_id=area_id,
                event_name=event_name,
                dtstart=dtstart,
                irrigation_method=irrigation_method,
                quantity=quantity,
                strict_time=strict_time,
                nutrients_mixing_program=nutrients_mixing_program,
                recurrence=recurrence,
                stored_as_template=stored_as_template,
                template_name=template_name
            )
            return str(result) if result else "Failed to create irrigation event"
        except Exception as e:
            logger.error(f"Error creating irrigation event: {e}")
            return f"Error creating irrigation event: {str(e)}"

    # Convenience methods that combine multiple data sources
    def get_irrigation_status(self) -> str:
        """
        Get comprehensive irrigation status by combining events and schedule data.
        
        Returns:
            str: Combined irrigation status information
        """
        try:
            logger.info("Getting comprehensive irrigation status")
            
            # Get both events and schedule data
            events_result = self.api_client.get_irrigation_events()
            schedule_result = self.api_client.get_program_schedule()
            
            status_data = {
                "irrigation_events": events_result,
                "program_schedule": schedule_result,
                "timestamp": json.dumps({"current_time": str(datetime.now())})
            }
            
            return str(status_data)
            
        except Exception as e:
            logger.error(f"Error getting irrigation status: {e}")
            return f"Error retrieving irrigation status: {str(e)}"

class TimeToolkit(Toolkit):
    def __init__(self):
        super().__init__(name="time_toolkit")
        self.converter = TimeConverter()

        # Register tools
        self.register(self.timestamp_ms_to_datetime)
        self.register(self.datetime_to_timestamp_ms)
        self.register(self.get_other_days)
        self.register(self.get_now_datetime)

    def timestamp_ms_to_datetime(self, timestamp_ms: str) -> str:
        """
        Convert a timestamp in milliseconds to a human-readable datetime string in 'YYYY-MM-DD HH:MM:SS' format.
        
        Args:
            timestamp_ms (str): Timestamp value in milliseconds (as string).
        
        Returns:
            str: Datetime string in 'YYYY-MM-DD HH:MM:SS' format.
        """
        try:
            return self.converter.timestamp_ms_to_datetime(int(timestamp_ms))
        except Exception as e:
            logger.error(f"Error converting timestamp to datetime: {e}")
            return f"Error: {str(e)}"

    def datetime_to_timestamp_ms(self, datetime_str: str) -> str:
        """
        Convert a datetime string in 'YYYY-MM-DD HH:MM:SS' format to a timestamp in milliseconds.
        
        Args:
            datetime_str (str): Datetime string in 'YYYY-MM-DD HH:MM:SS' format.
        
        Returns:
            str: Timestamp value in milliseconds.
        """
        try:
            dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
            return str(self.converter.datetime_to_timestamp_ms(dt))
        except Exception as e:
            logger.error(f"Error converting datetime to timestamp: {e}")
            return f"Error: {str(e)}"

    def get_other_days(self, other_days: int = 1) -> str:
        """
        Get a datetime value representing a number of days before or after the current time.

        Args:
            other_days (int): Number of days to add to the current time. Positive for future dates, negative for past dates.

        Returns:
            str: Datetime string representing the specified number of days before or after the current time.
        """
        try:
            result = self.converter.get_other_days(days=other_days)
            return result.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            logger.error(f"Error getting other days: {e}")
            return f"Error: {str(e)}"
    
    def get_now_datetime(self) -> str:
        """
        Get the current system time as a datetime string in 'YYYY-MM-DD HH:MM:SS' format.
        
        Returns:
            str: Current system time as a datetime string.
        """
        try:
            now = self.converter.get_now_datetime()
            return now.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            logger.error(f"Error getting current datetime: {e}")
            return f"Error: {str(e)}"

# Create toolkit instance
agriculture_toolkit = AgricultureToolkit()


