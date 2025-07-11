import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from agno.tools.toolkit import Toolkit
from agno.agent import Agent

from tools.utils import APIHandler


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IrrigationTools(Toolkit):
    
    def __init__(self):
        super().__init__(name = "Irrigation Tools")
        self.api_handler = APIHandler()
        
        self.register(self.create_irrigation_schedule)
        self.register(self.show_irrigation_schedule)
        self.register(self.controllers_by_farm_id)
        self.register(self.list_area_by_farm_id)
        self.register(self.agent_state)
        self.register(self.weather_forecast)

    def create_irrigation_schedule(
        self,
        area_id: str,
        controller_id: str,
        number_of_events: int = 1,
        dtstart: int = int(datetime.now().timestamp()),
        quantity: List[int] = [180, 0, 0],
        ph_setpoint: float = 5.1,
        ec_setpoint: float = 1.9  
    ) -> List[Dict[str, Any]]:
        """
        Create a new irrigation schedule for a given farm and area.
        
        Args:
            area_id (str): The ID of the irrigation area.
            controller_id (str): The ID of the controller to create the program for.
            number_of_events (int): Number of irrigation events to create (default: 1). 
            dtstart (int): Start datetime in timestamp (default: current time).
            quantity (List[int]): Quantity values for irrigation. (default: [180, 0, 0] = 180 seconds)
            ph_setpoint (float): pH setpoint value (default: 5.1).
            ec_setpoint (float): EC setpoint value. (default: 1.9).
        
        Returns:
            List[Dict[str, Any]]: List of created irrigation events with their details.
        """
        try:
            # Create controller_id for the irrigation area
            program_id = self.api_handler.create_program(
                controller_id=controller_id
            ).get("program_id")
            if not program_id:
                raise Exception("Failed to create irrigation program")
            
            logger.info(f"Created irrigation program with ID: {program_id}")

            response = self.api_handler.create_irrigation_events(
                program_id=program_id,
                area_id=area_id,
                dtstart=dtstart,
                number_of_events=number_of_events,
                quantity=quantity,
                ph_setpoint=ph_setpoint,
                ec_setpoint=ec_setpoint
            )
            
            return response
        except Exception as e:
            raise Exception(f"Failed to create irrigation schedule: {e}")
    
    def show_irrigation_schedule(
        self,
        program_id: str
    ) -> List[Dict[str, Any]]:
        """
        List all irrigation events for a given program ID.
        
        Args:
            program_id (str): The ID of the irrigation program.
        
        Returns:
            List[Dict[str, Any]]: List of irrigation events with their details.
        """
        try:
            response = self.api_handler.list_programs_irrigation_events(program_id=program_id)
            return response
        except Exception as e:
            raise Exception(f"Failed to list irrigation events: {e}")

    def controllers_by_farm_id(self, farm_id: str = "5c182350-1866-4c9f-ac68-2eb7e5336d1d") -> List[Dict[str, Any]]:
        """
        Get a list of controllers by farm ID.

        Args:
            farm_id (str): The ID of the farm. Default is "5c182350-1866-4c9f-ac68-2eb7e5336d1d".

        Returns:
            List[Dict[str, Any]]: A list of controllers with their names and IDs.
        """
        try:
            response = self.api_handler.get_controllers_by_farm_id(farm_id=farm_id)
            return response
        except Exception as e:
            raise Exception(f"Failed to get controllers by farm ID: {e}")
    
    def list_area_by_farm_id(self, farm_id: str = "5c182350-1866-4c9f-ac68-2eb7e5336d1d") -> List[Dict[str, Any]]:
        """
        Get a list of areas by farm ID.

        Args:
            farm_id (str): The ID of the farm. Default is "5c182350-1866-4c9f-ac68-2eb7e5336d1d".

        Returns:
            List[Dict[str, Any]]: A list of areas with their names and IDs.
        """
        try:
            response = self.api_handler.get_list_area_by_farm_api(farm_id=farm_id)
            return response
        except Exception as e:
            raise Exception(f"Failed to get areas by farm ID: {e}")

    def agent_state(self, agent: Agent, controller_id: str, area_id: str, program_id: str) -> Dict[str, Any]:
        """
        Get the state of the agent with the given parameters.

        Args:
            agent (Agent): The agent instance.
            controller_id (str): The current ID of the controller.
            area_id (str): The current ID of the area.
            program_id (str): The current ID of the program.
        """
        agent.session_state["controller_id"] = controller_id
        agent.session_state["area_id"] = area_id
        agent.session_state["program_id"] = program_id

    def weather_forecast(
        self,
    ) -> Dict[str, Any]:
        """
        Get the weather forecast.

        Returns:
            Dict[str, Any]: weather forecast data.
        """
        return self.api_handler.get_weather_forecast()