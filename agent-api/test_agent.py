from agents.assistant import get_assistant_agent

a = get_assistant_agent(user_id="farmer_001")

b = a.print_response(
        "Sự kiện tưới ngày 2025/06/30 cho ID mặc định như thế nào?",
        stream=True,
        show_full_reasoning=True,
        stream_intermediate_steps=True,
    )

b = a.print_response(
        "Dựa vào thời tiết hiện tại, hãy thay đổi sự kiện tưới ngày 2025/06/30 cho ID mặc định",
        stream=True,
        show_full_reasoning=True,
        stream_intermediate_steps=True,
    )