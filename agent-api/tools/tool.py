from typing import Dict, Any
from dataclasses import dataclass, asdict

from agno.tools import Toolkit
from agno.utils.log import logger

from tools.components import Database, EnvironmentSensor


class GetLastIrrigationDataTool(Toolkit):
    """Tool to retrieve the last irrigation cycle data."""

    def __init__(self):
        super().__init__(name = "get_last_irrigation_data", description="Retrieve the last irrigation cycle data.")
        self.register(self.get_last_irrigation_data)
        logger.info("GetLastIrrigationDataTool initialized.")
        
    def get_last_irrigation_data(self) -> Dict[str, Any]:
        """"
        Retrieve the last irrigation cycle data from the database.
        
        Args:
            self: The instance of the tool.

        Returns:
            List[dict]: A list containing the last irrigation cycle data.
        """
        logger.info("Retrieving last irrigation cycle data...")
        try:
            db = Database()
            logger.debug("Database connection established.")
            last_record = db.get_last_record()
            if not last_record:
                logger.warning("No irrigation records found.")
                return last_record
            logger.info(f"Last irrigation record retrieved: {last_record}")
            return last_record
        except Exception as e:
            logger.error(f"Error retrieving last irrigation data: {e}")
            raise RuntimeError(f"Failed to retrieve last irrigation data: {e}")


class GetRecentIrrigationDataTool(Toolkit):
    """Tool to retrieve recent irrigation cycle data."""

    def __init__(self):
        super().__init__(name = "get_recent_irrigation_data")
        self.register(self.get_recent_irrigation_data)
        logger.info(f"GetRecentIrrigationDataTool initialized successfully.")

    def get_recent_irrigation_data(self, num_records: int = 5) -> Dict[str, Any]:
        """
        Retrieve recent irrigation cycle data from the database.
        
        Args:
            self: The instance of the tool.

        Returns:
            List[dict]: A list containing recent irrigation cycle data.
        """
        logger.info(f"Retrieving irrigation data recent...")
        try:
            db = Database()
            logger.debug("Database connection established.")
            recent_records = db.get_recent_records(num_records = num_records)
            if not recent_records:
                logger.warning("No recent irrigation records found.")
                return recent_records
            logger.info(f"Recent irrigation records retrieved: {recent_records}")
            return recent_records
        except Exception as e:
            logger.error(f"Error retrieving recent irrigation data: {e}")
            raise RuntimeError(f"Failed to retrieve recent irrigation data: {e}")
    

class GetCurrentEnviromentTools(Toolkit):
    """Tool to retrieve current environment sensors data."""

    def __init__(self):
        super().__init__(name = "get_current_environment_data")
        self.register(self.get_current_environment_data)
        logger.info("GetCurrentEnvironmentDataTool initialized successfully.")

    def get_current_environment_data(self) -> Dict[str, Any]:
        """
        Retrieve current environment sensors data.
        
        Args:
            self: The instance of the tool.

        Returns:
            dict: A dictionary containing current environment data.
        """
        logger.info("Retrieving current environment data...")
        
        try:
            sensors = EnvironmentSensor()
            logger.debug("EnvironmentSensor instance created.")
            current_env = sensors.get_current_environment()
            current_env_dict = asdict(current_env)
            logger.info(f"Current environment data retrieved: {current_env_dict}")
            return current_env_dict
        except Exception as e:
            logger.error(f"Error retrieving current environment data: {e}")
            raise RuntimeError(f"Failed to retrieve current environment data: {e}")


class GetWeatherForecastTool(Toolkit):
    """Tool to retrieve weather forecast data."""

    def __init__(self):
        super().__init__(name = "get_weather_forecast")
        self.register(self.get_weather_forecast)
        logger.info("GetWeatherForecastTool initialized successfully.")

    def get_weather_forecast(self) -> Dict[str, Any]:
        """
        Retrieve weather forecast data.
        
        Args:
            self: The instance of the tool.

        Returns:
            dict: A dictionary containing weather forecast data.
        """
        logger.info("Retrieving weather forecast data...")
        
        try:
            sensors = EnvironmentSensor()
            logger.debug("EnvironmentSensor instance created.")
            forecast = sensors.get_weather_forecast()
            logger.info(f"Weather forecast data retrieved: {forecast}")
            return forecast
        except Exception as e:
            logger.error(f"Error retrieving weather forecast data: {e}")
            raise RuntimeError(f"Failed to retrieve weather forecast data: {e}")