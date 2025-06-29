import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any
from pydantic import BaseModel
from dataclasses import dataclass, asdict
import random
import psycopg2
from loguru import logger

class api_for_all:
    def __init__(self):
        pass

    def get_present_irrigation(self) -> Any:
        """
        Get the current irrigation status for a specific crop.
        """
        # Dữ liệu lịch tưới giả
        current_time = int(datetime.now().timestamp() * 1000)
        next_irrigation = current_time + (2 * 60 * 60 * 1000)  # 2 giờ sau
        
        irrigation_data = {
            "current_status": "active",
            "area_id": "AREA_001",
            "current_program": {
                "program_id": "PROG_" + str(random.randint(1000, 9999)),
                "event": {
                    "area_id": "AREA_001",
                    "name": "Morning Irrigation - Tomatoes",
                    "strict_time": True,
                    "dtstart": current_time,
                    "irrigation_method": 1,  # 0: sprinkler, 1: drip, 2: flood
                    "quantity": [150, 75, 0],  # [water, fertilizer, pesticide] in liters
                    "nutrients_mixing_program": {
                        "name": "Tomato Growth Mix",
                        "mixing_type": 1,
                        "ph_setpoint": 6.2,
                        "ec_setpoint": 2.1,
                        "rates": [2.5, 4.0, 1.2, 0.8, 3.5]  # N-P-K-Ca-Mg rates
                    },
                    "recurrence": "INTERVAL=1;FREQ=DAILY;UNTIL=20250730T180000Z"
                },
                "stored_as_template": True,
                "template_name": "Daily Tomato Care"
            },
            "next_irrigation": {
                "scheduled_time": next_irrigation,
                "area_id": "AREA_002", 
                "crop_type": "lettuce",
                "duration_minutes": 45
            },
            "system_health": {
                "pump_status": "operational",
                "water_pressure": "2.3 bar",
                "tank_level": "85%",
                "last_maintenance": "2025-06-25"
            }
        }
        
        return irrigation_data
    
    def get_weather_forecast(self, crop: str) -> Any:
        """
        Get the weather forecast for a specific crop.
        """
        # Dữ liệu thời tiết giả cho 7 ngày
        base_temp = random.randint(20, 30)
        
        forecast_data = {
            "crop": crop,
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
            "irrigation_recommendations": {
                "water_needs": "medium",
                "best_irrigation_times": ["06:00-08:00", "17:00-19:00"],
                "avoid_irrigation": False,
                "special_notes": f"Thời tiết thuận lợi cho {crop}. Tưới đều đặn vào sáng sớm."
            }
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
                "irrigation_advice": random.choice([
                    "Tưới bình thường", "Giảm lượng nước", "Tăng lượng nước", 
                    "Tạm dừng tưới", "Tưới sáng sớm", "Kiểm tra độ ẩm đất"
                ])
            }
            forecast_data["daily_forecast"].append(day_data)
        
        # Lời khuyên cụ thể theo loại cây
        crop_specific_advice = {
            "tomato": "Cà chua cần độ ẩm ổn định, tránh tưới lá để phòng bệnh.",
            "lettuce": "Rau xà lách cần đất luôn ẩm nhưng không úng nước.",
            "rice": "Lúa cần ngập nước trong giai đoạn sinh trưởng.",
            "corn": "Ngô cần nhiều nước trong giai đoạn tằm hoa.",
            "pepper": "Ớt cần tưới đều đặn, tránh khô hạn và úng nước."
        }
        
        forecast_data["crop_advice"] = crop_specific_advice.get(
            crop.lower(), 
            f"Theo dõi độ ẩm đất và tưới phù hợp với nhu cầu của {crop}."
        )
        
        return forecast_data