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

class api_for_all:
    def __init__(self):
        self.token = self.get_token()

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
    
    def get_program_schedule(self, program_id: str = "4c17ad40-54d6-11f0-83a2-b5dfc26d8446") -> dict:
        """
        Get program schedule from Mimosatek API.
        
        Args:
            token: Authentication token
            program_id: ID of the program
            start: Start timestamp in milliseconds
            end: End timestamp in milliseconds
            
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
        start = TimeConverter.datetime_to_timestamp_ms(TimeConverter.get_one_month_before())
        end = TimeConverter.datetime_to_timestamp_ms(TimeConverter.get_one_month_after())
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
                return response_data["data"]["program_schedule"][-1]
            else:
                raise ValueError("Invalid response format")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
        except (KeyError, ValueError) as e:
            raise Exception(f"Failed to parse response: {e}")
          
    def get_irrigation_events(self, program_id: str = "4c17ad40-54d6-11f0-83a2-b5dfc26d8446") -> Any:
        """
        Get list program's irrigation events and status from Mimosatek API.

        Args:
            token: Authentication token (if None, will get new token)
            program_id: ID of the irrigation program
            
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
                return response_data["data"]["irrigation_events"][-1]
            else:
                raise ValueError("Invalid response format")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
        except (KeyError, ValueError) as e:
            raise Exception(f"Failed to parse response: {e}")
    
    def get_weather_forecast(self) -> Any:
        """
        Get the weather forecast for a specific crop.
        """
        # Dữ liệu thời tiết giả cho 7 ngày
        base_temp = random.randint(20, 30)
        
        forecast_data = {
            "location": "Đồng bằng sông Cửu Long",
            "forecast_period": "7 days",
            "current_conditions": {
                "temperature": base_temp + random.randint(-3, 3),
                "humidity": random.randint(60, 85),
                "wind_speed": round(random.uniform(5.0, 15.0), 1),
                "pressure": random.randint(1010, 1025),
                "uv_index": random.randint(6, 11),
                "soil_moisture": random.randint(40, 70)
            },
            "daily_forecast": [],
        }
        
        # Tạo dự báo 7 ngày
        for i in range(7):
            day_data = {
                "date": (datetime.now().timestamp() + (i * 24 * 60 * 60)) * 1000,
                "day_name": ["Hôm nay", "Ngày mai", "Thứ ba", "Thứ tư", "Thứ năm", "Thứ sáu", "Chủ nhật"][i],
                "temperature": {
                    "min": base_temp + random.randint(-5, 0),
                    "max": base_temp + random.randint(0, 8),
                    "avg": base_temp + random.randint(-2, 4)
                },
                "humidity": random.randint(55, 90),
                "precipitation": {
                    "probability": random.randint(0, 80),
                    "amount": round(random.uniform(0, 25.0), 1)
                },
                "wind": {
                    "speed": round(random.uniform(3.0, 18.0), 1),
                    "direction": random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"])
                },
                "conditions": random.choice([
                    "sunny", "partly_cloudy", "cloudy", "light_rain", 
                    "moderate_rain", "thunderstorm", "overcast"
                ]),
            }
            forecast_data["daily_forecast"].append(day_data)
        
        return forecast_data