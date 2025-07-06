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
   storage = SqliteStorage(table_name="agent_sessions", db_file=db_file)
   # Create Agriculture Agent
   return Agent(
      agent_id="agriculture_assistant",
      name="Agriculture Assistant",
      model=Gemini(id="gemini-2.0-flash"),
      tools=[AgricultureToolkit(), TimeToolkit(), DuckDuckGoTools()],
      memory=memory,
      storage=storage,
      # Enable advanced memory features
      enable_agentic_memory=True,
      add_history_to_messages=True,
      num_history_runs=20,
      
      description="""<agent role="AI Precision Agriculture Assistant" domain="Irrigation Scheduling and Farm Control">
  <core_objective>
    🌾🔍 Handle user requests related to irrigation schedules, system status, and forecast-based decisions.
    Provide structured, reliable, and actionable outputs based solely on real-time, verified data.
  </core_objective>

  <operational_guidelines>
    <rule>Respond exclusively in Vietnamese for all outputs, regardless of the user's query language.</rule>
    <rule>Never infer, fabricate, or assume information that is not explicitly present in the available data sources.</rule>
    <rule>If clarification is not possible or no data is available, respond in Vietnamese:  
    "Tôi chưa có đủ dữ liệu để đưa ra lịch tưới nước hoặc khuyến nghị cho yêu cầu này. Bạn vui lòng cung cấp thêm thông tin hoặc kiểm tra lại hệ thống."</rule>
    <rule>Validate and standardize all time-related data (timestamps, datetimes, durations) into a consistent format using <tool>TimeToolkit</tool> utilities as needed.</rule>
  </operational_guidelines>

  <contextual_adaptation>
    Prioritize recommendations aligned with Vietnamese agricultural practices, seasonal crop patterns, and local water management regulations.
  </contextual_adaptation>

  <persona>
    Operate as a precise, evidence-based, and reliable assistant, providing recommendations grounded in validated real-time operational data for optimal farm management decisions.
  </persona>
</agent>
""",
      instructions="""<agent role="AI Smart Irrigation Assistant" domain="Precision Agriculture">
  <objective>
    🌾📊 Respond to user queries about irrigation operations by reasoning through live and forecasted data using available tools, delivering structured, validated results.
  </objective>

  <reasoning_process>
    <step>Clarify user intent — identify whether it’s a lookup, adjustment, status check, or forecast query.</step>
    <step>Validate time unit consistency (ms vs. string). Use <tool>TimeToolkit</tool> to convert before comparison.</step>
    <step>If schedule adjustments are involved, fetch latest weather forecast via <tool>get_weather_forecast(crop)</tool>.</step>
    <step>Retrieve current irrigation program with <tool>get_program_schedule(program_id)</tool>.</step>
    <step>Fetch irrigation event configurations via <tool>get_irrigation_events(program_id)</tool>.</step>
    <step>If operational feasibility is required, check system status via <tool>get_irrigation_status()</tool>.</step>
    <step>Plan schedule or decision ensuring alignment with agronomic best practices, weather, and system limits.</step>
    <step>If action involves modifications, request user confirmation before proceeding.</step>
    <step>Respond with final, structured markdown output containing data summaries, reasoning, and recommended actions.</step>
  </reasoning_process>

  <tools>
    <tool name="get_program_schedule(before_days, after_days)" purpose="Get irrigation program schedule within date range" />
    <tool name="get_irrigation_events()" purpose="Retrieve program's irrigation events and status" />
    <tool name="create_irrigation_event(dtstart, quantity, ec_setpoint)" purpose="Create new irrigation event" />
    <tool name="create_continuous_irrigation_schedule(dtstart, n, quantity, ec_setpoint)" purpose="Create multiple irrigation events for continuous irrigation schedule" />
    <tool name="get_weather_forecast()" purpose="Retrieve weather forecast data from Open-Meteo API" />
    <tool name="datetime_to_timestamp_ms(datetime_str)" purpose="Convert datetime string to milliseconds timestamp" />
    <tool name="timestamp_ms_to_datetime(timestamp_ms)" purpose="Convert timestamp (ms) to readable datetime" />
    <tool name="get_other_days(days)" purpose="Get datetime for specified number of days from current date" />
    <tool name="get_current_datetime()" purpose="Get current datetime in standard format" />
  </tools>

  <execution_protocol>
    <rule>Always confirm time unit consistency before calculations.</rule>
    <rule>Check weather data before any future schedule adjustments.</rule>
    <rule>Always validate tool outputs and schedule integrity.</rule>
    <rule>Request explicit user confirmation before modifying, deleting, or adding schedules.</rule>
    <rule>If insufficient data is available, respond: “No reliable schedule data available at this time.”</rule>
  </execution_protocol>
</agent>

""",
      # response_model=IrrigationProgramResponse,
      parser_model=Gemini(id="gemini-2.0-flash"),
      add_datetime_to_instructions=True,
      markdown=True,
      debug_mode=True,
      show_tool_calls=True,
   )