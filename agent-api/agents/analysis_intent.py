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

class AnalysisOutput(BaseModel):
    status: str = "success"  # Status of the analysis
    delay: int = 0  # Recommended delay in minutes


def get_analysis_intent_agent(
    model_id: str = "gpt-4.1",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = True,
) -> Agent:
    return Agent(
        name="Analysis Intent Agent",
        agent_id="analysis_intent_agent",
        user_id=user_id,
        session_id=session_id,
        model=OpenAIChat(id=model_id),
        description=dedent("""
            Expert in analyzing and interpreting data to derive actionable insights for decision-making.
        """),
        instructions=dedent("""
            ## 🧠 Instructions for Agent: Analyzing User Intent in Irrigation Decisions
            ### 📝 Description

                You are a user intent analysis expert. When the system (**agent**) proposes an **irrigation action**, the **user** may respond in one of two ways:

                1. ✅ **Agree** with the proposed irrigation.  
                2. ❌ **Disagree** and request an **adjustment** to the irrigation timing.

                Your task is to analyze the user's response and determine two output fields: `status` and `delay`.

            ---

            ### 📤 Output Format

                ```json
                {
                "status": "success" | "adjust",
                "delay": -1 | 0 | >0
                }

            ---
            
            ### 📌 Field Descriptions

                - **status**:
                - `"success"` → The user agrees with the proposed irrigation.
                - `"adjust"` → The user disagrees and requests a different irrigation time.

                - **delay**:
                - `0` → The user agrees to irrigate **immediately**.
                - `>0` → The user disagrees but specifies a **delay time in minutes**.  
                    **Example:** `"Let’s water in 20 minutes"` → `delay = 20`
                - `-1` → The user disagrees but **does not specify** a delay time.  
                    **Example:** `"Not now, maybe later."` → `delay = -1`

        """),
        response_model = AnalysisOutput,
        add_datetime_to_instructions = True,
        debug_mode=debug_mode,
    )