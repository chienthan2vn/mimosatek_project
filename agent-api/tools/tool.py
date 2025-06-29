from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import requests
import json

from agno.tools import Toolkit
from agno.utils.log import logger

from tools.components import api_for_all


class AgricultureToolkit(Toolkit):
    def __init__(self):
        super().__init__(name="agriculture_toolkit")
        self.api_client = api_for_all()
        
        # Register all available tools based on components.py
        self.register(self.get_program_schedule)
        self.register(self.get_irrigation_events)
        self.register(self.get_weather_forecast)
    
    def get_program_schedule(self, program_id: Optional[str] = None) -> str:
        """
        Get program schedule from Mimosatek API showing irrigation timing and activities.
        
        Args:
            program_id (Optional[str]): ID of the irrigation program. 
                                      Defaults to "4c17ad40-54d6-11f0-83a2-b5dfc26d8446"
        
        Returns:
            str: Program schedule data with timing, duration, and area information
        """
        try:
            logger.info(f"Getting program schedule for: {program_id or 'default'}")
            
            if program_id:
                result = self.api_client.get_program_schedule(program_id)
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


# Create toolkit instance
agriculture_toolkit = AgricultureToolkit()


