from enum import Enum
from typing import List, Optional

from agents.analysis_intent import get_analysis_intent_agent
from agents.reflection_agent import get_reflection_agent
from agents.plant_agent import get_plant_agent


class AgentType(Enum):
    ANALYSIS_INTENT_AGENT = "analysis_intent_agent"
    REFLECTION_AGENT = "reflection_agent"
    PLANT_AGENT = "plant_agent"


def get_available_agents() -> List[str]:
    """Returns a list of all available agent IDs."""
    return [agent.value for agent in AgentType]


def get_agent(
    model_id: str = "gpt-4.1",
    agent_id: Optional[AgentType] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = True,
):
    if agent_id == AgentType.ANALYSIS_INTENT_AGENT:
        return get_analysis_intent_agent(
            model_id=model_id,
            user_id=user_id,
            session_id=session_id,
            debug_mode=debug_mode,
        )
    elif agent_id == AgentType.REFLECTION_AGENT:
        return get_reflection_agent(
            model_id=model_id,
            user_id=user_id,
            session_id=session_id,
            debug_mode=debug_mode,
        )
    elif agent_id == AgentType.PLANT_AGENT:
        return get_plant_agent(
            model_id=model_id,
            user_id=user_id,
            session_id=session_id,
            debug_mode=debug_mode,
        )
    raise ValueError(f"Agent: {agent_id} not found")
