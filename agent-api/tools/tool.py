from typing import Dict, Any, List
from dataclasses import dataclass, asdict

from agno.tools import Toolkit
from agno.utils.log import logger

from tools.components import api_for_all


class AgricultureToolkit(Toolkit):
    def __init__(self):
        super().__init__(name="agriculture_toolkit")
        self.api_client = api_for_all()
        
        # Register tools
        self.register(self.get_irrigation_status)
        self.register(self.get_weather_forecast)
    
    def get_irrigation_status(self) -> str:
        """
        Get the current irrigation status for crops.
        
        Returns:
            str: Current irrigation status information
        """
        try:
            logger.info("Getting current irrigation status")
            result = self.api_client.get_present_irrigation()
            return str(result) if result else "No irrigation data available"
        except Exception as e:
            logger.error(f"Error getting irrigation status: {e}")
            return f"Error retrieving irrigation status: {str(e)}"
    
    def get_weather_forecast(self, crop: str) -> str:
        """
        Get weather forecast for a specific crop.
        
        Args:
            crop (str): The name of the crop to get weather forecast for
            
        Returns:
            str: Weather forecast information for the specified crop
        """
        try:
            logger.info(f"Getting weather forecast for crop: {crop}")
            result = self.api_client.get_weather_forecast(crop)
            return str(result) if result else f"No weather forecast available for {crop}"
        except Exception as e:
            logger.error(f"Error getting weather forecast for {crop}: {e}")
            return f"Error retrieving weather forecast for {crop}: {str(e)}"


# Create toolkit instance
agriculture_toolkit = AgricultureToolkit()


