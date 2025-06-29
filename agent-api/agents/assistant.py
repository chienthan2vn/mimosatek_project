from agno.agent import Agent
from agno.models.google import Gemini
from agno.memory.v2.memory import Memory
from agno.tools.googlesearch import GoogleSearchTools
from pydantic import BaseModel, Field
from typing import List, Optional
from agno.memory.v2.db.sqlite import SqliteMemoryDb
import os

from tools.tool import AgricultureToolkit

os.environ["GOOGLE_API_KEY"] = "AIzaSyDWhUlaOC1GRh0SFxbZ-v3VqE-EnstMZCc"

# Response Models
class NutrientsMixingProgram(BaseModel):
    name: str = Field(default="", description="Name of the mixing program")
    mixing_type: int = Field(description="Type of mixing method")
    ph_setpoint: float = Field(description="pH setpoint value")
    ec_setpoint: float = Field(description="EC (Electrical Conductivity) setpoint value")
    rates: List[float] = Field(description="List of nutrient rates")

class IrrigationEvent(BaseModel):
    area_id: str = Field(default="", description="ID of the irrigation area")
    name: str = Field(description="Name of the irrigation event")
    strict_time: bool = Field(default=False, description="Whether timing is strict")
    dtstart: int = Field(description="Start datetime in timestamp")
    irrigation_method: int = Field(description="Irrigation method type")
    quantity: List[int] = Field(description="Quantity values for irrigation")
    nutrients_mixing_program: NutrientsMixingProgram = Field(description="Nutrients mixing configuration")
    recurrence: str = Field(description="Recurrence pattern for irrigation")

class IrrigationProgramResponse(BaseModel):
    program_id: str = Field(default="", description="ID of the irrigation program")
    event: IrrigationEvent = Field(description="Irrigation event details")
    stored_as_template: bool = Field(default=False, description="Whether stored as template")
    template_name: str = Field(default="", description="Template name if applicable")


def get_assistant_agent() -> Agent:
    """
    Create and return an instance of the Assistant Agent.
    
    Returns:
        Agent: An instance of the Assistant Agent with configured tools and memory.
    """
    memory = Memory(
        # Use any model for creating and managing memories
        model=Gemini(id="gemini-2.0-flash"),
        db=SqliteMemoryDb(table_name="user_memories", db_file="tmp/agent.db"),
        delete_memories=True,
        clear_memories=True,
    )

    # Create Agriculture Agent
    return Agent(
        name="Agriculture Assistant",
        model=Gemini(id="gemini-2.0-flash"),
        tools=[AgricultureToolkit()],
        memory=memory,
        description="""
        I am an AI Agriculture Assistant specialized in precision irrigation management and smart farming.
        
        My core capabilities include:
        🌱 Real-time irrigation system monitoring and control
        🌤️ Weather-based crop management recommendations  
        📊 Data-driven irrigation scheduling optimization
        🔧 Agricultural system diagnostics and troubleshooting
        
        I provide evidence-based agricultural guidance using real-time sensor data and meteorological information.
        """,
        instructions=[
            # Critical Thinking & Analysis Framework
            "CRITICAL THINKING PROCESS: Before making any recommendation, I must:",
            "1. ANALYZE the current situation using available tools and data",
            "2. EVALUATE multiple factors: crop type, growth stage, weather, soil conditions",
            "3. SYNTHESIZE information from different sources to form comprehensive insights",
            "4. VALIDATE recommendations against agricultural best practices",
            
            # Tool Usage Guidelines
            "TOOL USAGE PROTOCOLS:",
            "• get_irrigation_status(): Use FIRST to understand current system state",
            "  - Analyzes: pump status, water levels, active programs, system health",
            "  - Returns: Complete irrigation system snapshot with operational data",
            "  - When to use: Always check before making irrigation changes",
            
            "• get_weather_forecast(crop): Use to get crop-specific weather insights",
            "  - Requires: Specific crop name (e.g., 'tomato', 'lettuce', 'rice')",
            "  - Returns: 7-day forecast with irrigation recommendations",
            "  - When to use: For scheduling, risk assessment, water planning",
            
            # Output Parsing & Response Structure
            "RESPONSE STRUCTURE REQUIREMENTS:",
            "• Always structure responses in the IrrigationProgramResponse format",
            "• Generate realistic program_id using format: PROG_YYYY_XXXX",
            "• Set appropriate irrigation_method: 0=sprinkler, 1=drip, 2=flood",
            "• Calculate quantity array: [water_liters, fertilizer_ml, pesticide_ml]",
            "• Use valid recurrence patterns: FREQ=DAILY/WEEKLY;INTERVAL=X;UNTIL=date",
            
            # Decision Making Logic
            "DECISION MAKING CRITERIA:",
            "• Water quantity based on: crop type + weather + soil moisture + growth stage",
            "• pH range: 5.5-7.0 (adjust based on crop requirements)",
            "• EC levels: 1.2-2.5 mS/cm (vary by crop nutrient needs)",
            "• Timing: Avoid midday heat, prefer early morning (6-8 AM) or evening (5-7 PM)",
            
            # Error Prevention & Validation
            "VALIDATION CHECKS:",
            "• Verify all required fields are populated with realistic values",
            "• Cross-check weather conditions before scheduling irrigation",
            "• Ensure nutrient mixing ratios are within safe agricultural ranges",
            "• Validate recurrence patterns match Vietnamese farming practices",
            
            # Communication Standards
            "COMMUNICATION GUIDELINES:",
            "• Explain reasoning behind recommendations clearly",
            "• Provide specific, actionable advice with measurable parameters",
            "• Include warnings for potential risks or adverse conditions",
            "• Use Vietnamese agricultural terminology when appropriate",
            "• Always justify irrigation schedules with data-driven reasoning"
        ],
        response_model=IrrigationProgramResponse,
        markdown=True,
        debug_mode=True,
        show_tool_calls=True,
    )