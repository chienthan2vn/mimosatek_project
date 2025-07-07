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
        # self.register(self.get_list_area_by_farm)
        self.register(self.create_program)
        self.register(self.get_controller_id_by_farm)

    def get_program_schedule(self, program_id: str, before_days: int = -1, after_days: int = 1) -> str:
        """
        Get program schedule from Mimosatek API showing irrigation timing and activities.
        
        Args:
            program_id (str): The ID of the irrigation program
            before_days (int): Number of days before the current date to include in the schedule (default: -1)
            after_days (int): Number of days after the current date to include in the schedule (default: 1)

        Returns:
            str: Program schedule data with timing, duration, and area information
        """
        try:
            logger.info(f"Getting program schedule for program: {program_id}")
            
            result = self.api_client.get_program_schedule(
                program_id=program_id, 
                before_days=before_days, 
                after_days=after_days
            )
            
            return str(result) if result else "No schedule data available"
            
        except Exception as e:
            logger.error(f"Error getting program schedule: {e}")
            return f"Error retrieving program schedule: {str(e)}"

    def get_irrigation_events(self, program_id: str) -> str:
        """
        Get list of irrigation events and their configuration from Mimosatek API.
        
        Args:
            program_id (str): The ID of the irrigation program to get events for

        Returns:
            str: Irrigation events data with nutrients, timing, and configuration details
        """
        try:
            logger.info(f"Getting irrigation events for program: {program_id}")

            result = self.api_client.get_irrigation_events(program_id=program_id)

            return str(result) if result else "No irrigation events available"
            
        except Exception as e:
            logger.error(f"Error getting irrigation events: {e}")
            return f"Error retrieving irrigation events: {str(e)}"

    def create_irrigation_event(self, program_id: str, dtstart: int, interval_minutes: int = 60, n: int = 1,
                                quantity_second: int = 200, ec_setpoint: float = 1.9,
                                ph_setpoint: float = 5.1) -> str:
        """
        Create or Edit Choiirrigation event(s) using Mimosatek API.

        Args:
            program_id (str): The ID of the irrigation program to create events for.
            dtstart (int): Start time of the first event (timestamp in ms) (default: current time).
            interval_minutes (int, optional): Interval in minutes between events (default: 60).
            n (int, optional): Number of irrigation events to create (default: 1).
            quantity_second (int, optional): Irrigation duration in seconds (default: 200).
            ec_setpoint (float, optional): Electrical conductivity setpoint value (default: 1.9).
            ph_setpoint (float, optional): pH setpoint value (default: 5.1).

        Returns:
            str: Result message. Single event dict if n=1, list of events if n>1.
        """
        try:
            logger.info(f"Creating {n} irrigation event(s)")
            result = self.api_client.create_irrigation_event(
                program_id=program_id,
                dtstart=dtstart,
                interval_minutes=interval_minutes,
                n=n,
                quantity_second=quantity_second,
                ec_setpoint=ec_setpoint,
                ph_setpoint=ph_setpoint
            )
            return str(result) if result else "Failed to create irrigation event"
        except Exception as e:
            logger.error(f"Error creating irrigation event: {e}")
            return f"Error creating irrigation event: {str(e)}"

    # def get_list_area_by_farm(self, farm_id: str) -> str:
    #     """
    #     Get list of areas for a specific farm from Mimosatek API.
        
    #     Args:
    #         farm_id (str): The ID of the farm to get areas for
            
    #     Returns:
    #         str: List of areas data including plant information
    #     """
    #     try:
    #         logger.info(f"Getting areas for farm: {farm_id}")
            
    #         result = self.api_client.get_list_area_by_farm(farm_id=farm_id)
            
    #         return str(result) if result else "No areas found for this farm"
            
    #     except Exception as e:
    #         logger.error(f"Error getting areas for farm: {e}")
    #         return f"Error retrieving areas for farm: {str(e)}"

    def create_program(self, controller_id: str) -> str:
        """
        Create a new irrigation program using Mimosatek API (Always call when creating or editing irrigation events).
        
        Args:
            controller_id (str): The ID of the controller to create the program for
            
        Returns:
            str: Response data from program creation
        """
        try:
            logger.info(f"Creating program for controller: {controller_id}")
            result = self.api_client.create_program(controller_id=controller_id)
            return str(result) if result else "Failed to create program"
            
        except Exception as e:
            logger.error(f"Error creating program: {e}")
            return f"Error creating program: {str(e)}"

    def get_controller_id_by_farm(self) -> str:
        """
        Get the controller ID.
            
        Returns:
            str: The controller ID information
        """
        try:

            result = self.api_client.get_controller_id_by_farm()

            return str(result) if result else "No controller found for this farm"
            
        except Exception as e:
            logger.error(f"Error getting controller ID for farm: {e}")
            return f"Error retrieving controller ID: {str(e)}"

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
        Get the current time as a datetime string in 'YYYY-MM-DD HH:MM:SS' format.
        
        Returns:
            str: Current time as a datetime string.
        """
        try:
            now = self.converter.get_now_datetime()
            return now.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            logger.error(f"Error getting current datetime: {e}")
            return f"Error: {str(e)}"

# Create toolkit instance
agriculture_toolkit = AgricultureToolkit()


