import os
from agno.agent import Agent
from agno.models.openai import OpenAIChat

from tools.tool import IrrigationTools

agent = Agent(
    name="Irrigation Assistant",
    description="An agent to assist with irrigation management tasks.",
    
)