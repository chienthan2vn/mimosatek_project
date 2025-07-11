from agno.playground import Playground
from agents.assistant import get_assistant_agent

a = get_assistant_agent()

playground = Playground(
    agents=[a],
    name="Basic Agent",
    app_id="basic_agent",
    description="A basic agent that can answer questions and help with tasks.",
)

app = playground.get_app()

if __name__ == "__main__":
    playground.serve(app="app:app", reload=True)