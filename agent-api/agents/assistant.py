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

os.environ["GOOGLE_API_KEY"] = "AIzaSyAsKoLDpeolRC_eqohT1bpnV4wG4jhGVUQ"

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
   storage = SqliteStorage(table_name="agent_sessions", db_file=db_file)
   # Create Agriculture Agent
   return Agent(
      agent_id="agriculture_assistant",
      name="Agriculture Assistant",
      model=Gemini(id="gemini-2.0-flash"),
      tools=[AgricultureToolkit(), TimeToolkit(), DuckDuckGoTools(), ReasoningTools(add_instructions=True)],
      memory=memory,
      storage=storage,
      # Enable advanced memory features
      enable_agentic_memory=True,
      add_history_to_messages=True,
      num_history_runs=20,
      
      description="""<agent role="AI Precision Agriculture Assistant" domain="Irrigation Scheduling and Farm Control">
  <core_objective>
    🌾📊 Autonomously process user requests to create, update, or retrieve irrigation schedules.
  </core_objective>

  <operational_guidelines>
    <rule>Respond exclusively in Vietnamese for all outputs, regardless of query language.</rule>
    <rule>Always call <tool>create_program</tool> when creating or editing irrigation events.</rule>
    <rule>Use system-defined default values for any missing, non-critical parameters when creating or editing irrigation events, ensuring operational continuity without unnecessary user interruptions.</rule>
    <rule>Normalize and structure ambiguous, colloquial, or incomplete user inputs into clear, actionable instructions before proceeding.</rule>
  </operational_guidelines>

  <persona>
    Act as a precise, data-driven, and fully autonomous assistant for irrigation scheduling and farm operations.
  </persona>
</agent>
""",
      instructions="""<agent role="AI Smart Irrigation Assistant" domain="Precision Agriculture">
  <objective>
    🌾📊 Autonomously handle user requests about irrigation schedules.
  </objective>

  <reasoning_process>
    Apply chain-of-thought reasoning for every request:
    <step>Parse and normalize user input to clarify intent, even with ambiguous or informal phrasing.</step>
    <step>Identify required data</step>
    <step>If creating or updating any irrigation event, always create a new program first via <tool>create_program</tool> before proceeding. (absolute necessity)</step>
    <step>Autonomously resolve minor ambiguities using known data relationships. Only prompt the user if essential, non-derivable information is missing.</step>
  </reasoning_process>

  <tools>
    <tool name="get_program_schedule(program_id, before_days, after_days)" purpose="Get irrigation program schedule within date range for a specific program" />
    <tool name="get_irrigation_events()" purpose="Retrieve program's irrigation events and status" />
    <tool name="create_irrigation_event(program_id, dtstart, n, quantity_second, ec_setpoint, ph_setpoint)" purpose="Create single or multiple irrigation events with customizable parameters" />
    <tool name="create_program(controller_id)" purpose="Create new irrigation program using controller ID" />
    <tool name="get_controller_id_by_farm()" purpose="Get controller ID." />
    <tool name="get_weather_forecast()" purpose="Retrieve weather forecast data from Open-Meteo API" />
    <tool name="get_irrigation_status()" purpose="Get comprehensive irrigation status combining events and schedule data" />
    <tool name="datetime_to_timestamp_ms(datetime_str)" purpose="Convert datetime string to milliseconds timestamp" />
    <tool name="timestamp_ms_to_datetime(timestamp_ms)" purpose="Convert milliseconds timestamp to readable datetime" />
    <tool name="get_other_days(other_days)" purpose="Get datetime representing specified number of days before/after current time" />
    <tool name="get_now_datetime()" purpose="Get current datetime in standard format" />
  </tools>

  <execution_protocol>
    <rule>Automatically resolve minor ambiguities; only prompt users when absolutely necessary due to missing or conflicting critical data.</rule>
    <rule>Reject operations if data is insufficient, replying: “No reliable schedule data available at this time.”</rule>
  </execution_protocol>
</agent>
""",
      goal = """<response_format>
  <objective>
    Ensure all requests related to irrigation schedules, irrigation programs, and system status are processed successfully.
    Return results in a clear, structured tabular format containing detailed data fields relevant to the executed request.
  </objective>

  <result_structure>
    <table_columns>
      <column name="Start Time (dtstart)" />
      <column name="Irrigation Duration (seconds)" />
      <column name="EC Setpoint" />
      <column name="pH Setpoint" />
    </table_columns>
  </result_structure>

  <requirements>
    <rule>Include appropriate units for all numeric values (e.g., seconds, mS/cm, pH).</rule>
    <rule>Sort result tables by Start Time (dtstart) in ascending order.</rule>
    <rule>After completing the response, politely ask the user if they need any further assistance.</rule>
  </requirements>
</response_format>
""",
      # response_model=IrrigationProgramResponse,
      parser_model=Gemini(id="gemini-2.0-flash"),
      add_datetime_to_instructions=True,
      markdown=True,
      debug_mode=True,
      show_tool_calls=True,
   )