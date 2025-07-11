import os
from textwrap import dedent
from agno.agent import Agent
from agno.models.google import Gemini
import json
import logging
import requests
from typing import List, Optional, Dict, Any

from tools.payload import (get_payload_of_create_program_api,
                           get_payload_of_list_programs_irrigation_envents_api,
                           get_payload_for_create_irrigation_event_api,
                           get_list_area_by_farm_api,
                           get_payload_for_controllers_api)

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
            
    # @staticmethod
    # def get_controller_id_by_farm_and_area_id(farm_id: str, area_id: str) -> Dict[str, Any]:
    #     """
    #     Get the controller ID based on farm and area IDs.
        
    #     Args:
    #         farm_id (str): The ID of the farm.
    #         area_id (str): The ID of the area.
        
    #     Returns:
    #         str: The controller ID.
    #     """

    #     #TODO: Implement the logic to retrieve the controller ID based on farm and area IDs.s
    #     try:
    #         return {
    #             "farm_id": farm_id,
    #             "area_id": area_id,
    #             "controller_id": "4034b240-6fc1-11ed-9cbe-f9420b7f5b37"  # Replace with actual logic to get controller ID
    #         }
    #     except Exception as e:
    #         logger.error(f"Error getting controller ID for farm {farm_id} and area {area_id}: {e}")
    #         raise Exception(f"Failed to get controller ID: {e}")

    def get_list_area_by_farm_api(self, farm_id: str) -> Dict[str, Any]:
        """
        Get a list of areas by farm ID.

        Args:
            farm_id (str): The ID of the farm.

        Returns:
            List[Dict[str, Any]]: A list of areas with their names and IDs.
        """
        try: 
            payload = get_list_area_by_farm_api(farm_id=farm_id)
            response = requests.post(
                self.url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            response_data = response.json()
            
            if "data" in response_data and "areas" in response_data["data"]:
                resp = []
                for i in response_data["data"]["areas"]:
                    area_info = {
                        "farm_id": farm_id,
                        "area_name": i["name"],
                        "area_id": i["id"]
                    }
                    resp.append(area_info)
                return resp
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
        except (KeyError, ValueError) as e:
            raise Exception(f"Failed to parse response: {e}")
        
    def create_program(
            self,
            controller_id: str,
        ) -> Dict[str, Any]:
        """
        Create a new irrigation program.
        
        Args:
            controller_id (str): The ID of the controller to create the program for.

        Returns:
            Dict[str, Any]: The response from the API.
        """
        try:
           
            # controller_info = APIHandler().get_controller_id_by_farm_and_area_id(farm_id=farm_id, area_id=area_id)
            # controller_id = controller_info.get("controller_id")
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

    def get_controllers_by_farm_id(self, farm_id: str) -> List[Dict[str, Any]]:
        """
        Get a list of controllers by farm ID.

        Args:
            farm_id (str): The ID of the farm.

        Returns:
            List[Dict[str, Any]]: A list of controllers with their detailed information.
        """
        try:
            payload = get_payload_for_controllers_api(farm_id=farm_id)
            logger.info(f"Payload for getting controllers: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                self.url,
                headers=self.headers,
                json=payload
            )
            
            response.raise_for_status()  # Raise an exception for bad status codes
            logger.info(f"Status code: {response.status_code}")
            
            response_data = response.json()
            # logger.info(f"Response data: {json.dumps(response_data, indent=2)}")
            
            if "data" in response_data and "controllers" in response_data["data"]:
                results = []
                controllers = response_data["data"]["controllers"]
                for controller in controllers:
                    controller_id = controller.get("id")
                    temp_data = {
                        "controller_id": controller_id,
                        "nodes": []
                    }
                    if controller_id:
                        for node in controller.get("nodes", []):
                            area_id = node.get("area_id")
                            area_name = node.get("area_name")
                            temp = {"area_id": area_id, "area_name": area_name}
                            temp_data["nodes"].append(temp)
                    results.append(temp_data)
                logger.info(f"Found {len(controllers)} controllers for farm {farm_id}")
                return results
            else:
                raise ValueError("Invalid response format or no controllers found")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise Exception(f"Request failed: {e}")
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to parse response: {e}")
            raise Exception(f"Failed to parse response: {e}")

    # def get_controller_id_and_area_info_by_farm_id(
    #     self,
    #     area_name: str,
    #     farm_id: str = "5c182350-1866-4c9f-ac68-2eb7e5336d1d",
    # ) -> Dict[str, Any]:
    #     """
    #     Get the controller ID and area id and area name by farm ID and area name.

    #     Args:
    #         area_name (str): The name of the irrigation area.
    #         farm_id (str): The ID of the farm. Default is "5c182350-1866-4c9f-ac68-2eb7e5336d1d".
        
    #     Returns:
    #         Dict[str, Any]: A dictionary containing the controller ID, area information by farm id and area name.
    #     """
    #     try:
    #         sub_agent = Agent(
    #             model=Gemini(id="gemini-2.5-flash"),
    #             name="get_controller_id_and_area_info",
    #             description="Get the controller ID and area id and area name by farm ID.",

    #         )
    #     except Exception as e:
    #         logger.error(f"Error getting controller ID and area info: {e}")
    #         raise Exception(f"Failed to get controller ID and area info: {e}")