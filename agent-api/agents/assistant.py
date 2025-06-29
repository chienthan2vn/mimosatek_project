from agno.agent import Agent
from agno.models.google import Gemini
from pydantic import BaseModel, Field
from typing import List, Optional
from agno.memory.v2.memory import Memory
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.storage.sqlite import SqliteStorage
from agno.tools.reasoning import ReasoningTools
from agno.tools.duckduckgo import DuckDuckGoTools
import os

from tools.tool import AgricultureToolkit

os.environ["GOOGLE_API_KEY"] = "AIzaSyDWhUlaOC1GRh0SFxbZ-v3VqE-EnstMZCc"

# Response Models
class NutrientsMixingProgram(BaseModel):
    name: str = Field(default="", description="Name of the mixing program. Fixed and unchangeable")
    mixing_type: int = Field(description="Type of mixing method. Fixed and unchangeable")
    ph_setpoint: float = Field(description="pH setpoint value. Fixed and unchangeable")
    ec_setpoint: float = Field(description="EC (Electrical Conductivity) setpoint value. Fixed and unchangeable")
    rates: List[float] = Field(description="List of nutrient rates. There are always 5 elements. Fixed and unchangeable")

    
class IrrigationProgramResponse(BaseModel):
    program_id: str = Field(default="", description="ID of the irrigation program")
    name: str = Field(description="Name of the irrigation event")
    area_id: str = Field(default="", description="ID of the irrigation area")
    strict_time: bool = Field(default=False, description="Whether timing is strict")
    dtstart: int = Field(description="Start datetime in timestamp")
    irrigation_method: int = Field(description="Irrigation method type")
    quantity: List[int] = Field(description="Quantity values for irrigation")
    recurrence: str = Field(description="Recurrence pattern for irrigation")
    nutrients_mixing_program: NutrientsMixingProgram = Field(description="Nutrients mixing configuration")



def get_assistant_agent(user_id: str = "default_user") -> Agent:
    """
    Create and return an instance of the Assistant Agent with long-term memory.
    
    Args:
        user_id (str): Unique identifier for the user to maintain separate memory contexts
    
    Returns:
        Agent: An instance of the Assistant Agent with configured tools and persistent memory.
    """
    db_file = "tmp/agent.db"
    
    # Long-term memory configuration for persistent learning
    memory = Memory(
        model=Gemini(id="gemini-2.0-flash"),
        db=SqliteMemoryDb(
            table_name=f"user_memories_{user_id}",
            db_file=db_file
        ),
    )

    # Create Agriculture Agent
    return Agent(
        name="Agriculture Assistant",
        model=Gemini(id="gemini-2.0-flash"),
        tools=[AgricultureToolkit(), DuckDuckGoTools()],
        memory=memory,
        
        # Enable advanced memory features
        enable_agentic_memory=True,
        add_history_to_messages=True,
        description="""
            🌱📊 You are an AI Precision Irrigation Assistant specializing in real-time irrigation scheduling, smart farm system control, and data-driven crop management.

            **Objective:**  
            Process all user requests related to irrigation operations (e.g. view, modify, or check schedules) and respond with a structured, up-to-date irrigation schedule object.

            **Operational Principles:**  
            - Always base your responses on verified, available data sources including live sensor readings, forecasted weather data, and current system states.
            - Never infer or fabricate information.
            - Use farm-specific practices optimized for Vietnamese crop systems and seasonal patterns where applicable.

            **Persona Commitment:**  
            - Operate as a reliable, data-driven, precision agriculture assistant.
            - Deliver precise, actionable, evidence-based scheduling decisions for optimal water and crop health management.""",
        instructions="""🌱📊 You are an AI Smart Irrigation Assistant specializing in precision agriculture scheduling and irrigation management.

            **Objective:**  
            Respond to any user request related to irrigation schedules by using available tools and data to generate accurate, structured irrigation schedules.

            ---

            **Critical Thinking Process:**  
            For each request, strictly follow this reasoning flow: 
            1. Detailed analysis of user requirements 
            2. Always check the weather forecast before planning any changes to your watering schedule.
            3. Analyze the current irrigation program and events via available tools
            4. Check system status and operational parameters  
            5. Validate all proposed schedules against local farming best practices  


            ---

            **Available Tools:**  
            - `get_program_schedule(program_id)` → Get latest schedule details  
            - `get_irrigation_events(program_id)` → Retrieve irrigation events and configurations  
            - `get_weather_forecast(crop)` → Get weather forecast
            - `get_irrigation_status()` → Fetch current system-wide irrigation status  

            **When to use:**  
            Use one or multiple tools as needed based on the specific request content.""",
        response_model=IrrigationProgramResponse,
        parser_model=Gemini(id="gemini-2.0-flash"),
        markdown=True,
        debug_mode=True,
        show_tool_calls=True,
    )