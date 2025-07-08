import os
import json
import logging
import requests
from typing import List, Optional, Dict, Any

from tools.payload import (get_payload_of_create_program_api,
                           get_payload_of_list_programs_irrigation_envents_api,
                           get_payload_for_create_irrigation_event_api)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIHandler:
    """
    Class to handle API requests and responses for Mimosatek.
    """

    def __init__(self):
        self.token = self.get_authen_token()
        self.url = "https://demo.mimosatek.com/api/monitor"
        self.headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
            'authorization': self.token,
            'Content-Type': 'application/json'
        }

    def get_authen_token(self) -> str:
            """
            Function to get the authentication token from the Mimosatek API.
            """
            url = "https://demo.mimosatek.com/api/auth"

            payload = {
                "query": """
                    mutation login ($username: String!, $password: String!) {
                        login(username: $username, password: $password, long_lived: true) {
                            token
                        }
                    }
                """,
                "variables": {
                    "username": "phonglab@mimosatek.com",
                    "password": "mimosatek"
                }
            }

            headers = {
                'accept': '*/*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
                'Content-Type': 'application/json'
            }

            try:
                response = requests.post(url, headers=headers, json=payload)
                response.raise_for_status()  # Raise an exception for bad status codes
                
                response_data = response.json()
                
                if "data" in response_data and "login" in response_data["data"]:
                    return response_data["data"]["login"]["token"]
                else:
                    raise ValueError("Invalid response format or login failed")
                
            except requests.exceptions.RequestException as e:
                raise Exception(f"Request failed: {e}")
            except (KeyError, ValueError) as e:
                raise Exception(f"Failed to extract token from response: {e}")
            
    @staticmethod
    def get_controller_id_by_farm_and_area_id(farm_id: str, area_id: str) -> Dict[str, Any]:
        """
        Get the controller ID based on farm and area IDs.
        
        Args:
            farm_id (str): The ID of the farm.
            area_id (str): The ID of the area.
        
        Returns:
            str: The controller ID.
        """

        #TODO: Implement the logic to retrieve the controller ID based on farm and area IDs.s
        try:
            return {
                "farm_id": farm_id,
                "area_id": area_id,
                "controller_id": "4034b240-6fc1-11ed-9cbe-f9420b7f5b37"  # Replace with actual logic to get controller ID
            }
        except Exception as e:
            logger.error(f"Error getting controller ID for farm {farm_id} and area {area_id}: {e}")
            raise Exception(f"Failed to get controller ID: {e}")
    

    def create_program(
            self,
            farm_id: str,
            area_id: str,
        ) -> Dict[str, Any]:
        """
        Create a new irrigation program.
        
        Args:
            controler_id (str): The ID of the controller to create the program for.
        
        Returns:
            Dict[str, Any]: The response from the API.
        """
        try:
           
            controller_info = APIHandler().get_controller_id_by_farm_and_area_id(farm_id=farm_id, area_id=area_id)
            controller_id = controller_info.get("controller_id")
            logger.info(f"Controller ID: {controller_id}")
            
            
            # Prepare the payload for creating the program
            payload = get_payload_of_create_program_api(controller_id=controller_id)
            logger.info(f"Payload for creating program: {json.dumps(payload, indent=2)}")
            # Make the API request to create the program
            response = requests.post(
                self.url,
                headers=self.headers,
                json=payload
            )
            
            response.raise_for_status()  # Raise an exception for bad status codes
            logger.info(f"Status code: {response.status_code}")
            
            response_data = response.json()
            logger.info(f"Response data: {json.dumps(response_data, indent=2)}")
            
            if "data" in response_data and "create_irrigation_program" in response_data["data"]:
                program_id = response_data["data"]["create_irrigation_program"]
                logger.info(f"Program created successfully with ID: {program_id}")
                return {
                    "program_id": program_id,
                    "controller_id": controller_id,
                    "farm_id": farm_id,
                    "area_id": area_id
                }
            else:
                raise ValueError("Invalid response format or program creation failed")
            
        except ValueError as e:
            logger.error(f"Error creating program: {e}")
            raise Exception(f"Failed to create program: {e}")
           
    def list_programs_irrigation_events(
        self,
        program_id: str
    ) -> List[Dict[str, Any]]:
        """
        List all irrigation events for a given program ID.
        
        Args:
            program_id (str): The ID of the irrigation program.
        
        Returns:
            List[Dict[str, Any]]: A list of irrigation events.
        """
        try:
            
            payload = get_payload_of_list_programs_irrigation_envents_api(program_id=program_id)
            logger.info(f"Payload for listing irrigation events: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                self.url,
                headers=self.headers,
                json=payload
            )
            
            response.raise_for_status()  # Raise an exception for bad status codes
            logger.info(f"Status code: {response.status_code}")
            
            response_data = response.json()
            logger.info(f"Response data: {json.dumps(response_data, indent=2)}")
            
            if "data" in response_data and "irrigation_events" in response_data["data"]:
                irrigation_events = response_data["data"]["irrigation_events"]
                logger.info(f"Found {len(irrigation_events)} irrigation events for program {program_id}")
                return irrigation_events   
            else:
                raise ValueError("Invalid response format or no irrigation events found")
            
        except Exception as e:
            logger.error(f"Error listing irrigation events for program {program_id}: {e}")
            raise Exception(f"Failed to list irrigation events: {e}")   
    
    
    def create_irrigation_events(
        self,
        program_id: str,
        area_id: str,
        dtstart: int,
        quantity: List[int],
        ph_setpoint: float,
        ec_setpoint: float,
        number_of_events: int = 1,
        irrigation_interval: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Create a new irrigation event for a given program ID.
        
        Args:
            program_id (str): The ID of the irrigation program.
            area_id (str): The ID of the irrigation area.
            dtstart (int): The start datetime in timestamp.
            quantity (List[int]): The quantity values for irrigation.
            ph_setpoint (float): The pH setpoint value.
            ec_setpoint (float): The EC setpoint value.
            number_of_events (int): Number of events to create. Default is 1.
            irrigation_interval (int): Interval between irrigation events in minutes. Default is 60 minutes.
        
        Returns:
            Dict[str, Any]: The response from the API.
        """
        
        try:
            responses = []
            for i in range(number_of_events):                
                    payload = get_payload_for_create_irrigation_event_api(
                        program_id=program_id,
                        area_id=area_id,
                        dtstart=dtstart,
                        quantity=quantity,
                        ph_setpoint=ph_setpoint,
                        ec_setpoint=ec_setpoint
                    )
                    logger.info(f"Payload for creating irrigation event: {json.dumps(payload, indent=2)}")
                    
                    response = requests.post(
                        self.url,
                        headers=self.headers,
                        json=payload
                    )
                    
                    response.raise_for_status()  # Raise an exception for bad status codes
                    logger.info(f"Status code: {response.status_code}")
                    
                    response_data = response.json()
                    logger.info(f"Response data: {json.dumps(response_data, indent=2)}")
                    
                    if "data" in response_data and "create_irrigation_event" in response_data["data"]:
                        event_id = response_data["data"]["create_irrigation_event"]
                        logger.info(f"Irrigation event created successfully with ID: {event_id}")
                        responses.append({
                            "program_id": program_id,
                            "dtstart": dtstart + i * irrigation_interval * 60,  # Increment start time for each event
                            "quantity": quantity,
                            "ph_setpoint": ph_setpoint,
                            "ec_setpoint": ec_setpoint
                        })
                    
            return responses
                
        except Exception as e:
            logger.error(f"Error creating irrigation event {i+1} for program {program_id}: {e}")
            raise Exception(f"Failed to create irrigation event: {e}")
        
        
# Test API
# api_handler = APIHandler()
# print(f"Token: {api_handler.token}")
# response = api_handler.create_program(farm_id="95c3d870-7fab-11ef-bfc9-113ee5630d77", area_id="16106380-f811-11ef-8831-112b9cc8d9f8")
# print(f"Program created: {response}")
# program_id = response.get("program_id")
# program_id = "fda5c0f0-5b5d-11f0-83a2-b5dfc26d8446"
# farm_id = "95c3d870-7fab-11ef-bfc9-113ee5630d77"
# area_id = "16106380-f811-11ef-8831-112b9cc8d9f8"

# from datetime import datetime
# events = api_handler.create_irrigation_events(
#     program_id=program_id,
#     area_id=area_id,
#     dtstart=int(datetime.now().timestamp()),  # Example timestamp
#     quantity=[180, 0, 0],  # Example quantities
#     ph_setpoint=5.1,
#     ec_setpoint=1.9,
#     number_of_events=10
# )

# print(events)
