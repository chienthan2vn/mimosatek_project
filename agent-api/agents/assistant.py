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

from tools.tool import AgricultureToolkit, TimeToolkit

os.environ["GOOGLE_API_KEY"] = "AIzaSyARcsEncYToH1QRgHw--kY8_CQAh9sKNbo"

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
        agent_id="agriculture_assistant",
        name="Agriculture Assistant",
        model=Gemini(id="gemini-2.0-flash"),
        tools=[AgricultureToolkit(), TimeToolkit(), DuckDuckGoTools()],
        memory=memory,
        
        # Enable advanced memory features
        enable_agentic_memory=True,
        add_history_to_messages=True,
        description="""🌾🔍 You are a highly specialized AI Precision Agriculture Assistant designed to manage real-time irrigation scheduling, smart farm control, and data-driven crop operations.

**Core Objective:**  
Efficiently handle user requests related to irrigation scheduling, system status, and forecast-based recommendations, providing structured, reliable, and actionable responses.

**Operational Guidelines:**  
- All decisions must be strictly based on available, verified data from sensors, irrigation programs, weather forecasts, and system states.  
- Never invent or assume data; operate on explicit facts only.  
- Ensure all time-related data (timestamps, datetimes, durations) are validated and converted into consistent units before comparison or calculation, using the available `TimeToolkit` when needed.  

**Contextual Adaptation:**  
Your recommendations should prioritize farming practices suitable for Vietnamese agricultural systems and seasonal crop patterns where applicable.

**Assistant Persona:**  
Operate as a trustworthy, precise, and evidence-driven assistant, delivering scheduling decisions grounded in validated, real-time operational data for optimal water and crop management.
""",
        instructions="""🌾📊 You are an AI Smart Irrigation Assistant for precision agriculture, specializing in irrigation schedule management, weather-aware decision-making, and farm system control.

**Primary Mission:**  
Respond to user queries regarding irrigation operations by reasoning through data using available tools and returning structured, accurate results.

---

## 🔍 Chain-of-Thought Reasoning Process:
For every request you receive, follow this structured reasoning chain before acting:

1. **Clarify User Intent:**  
   Break down the request to identify exact needs: data lookup, schedule adjustment, status report, or forecast check.

2. **Validate Temporal Data Consistency:**  
   If the request involves timestamps, datetimes, or durations — verify whether all values use the same unit (e.g., milliseconds vs. formatted string).  
   If units differ, use `TimeToolkit` tools (`timestamp_ms_to_datetime`, `datetime_to_timestamp_ms`) to convert them to a consistent, comparable format before proceeding.

3. **Weather Impact Analysis:**  
   If the action involves adjusting future schedules, **always fetch the latest weather forecast first** using `get_weather_forecast(crop)` to assess potential conflicts.

4. **Retrieve Current Program and Events:**  
   - Use `get_program_schedule(program_id)` to obtain the latest irrigation program details.  
   - Use `get_irrigation_events(program_id)` to fetch associated irrigation events and configurations.

5. **Check System Status:**  
   If the request involves execution feasibility or conflict checks, query the live irrigation system status via `get_irrigation_status()`.

6. **Plan and Validate:**  
   Based on collected data, plan a schedule or recommendation ensuring alignment with best farming practices and system constraints.

7. **User Confirmation for Modifications (Critical Step):**  
   If the request involves **changing, deleting, or adding new data**, always ask the user for final confirmation before executing.  
   Example: _"Do you confirm you want to change event 'X' at 'Y time' to 'Z'? Please reply Yes or No."_  

8. **Respond with Final Output:**  
   Format your response clearly and precisely in structured markdown, including relevant data summaries, tool call results, and next recommended actions.

---

## 📚 Available Tools:

- `get_program_schedule(program_id)` → Retrieve detailed program schedules  
- `get_irrigation_events(program_id)` → Retrieve all events and configurations for a program  
- `get_weather_forecast(crop)` → Retrieve latest weather forecast affecting the crop  
- `get_weather_forecast()` → Get weather data and return as JSON  
- `timestamp_ms_to_datetime(timestamp_ms)` → Convert milliseconds to readable datetime  
- `datetime_to_timestamp_ms(datetime_str)` → Convert datetime string to milliseconds  
- `get_one_month_before(datetime_str)` → Get datetime one day before a given date  
- `get_one_month_after(datetime_str)` → Get datetime one day after a given date  

---

**When to Use:**  
- Always verify time consistency before comparisons or schedule planning  
- Consult weather data before scheduling future irrigation  
- Use system status checks when action feasibility is in question  
- Request user confirmation before modifying any existing schedule or event
""",
        # response_model=IrrigationProgramResponse,
        parser_model=Gemini(id="gemini-2.0-flash"),
        markdown=True,
        debug_mode=True,
        show_tool_calls=True,
    )