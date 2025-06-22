from textwrap import dedent
from typing import Optional
from pydantic import BaseModel

from agno.agent import Agent, AgentKnowledge
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.url import UrlKnowledge
from agno.memory.v2.db.postgres import PostgresMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.openai import OpenAIChat
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.vectordb.pgvector import PgVector, SearchType

from db.session import db_url
from tools.tool import GetRecentIrrigationDataTool, GetCurrentEnviromentTools, GetWeatherForecastTool, GetLastReflectionTools



class PlantOutput(BaseModel):
    time_waiting: int  # Recommended waiting time in minutes
    next_time_watering: str # Next irrigation time in ISO format
    reason: str  # Reasoning for the recommendation

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
            Adjust the waiting time (T_chờ) to bring the EC value closer to the target of **4.0**.

            ## 📥 Provided Data
            You are given the following contextual information:

            ### Reflection from the most recent irrigation cycle
            - **last_reflection**: Qualitative analysis and insights from the previous irrigation cycle

            ### Recent operational history
            - **history_summary**: JSON data containing recent irrigation cycles, EC values, and system performance metrics

            ### Current environmental data
            - **current_env**: JSON data with real-time sensor readings including temperature, humidity, and current EC levels

            ### Weather forecast
            - **forecast**: Weather prediction data that may affect irrigation planning

            ## ⚖️ Important Rules

            - **If EC > 4.0** → Decrease the waiting time to irrigate earlier
            - **If EC < 4.0** → Increase the waiting time to allow more evaporation
            - **Valid range for T_chờ**: from 60 to 300 minutes
            - **Adjust gradually** – avoid drastic changes between cycles

            ## 🧠 Your Task
            Based on both qualitative reflections and quantitative data, calculate and recommend the next waiting time (T_chờ) to help regulate EC toward the 4.0 target.
        """),
        tools = [GetLastReflectionTools(), GetRecentIrrigationDataTool(), GetCurrentEnviromentTools(), GetWeatherForecastTool()],
        add_datetime_to_instructions = True,
        response_model = PlantOutput,
        show_tool_calls = True,
        debug_mode = debug_mode
    )