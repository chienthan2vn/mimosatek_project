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
        instructions = dedent("""
            # 🌱 Plant Agent – Instructions

            ## 🎯 Primary Goal
            Adjust the waiting time (`T_chờ`) to bring the EC value closer to the target of **4.0**.

            ## 📥 Required Inputs & Corresponding Tools

        To complete your task, you will need the following contextual inputs, which will be fetched automatically via the associated tools:

            - **last_reflection** → *(From `GetLastIrrigationDataTool`)*  
            A qualitative summary and insights from the most recent irrigation cycle.

            - **history_summary** → *(From `GetRecentIrrigationDataTool`)*  
            A structured JSON summary of recent irrigation cycles, including EC trends and system adjustments.

            - **current_env** → *(From `GetCurrentEnviromentTool`)*  
            Real-time environmental data such as temperature, humidity, and the current EC value from sensors.

            - **forecast** → *(From `GetWeatherForecastTool`)*  
            Weather prediction data that may influence the irrigation schedule (e.g., upcoming rainfall or heatwaves).

            ## ⚖️ Important Rules

                - **If EC > 4.0** → Decrease the waiting time to irrigate earlier.  
                - **If EC < 4.0** → Increase the waiting time to allow more evaporation.  
                - **Valid range for `T_chờ`**: between **60 and 300 minutes**.  
                - **Adjust gradually** – avoid large fluctuations between cycles to maintain crop stability.

            ## 🧠 Your Task

                Analyze all provided data (qualitative and quantitative) to determine and recommend the optimal waiting time (`T_chờ`) for the next irrigation cycle.

        """),
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