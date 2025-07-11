from agents.assistant import get_assistant_agent

if __name__ == "__main__":
    # Initialize the assistant agent
    agent = get_assistant_agent()

    farm_id = "95c3d870-7fab-11ef-bfc9-113ee5630d77"
    area_id = "16106380-f811-11ef-8831-112b9cc8d9f8"
    
    while True:
        user_input = input("Enter your request: ")
        agent.print_response(f"{user_input}", stream = True)