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

    def get_program_schedule(self, before_days: int = -1, after_days: int = 1) -> Any:
        """
        Get a list of the program's current watering schedules from Mimosatek API.
        
        Args:     
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
                "program_id": "4c17ad40-54d6-11f0-83a2-b5dfc26d8446",
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
          
    def get_irrigation_events(self) -> Any:
        """
        Get list program's irrigation events and status from Mimosatek API.
            
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
                "program_id": "4c17ad40-54d6-11f0-83a2-b5dfc26d8446"
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
    
    def create_irrigation_event(self, dtstart: int, quantity: list = None, ec_setpoint: float = 1.9) -> dict:
        """
        Create irrigation event using Mimosatek API.
        
        Args:
            dtstart: Start timestamp in milliseconds
            quantity: List of irrigation duration values [seconds, minutes, hours]. Only the first index (seconds) is actively used for irrigation duration. Format: [seconds, minutes, hours] (default: [200, 0, 0] = 200 seconds)
            ec_setpoint: Electrical conductivity setpoint value (default: 1.9)
            
        Returns:
            dict: Response data containing event id and duration
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
        
        # Set default values
        if quantity is None:
            quantity = [200, 0, 0]
        
        # Build event object with direct values
        event = {
            "area_id": "16106380-f811-11ef-8831-112b9cc8d9f8",
            "name": "KV2",
            "strict_time": False,
            "dtstart": dtstart,
            "irrigation_method": 0,
            "quantity": quantity,
            "nutrients_mixing_program": {
                "name": "sos",
                "mixing_type": 1,
                "ph_setpoint": 5.1,
                "ec_setpoint": ec_setpoint,
                "rates": [3, 5, 0, 0, 5]
            },
            "recurrence": "INTERVAL=1;FREQ=DAILY;UNTIL=20260621T165959Z"
        }
        
        # Build payload with direct values
        payload = {
            "query": query,
            "variables": {
                "program_id": "4c17ad40-54d6-11f0-83a2-b5dfc26d8446",
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
                return response_data["data"]["create_irrigation_event"]
            else:
                raise ValueError("Invalid response format")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
        except (KeyError, ValueError) as e:
            raise Exception(f"Failed to parse response: {e}")

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
    
    def create_continuous_irrigation_schedule(self, dtstart: int, n: int = 1, quantity: list = None, ec_setpoint: float = 1.9) -> list:
        """
        Create multiple irrigation events for continuous irrigation schedule.
        
        Args:
            dtstart: Start timestamp in milliseconds for the first irrigation event
            n: Number of irrigation events to create (default: 1)
            quantity: List of irrigation duration values [seconds, minutes, hours]. Only the first index (seconds) is actively used for irrigation duration. Format: [seconds, minutes, hours] (default: [200, 0, 0] = 200 seconds)
            ec_setpoint: Electrical conductivity setpoint value (default: 1.9)
            
        Returns:
            list: List of created irrigation events with their IDs and durations
        """
        results = []
        interval_minutes = 60
        interval_ms = interval_minutes * 60 * 1000  # Convert minutes to milliseconds
        
        for i in range(n):
            # Calculate the dtstart for this iteration
            current_dtstart = dtstart + (i * interval_ms)
            
            try:
                # Create irrigation event using the existing method
                event_result = self.create_irrigation_event(
                    dtstart=current_dtstart,
                    quantity=quantity,
                    ec_setpoint=ec_setpoint
                )
                
                # Add additional info about the iteration
                event_result['iteration'] = i + 1
                event_result['dtstart'] = current_dtstart
                event_result['scheduled_time'] = datetime.fromtimestamp(current_dtstart / 1000).isoformat()
                
                results.append(event_result)
                
                # Log successful creation
                logger.info(f"Created irrigation event {i+1}/{n} at {event_result['scheduled_time']}")
                
            except Exception as e:
                # Log error and continue with next iteration
                error_result = {
                    'iteration': i + 1,
                    'dtstart': current_dtstart,
                    'scheduled_time': datetime.fromtimestamp(current_dtstart / 1000).isoformat(),
                    'error': str(e),
                    'status': 'failed'
                }
                results.append(error_result)
                logger.error(f"Failed to create irrigation event {i+1}/{n}: {e}")
        
        return results