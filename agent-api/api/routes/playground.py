from agno.playground import Playground

from agents.analysis_intent import get_analysis_intent_agent
from agents.plant_agent import get_plant_agent
from agents.reflection_agent import get_reflection_agent

######################################################
## Routes for the Playground Interface
######################################################

# Get Agents to serve in the playground
analysis_intent_agent = get_analysis_intent_agent()
plant_agent = get_plant_agent()
reflection_agent = get_reflection_agent()
# Create a playground instance
playground = Playground(agents=[analysis_intent_agent, plant_agent, reflection_agent])

# Get the router for the playground
playground_router = playground.get_async_router()
