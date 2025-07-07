import os
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any
from pydantic import BaseModel
from dataclasses import dataclass, asdict
import random
import psycopg2
from loguru import logger
from tools.utils import TimeConverter
import openmeteo_requests
import requests_cache
from retry_requests import retry
import pandas as pd
from datetime import datetime, timezone

class api_for_all:
    def __init__(self):
        self.token = self.get_token()
        self.time_converter = TimeConverter()

    def get_token(self) -> str:
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

    def get_controller_id_by_farm(self) -> Dict[str, Any]:
        """
        Get the controller ID.

        Returns:
            str: The controller ID.
        """
        farm_id = "3a63be60-6fc1-11ed-9cbe-f9420b7f5b37"
        #TODO: Implement the logic to retrieve the controller ID based on farm and area IDs.s
        try:
            return {
                "farm_id": farm_id,
                "controller_id": "4034b240-6fc1-11ed-9cbe-f9420b7f5b37"  # Replace with actual logic to get controller ID
            }
        except Exception as e:
            logger.error(f"Error getting controller ID for farm {farm_id}: {e}")
            raise Exception(f"Failed to get controller ID: {e}")

    def get_program_schedule(self, program_id: str, before_days: int = -1, after_days: int = 1) -> Any:
        """
        Get a list of the program's current watering schedules from Mimosatek API.
        
        Args:
            program_id: The ID of the irrigation program
            before_days: Number of days before the current date to include in the schedule
            after_days: Number of days after the current date to include in the schedule
            
        Returns:
            dict: Program schedule data
        """
        url = "https://demo.mimosatek.com/api/monitor"

        # GraphQL query for program schedule
        query = """
            query Program_schedule ($program_id: ID!, $start: Float!, $end: Float!) {
                program_schedule(program_id: $program_id, start: $start, end: $end) {
                    area_id
                    area_name
                    event_id
                    event_name
                    ts
                    duration
                    activity_type
                    irrigation_method
                    event {
                        id
                        name
                        area_id
                        strict_time
                        dtstart
                        irrigation_method
                        quantity
                        recurrence
                    }
                }
            }
        """
        start = self.time_converter.datetime_to_timestamp_ms(self.time_converter.get_other_days(days=before_days))
        end = self.time_converter.datetime_to_timestamp_ms(self.time_converter.get_other_days(days=after_days))
        payload = {
            "query": query,
            "variables": {
                "program_id": program_id,
                "start": float(start),
                "end": float(end)
            }
        }
        
        headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
            'authorization': self.token,
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            response_data = response.json()
            
            if "data" in response_data and "program_schedule" in response_data["data"]:
                # print(response_data["data"]["program_schedule"])
                return response_data["data"]["program_schedule"]
            else:
                raise ValueError("Invalid response format")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
        except (KeyError, ValueError) as e:
            raise Exception(f"Failed to parse response: {e}")

    def get_irrigation_events(self, program_id: str) -> Any:
        """
        Get list program's irrigation events and status from Mimosatek API.

        Args:
            program_id: The ID of the irrigation program

        Returns:
            Dict containing irrigation events data
        """
        url = "https://demo.mimosatek.com/api/monitor"
        
        # GraphQL query for irrigation events
        query = """
            query Irrigation_events ($program_id: ID!) {
                irrigation_events(program_id: $program_id) {
                    id
                    name
                    area_id
                    strict_time
                    dtstart
                    irrigation_method
                    quantity
                    recurrence
                    nutrients_mixing_program {
                        name
                        mixing_type
                        rates
                        ph_setpoint
                        ec_setpoint
                    }
                }
            }
        """
        
        payload = {
            "query": query,
            "variables": {
                "program_id": program_id
            }
        }
        
        headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
            'authorization': self.token,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            response_data = response.json()
        
            if "data" in response_data and "irrigation_events" in response_data["data"]:
                # print(response_data["data"]["irrigation_events"])
                return response_data["data"]["irrigation_events"]
            else:
                raise ValueError("Invalid response format")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
        except (KeyError, ValueError) as e:
            raise Exception(f"Failed to parse response: {e}")

    def create_irrigation_event(self, program_id: str, dtstart: int, interval_minutes: int = 60, n: int = 1, quantity_second: int = 200, ec_setpoint: float = 1.9, ph_setpoint: float = 5.1) -> Any:
        """
        Create irrigation event(s) using Mimosatek API.
        
        Args:
            program_id: The ID of the irrigation program to create events for
            dtstart: Start timestamp in milliseconds for the first irrigation event (default: current time)
            interval_minutes: Interval in minutes between events (default: 60)
            n: Number of irrigation events to create (default: 1)
            quantity_second: Irrigation duration in seconds (default: 200)
            ec_setpoint: Electrical conductivity setpoint value (default: 1.9)
            ph_setpoint: pH setpoint value (default: 5.1)

        Returns:
            dict or list: Single event dict if n=1, list of events if n>1
        """
        url = "https://demo.mimosatek.com/api/monitor"
        
        # GraphQL mutation for creating irrigation event
        query = """
            mutation create_irrigation_event(
                $program_id: ID!
                $event: InputIrrigationEvent!
                $stored_as_template: Boolean
                $template_name: String
            ) {
                create_irrigation_event(
                    program_id: $program_id
                    event: $event
                    stored_as_template: $stored_as_template
                    template_name: $template_name
                ) {
                    id
                    duration
                }
            }
        """
            
        results = []
        interval_ms = interval_minutes * 60 * 1000  # Convert minutes to milliseconds
        
        for i in range(n):
            # Calculate the dtstart for this iteration
            current_dtstart = dtstart + (i * interval_ms)
            
            # Build event object with direct values
            area_id = "16106380-f811-11ef-8831-112b9cc8d9f8" 
            area_name = "Test Event" 
            event = {
                "area_id": area_id,
                "name": area_name,
                "strict_time": False,
                "dtstart": current_dtstart,
                "irrigation_method": 0,
                "quantity": [quantity_second, 0, 0],
                "nutrients_mixing_program": {
                    "name": "",
                    "mixing_type": 1,
                    "ph_setpoint": ph_setpoint,
                    "ec_setpoint": ec_setpoint,
                    "rates": [3, 5, 0, 0, 5]
                },
                "recurrence": "INTERVAL=1;FREQ=DAILY;UNTIL=20260621T165959Z"
            }
            
            # Build payload with direct values
            payload = {
                "query": query,
                "variables": {
                    "program_id": program_id,
                    "event": event,
                    "stored_as_template": False,
                    "template_name": ""
                }
            }
            
            headers = {
                'accept': '*/*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
                'authorization': self.token,
                'Content-Type': 'application/json'
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                response_data = response.json()
                
                if "data" in response_data and "create_irrigation_event" in response_data["data"]:
                    event_result = response_data["data"]["create_irrigation_event"]
                    
                    # Add additional info about the iteration (only if n > 1)
                    if n > 1:
                        event_result['iteration'] = i + 1
                        event_result['dtstart'] = current_dtstart
                        event_result['scheduled_time'] = datetime.fromtimestamp(current_dtstart / 1000).isoformat()
                        logger.info(f"Created irrigation event {i+1}/{n} at {event_result['scheduled_time']}")
                    
                    results.append(event_result)
                else:
                    raise ValueError("Invalid response format")
                    
            except requests.exceptions.RequestException as e:
                if n > 1:
                    # Log error and continue with next iteration for multiple events
                    error_result = {
                        'iteration': i + 1,
                        'dtstart': current_dtstart,
                        'scheduled_time': datetime.fromtimestamp(current_dtstart / 1000).isoformat(),
                        'error': str(e),
                        'status': 'failed'
                    }
                    results.append(error_result)
                    logger.error(f"Failed to create irrigation event {i+1}/{n}: {e}")
                else:
                    # For single event, raise the exception
                    raise Exception(f"Request failed: {e}")
            except (KeyError, ValueError) as e:
                if n > 1:
                    # Log error and continue with next iteration for multiple events
                    error_result = {
                        'iteration': i + 1,
                        'dtstart': current_dtstart,
                        'scheduled_time': datetime.fromtimestamp(current_dtstart / 1000).isoformat(),
                        'error': str(e),
                        'status': 'failed'
                    }
                    results.append(error_result)
                    logger.error(f"Failed to create irrigation event {i+1}/{n}: {e}")
                else:
                    # For single event, raise the exception
                    raise Exception(f"Failed to parse response: {e}")
        
        # Return single event if n=1, list if n>1
        return results[0] if n == 1 else results

    def get_weather_forecast(self) -> Dict[str, Any]:
        """
        Get weather data from Open-Meteo API and return as JSON
            
        Returns:
            dict: Weather data in JSON format
        """
        try:
            latitude=11.74
            longitude=108.37
            # Setup the Open-Meteo API client with cache and retry on error
            cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
            retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
            openmeteo = openmeteo_requests.Client(session=retry_session)

            # Make sure all required weather variables are listed here
            url = "https://api.open-meteo.com/v1/forecast"
            start_date = datetime.now().strftime('%Y-%m-%d')
            end_date = (datetime.now() + pd.DateOffset(days=1)).strftime('%Y-%m-%d')
            
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation_probability", 
                        "apparent_temperature", "et0_fao_evapotranspiration", "rain", "visibility"],
                "models": "best_match",
                "timezone": "Asia/Bangkok",
                "start_date": start_date,
                "end_date": end_date
            }
            responses = openmeteo.weather_api(url, params=params)

            # Process first location
            response = responses[0]
            
            # Process hourly data
            hourly = response.Hourly()
            hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
            hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
            hourly_precipitation_probability = hourly.Variables(2).ValuesAsNumpy()
            hourly_apparent_temperature = hourly.Variables(3).ValuesAsNumpy()
            hourly_et0_fao_evapotranspiration = hourly.Variables(4).ValuesAsNumpy()
            hourly_rain = hourly.Variables(5).ValuesAsNumpy()
            hourly_visibility = hourly.Variables(6).ValuesAsNumpy()

            # Create date range
            date_range = pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left"
            )

            # Build response data
            weather_data = {
                "location": {
                    "latitude": float(response.Latitude()),
                    "longitude": float(response.Longitude()),
                    "elevation": float(response.Elevation()),
                    "timezone": str(response.Timezone())
                },
                "forecast": []
            }

            # Convert numpy arrays to lists and combine with dates
            for i, date in enumerate(date_range):
                if i < len(hourly_temperature_2m):
                    def safe_float_convert(value):
                        """Safely convert numpy value to float or return None"""
                        try:
                            if pd.isna(value) or value is None:
                                return None
                            return float(value)
                        except (ValueError, TypeError):
                            return None
                    
                    weather_data["forecast"].append({
                        "datetime": date.isoformat(),
                        "temperature_2m": safe_float_convert(hourly_temperature_2m[i]),
                        "relative_humidity_2m": safe_float_convert(hourly_relative_humidity_2m[i]),
                        "precipitation_probability": safe_float_convert(hourly_precipitation_probability[i]),
                        "apparent_temperature": safe_float_convert(hourly_apparent_temperature[i]),
                        "et0_fao_evapotranspiration": safe_float_convert(hourly_et0_fao_evapotranspiration[i]),
                        "rain": safe_float_convert(hourly_rain[i]),
                        "visibility": safe_float_convert(hourly_visibility[i])
                    })

            return weather_data

        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def get_list_area_by_farm(self, farm_id: str) -> Any:
        """
        Get list of areas for a specific farm from Mimosatek API.
        
        Args:
            farm_id: The ID of the farm to get areas for
            
        Returns:
            dict: List of areas data including plant information
        """
        url = "https://demo.mimosatek.com/api/monitor"
        
        # GraphQL query for areas by farm
        query = """
            query areas($farm_id: ID!) {
                areas(farm_id: $farm_id) {
                    id
                    name
                    start_at
                    end_at
                    latest_signal_at
                    irrigation_recommendations_system
                    plant {
                        name
                        code
                        type
                    }
                }
            }
        """
        
        payload = {
            "query": query,
            "variables": {
                "farm_id": farm_id
            }
        }
        
        headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
            'authorization': self.token,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
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
            else:
                raise ValueError("Invalid response format")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
        except (KeyError, ValueError) as e:
            raise Exception(f"Failed to parse response: {e}")
    
    def create_program(self, controller_id: str) -> Any:
        """
        Create a new irrigation program using Mimosatek API.
        
        Args:
            controller_id: The ID of the controller to create the program for
            
        Returns:
            dict: Response data from program creation
        """
        url = "https://demo.mimosatek.com/api/monitor"
        
        # GraphQL mutation for creating irrigation program
        query = """
            mutation Create_irrigation_program ($controller_id: ID!, $name: String!) {
                create_irrigation_program(controller_id: $controller_id, name: $name)
            }
        """
        
        name = "irrigation program_" + str(int(time.time()))
        payload = {
            "query": query,
            "variables": {
                "controller_id": controller_id,
                "name": name
            }
        }
        
        headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
            'authorization': self.token,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            response_data = response.json()
            
            if "data" in response_data and "create_irrigation_program" in response_data["data"]:
                return {"program_id": response_data["data"]["create_irrigation_program"]}
            else:
                raise ValueError("Invalid response format")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
        except (KeyError, ValueError) as e:
            raise Exception(f"Failed to parse response: {e}")

