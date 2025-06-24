from textwrap import dedent
from typing import Optional
from pydantic import BaseModel

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from db.session import db_url
from tools.tool import GetRecentIrrigationDataTool, GetCurrentEnviromentTool, GetWeatherForecastTool, GetLastIrrigationDataTool
from tools.sensor_manager import EnvironmentSensorData


class PlantOutput(BaseModel):
    time_waiting: int  # Recommended waiting time in minutes
    next_time_watering: str # Next irrigation time in ISO format
    reason: str  # Reasoning for the recommendation
    environ_sensor_data: EnvironmentSensorData  # Current environment sensor data

def get_plant_agent(
    model_id: str = "gpt-4.1",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = True,
) -> Agent:
    return Agent(
        name = "Plant Agent",
        agent_id = "plant_agent",
        user_id = user_id,
        session_id = session_id,
        model = OpenAIChat(id=model_id),
        description = dedent("""
            Agricultural expert with 20+ years of experience in analyzing and optimizing crop irrigation cycles to improve water efficiency, increase yields, and promote sustainable farming.              
        """),
        instructions = dedent("""🌱 **Plant Agent – Instructions (Optimized)**

## 🎯 Primary Goal
Adjust the waiting time (`T_chờ`) to bring the EC value closer to the target of **4.0**.

## 🧑‍🌾 Role
You are a precision agriculture AI agent specialized in irrigation optimization. Your task is to make data-driven decisions while ensuring crop health stability.

## 📥 Required Inputs & Tools
You will automatically retrieve:
- **last_reflection** *(from `GetLastIrrigationDataTool`)*
- **history_summary** *(from `GetRecentIrrigationDataTool`)*
- **current_env** *(from `GetCurrentEnviromentTool`)*
- **forecast** *(from `GetWeatherForecastTool`)*

## ⚖️ Important Rules
- **If EC > 4.0** → Decrease waiting time (irrigate earlier)
- **If EC < 4.0** → Increase waiting time (allow more evaporation)
- **Valid `T_chờ` range:** 60–300 minutes
- Adjust gradually (10–20 minutes per cycle)

## 📖 Procedure
1. Retrieve and review all input data.
2. Compare current EC with 4.0.
3. Adjust `T_chờ` by 10–20 minutes in appropriate direction, ensuring it stays within valid range.
4. Check forecast for upcoming weather extremes that could affect EC.
5. If EC data is unavailable or erratic, estimate adjustment based on historical trends and forecast.
6. Explain the reasoning behind your recommendation in 1-2 sentences."""),
        tools = [
            GetLastIrrigationDataTool(),
            GetRecentIrrigationDataTool(), 
            GetCurrentEnviromentTool(), 
            GetWeatherForecastTool()],
        add_datetime_to_instructions = True,
        response_model = PlantOutput,
        show_tool_calls = True,
        debug_mode = debug_mode
    )