from textwrap import dedent
from typing import Optional
from pydantic import BaseModel

from agno.agent import Agent
from agno.models.openai import OpenAIChat

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
        instructions=dedent("""## 🧠 Instructions for Agent: Analyzing User Intent in Irrigation Decisions

### 🎯 Role & Objective
You are a user intent analysis expert in an agricultural automation system.  
Your job is to carefully interpret the **user's response** after the system proposes an irrigation action, and decide how to proceed based on their intent.

You must output two fields:  
- `status`: whether the user agrees or requests an adjustment  
- `delay`: the time difference in minutes between the proposed time and the user's requested time (positive, negative, or zero)

---

### 📖 Decision Procedure
Follow these steps:

1. **Read and understand the user's message carefully.**
2. **Determine the overall intent:**
   - If the user explicitly agrees → `status = "success"`
   - If the user asks for a different time → `status = "adjust"`
3. **Extract time adjustment if mentioned:**
   - If the user says **now / immediately / go ahead** → `delay = 0`
   - If the user requests to water in X minutes → `delay = +X`
   - If the user requests to water X minutes earlier → `delay = -X`
4. **If the time is ambiguous, estimate conservatively or set to `0` and note ambiguity in reasoning.**
5. **If no clear intent can be determined, default `status = "adjust"` and `delay = 0`**
        """),
        response_model = AnalysisOutput,
        add_datetime_to_instructions = True,
        debug_mode=debug_mode,
    )