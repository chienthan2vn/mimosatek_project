from agents.assistant import get_assistant_agent

a = get_assistant_agent()
# b = a.run("What is the watering schedule today?")

b = a.print_response(
        "Lịch tưới tiêu ngày hôm nay như thế nào cho cây cà chua?",
        stream=True,
        show_full_reasoning=True,
        stream_intermediate_steps=True,
    )
# print(b.content)