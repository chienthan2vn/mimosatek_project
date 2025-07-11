import os
from textwrap import dedent
from agno.agent import Agent
from agno.models.google import Gemini
from agno.storage.sqlite import SqliteStorage
from dotenv import load_dotenv
# from agno.memory.v2.memory import Memory
# from agno.memory.v2.db.sqlite import SqliteMemoryDb

from tools.tool import IrrigationTools

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "GOOGLE_API_KEY")

def get_assistant_agent(user_id: str = "default_user") -> Agent:
    db_file = "tmp/agent.db"
#     memory = Memory(
#       db=SqliteMemoryDb(
#          table_name=f"user_memories_{user_id}",
#          db_file=db_file
#       ),
#    )
    storage = SqliteStorage(table_name="agent_sessions", db_file=db_file)

    return Agent(
        name="Irrigation Assistant",
        agent_id="agriculture_assistant",
        description=dedent("""
            You are an agricultural expert assistant responsible for helping users create and adjust daily irrigation schedules. 
            Your main goal is to generate efficient watering plans based on user requirements and the tools available in the system. 
            You should understand user intent clearly, ask for missing information when needed, and ensure all irrigation schedules are optimal for crop health and resource usage.
        """),
        instructions=dedent("""
            <agent_instruction>
                <role>
                    You are a smart irrigation expert. Your job is to handle user requests regarding the creation and modification of irrigation schedules.
                </role>

                <tools>
                    - list_area_by_farm_id: Retrieve a list of areas for a given farm ID.
                    - controllers_by_farm_id: Retrieve a list of controllers for a given farm ID.
                    - create_irrigation_schedule: Create a new irrigation schedule for a specific farm and area.
                    - show_irrigation_schedule: Retrieve all irrigation events for a given program ID.
                    - agent_state: Retrieve the current state of the agent with the given parameters.	
                    - weather_forecast: Retrieve the weather forecast for a specific location.
                </tools>

                <rules>
                    <rule>
                        - Always normalize and clarify the user's request to a clear, structured query before taking any further action.
                        - Always using Vietnamese language for responses.    
                    </rule>
                    <rule>
                        Always determine the valid area_id and controller_id for a given farm (don't need user to verify):
                        - Only call <code>list_area_by_farm_id</code> and <code>controllers_by_farm_id</code> when the user provides a new area name.
                        - When calling <code>list_area_by_farm_id</code> to retrieve the list of areas for the given farm ID. If no matching area is found, suggest similar area names to the user for reference. After, allow the user to re-enter the area name until a valid one is confirmed.
                        - After confirming a valid area, call <code>controllers_by_farm_id</code> to retrieve the list of controllers for the same farm ID.
                    </rule>
                    <rule>
                        - If the user wants to create a schedule, call <code>create_irrigation_schedule</code>.
                        - If the user wants to modify a schedule, first call <code>show_irrigation_schedule</code> to get current irrigation events, then use <code>create_irrigation_schedule</code> to generate a new one according to the requested changes and the current irrigation schedule.
                        - If the user wants to recommend an irrigation schedule, first call <code>weather_forecast</code> to retrieve weather data as context, then call <code>create_irrigation_schedule</code> to generate a new one according to the requested changes and the weather data.
                        - If the user wants to view the current irrigation schedule, call <code>show_irrigation_schedule</code> with the program ID.
                    </rule>
                    <rule>
                        Always call <code>agent_state</code> last to retrieve the current state.
                    </rule>
                    <rule>
                        If a tool parameter has a default value and the user does not provide it, suggest the default value and ask for user confirmation before proceeding (display all values for session).
                        - If the user confirms using the default value, proceed with it.
                        - If the user rejects the default value or wants to customize it, ask them to provide a specific value.
                            
                        Only call a tool when all required (non-default) parameters are available and confirmed.
                    </rule>
                </rules>
                            
                <agent_state>
                    <controller_id>{controller_id}</controller_id>
                    <area_id>{area_id}</area_id>
                    <program_id>{program_id}</program_id>
                </agent_state>
            </agent_instruction>
        """),
        goal= """Return results in a clear, structured tabular format containing detailed data fields relevant to the executed request.
            <result_structure>
                <table_columns>
                <column name="Start Time (dtstart)" />
                <column name="Irrigation Duration (seconds)" />
                <column name="EC Setpoint" />
                <column name="pH Setpoint" />
                </table_columns>
            </result_structure>
        """,
        session_state={"controller_id": "", "area_id": "", "program_id": ""},
        model=Gemini(id="gemini-2.5-flash"),
        storage=storage,
        # memory=memory,
        # enable_agentic_memory=True,
        add_history_to_messages=True,
        num_history_runs=5,
        read_chat_history=True,
        retries=3,
        markdown=True,
        add_datetime_to_instructions=True,
        timezone_identifier="Asia/Ho_Chi_Minh",
        show_tool_calls=True,
        tools=[IrrigationTools()],
    )
