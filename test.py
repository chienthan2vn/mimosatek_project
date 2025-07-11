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

# For synchronous router:
# app = fastapi_app.get_app(use_async=False)

if __name__ == "__main__":
    playground.serve(app="test:app", reload=True)