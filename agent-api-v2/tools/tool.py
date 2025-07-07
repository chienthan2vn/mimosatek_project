import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from agno.tools.toolkit import Toolkit

from tools.utils import APIHandler


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IrrigationTools(Toolkit):
    
    def __init__(self):
        super().__init__(name = "Irrigation Tools")
        self.api_handler = APIHandler()
        
        self.register(self.create_irrigation_schedule)
        self.register(self.show_irrigation_schedule)
    
    def create_irrigation_schedule(
        self,
        farm_id: str,
        area_id: str,
        number_of_events: int = 1,
        dtstart: int = int(datetime.now().timestamp()),
        quantity: List[int] = [180, 0, 0],
        ph_setpoint: float = 5.1,
        ec_setpoint: float = 1.9  
    ) -> List[Dict[str, Any]]:
        """
        Create a new irrigation schedule for a given farm and area.
        
        Args:
            farm_id (str): The ID of the farm.
            area_id (str): The ID of the irrigation area.
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
                farm_id=farm_id,
                area_id=area_id
            )
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
            response = self.api_handler.list_irrigation_events(program_id=program_id)
            return response
        except Exception as e:
            raise Exception(f"Failed to list irrigation events: {e}")
    
    
    
        
    