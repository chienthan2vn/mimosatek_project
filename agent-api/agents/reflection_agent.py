from textwrap import dedent
from typing import Optional

from agno.agent import Agent, AgentKnowledge
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.url import UrlKnowledge
from agno.memory.v2.db.postgres import PostgresMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.openai import OpenAIChat
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.vectordb.pgvector import PgVector, SearchType

from db.session import db_url
from tools.tool import GetLastIrrigationDataTool

def get_reflection_agent(
    model_id: str = "gpt-4.1",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = True,
) -> Agent:
    return Agent(
        name = "Reflection Agent",
        agent_id = "reflection_agent",
        user_id = user_id,
        session_id = session_id,
        model = OpenAIChat(id=model_id),
        description = dedent("""
            Agricultural expert with 20+ years of experience in analyzing and optimizing crop irrigation cycles to improve water efficiency, increase yields, and promote sustainable farming.                     
        """),
        instructions = dedent(""" 
            # 🧠 Reflection Agent – Instructions

            ## Role
            You are a **Reflection Agent** acting as an **agronomy expert** in an automated irrigation system.

            ## Task
            Analyze the data from a **recently completed irrigation cycle** and generate a **short, suggestive comment** to help the **Plan Agent** improve decisions for the next cycle.

            ## Technical Objective
            - **Target EC**: `4.0`
            - Your comment must evaluate:
            1. The **measured EC** vs. the target EC
            2. Whether the **waiting time before irrigation** was appropriate

            ## Input Format
            - `input_data`: includes `T_chờ_phút` (waiting time in minutes)
            - `output_data`: includes:
            - `T_đầy_giây` (full irrigation time in seconds)
            - `EC_đo_được` (measured EC value)

            ## Output Requirements
            - Return **only one string comment**
            - The comment must be:
            - **Concise**: max **100 words**
            - **Suggestive**: provide useful insights for future adjustments (e.g., reduce waiting time, EC too low/high, etc.)
            - **Professional**: reflect the judgment of a skilled agronomist

            ## Example Comment (for inspiration only)
            > "The current EC is below the target. Consider reducing waiting time or increasing solution concentration. Full irrigation was fast and needs no change."

        """),
        tools = [GetLastIrrigationDataTool()],
        markdown = True,
        add_datetime_to_instructions = True,
        debug_mode = debug_mode
    )