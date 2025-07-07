import json
from typing import Dict, Any, List



def get_payload_of_create_program_api(controller_id: str) -> Dict[str, Any]:
    """
    Prepare the payload for creating a new irrigation program.

    Args:
        controller_id (str): The ID of the controller to create the program for.

    Returns:
        Dict[str, Any]: The payload for the API request.
    """
    query = """
    mutation Create_irrigation_program ($controller_id: ID!, $name: String!) {
        create_irrigation_program(controller_id: $controller_id, name: $name)
    }
    """
    
    variables = {
        "controller_id": controller_id,
        "name": "Irrigation Program "
    }
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    payload = json.dumps(payload)
    
    return payload
    
def get_payload_of_list_programs_irrigation_envents_api(program_id: str) -> Dict[str, Any]:
    """
    Prepare the payload for listing irrigation events of a specific program.

    Args:
        program_id (str): The ID of the irrigation program.

    Returns:
        Dict[str, Any]: The payload for the API request.
    """
    query = """
    query Irrigation_events ($program_id: ID!){
        irrigation_events(program_id: $program_id) {
            id
            name
            area_id
            strict_time
            dtstart
            irrigation_method
            quantity
            recurrence
            nutrients_mixing_program {
                name
                mixing_type
                rates
                ph_setpoint
                ec_setpoint
            }
        }
    }
    """
    
    variables = {
        "program_id": program_id
    }
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    payload = json.dumps(payload)
    
    return payload
    
def get_payload_for_create_irrigation_event_api(
    program_id: str,
    area_id: str,
    dtstart: int,
    quantity: List[int],
    ph_setpoint: float,
    ec_setpoint: float,
):
    """
    Prepare the payload for creating a new irrigation event.

    Returns:
        Dict[str, Any]: The payload for the API request.
    """
    query = """
    mutation create_irrigation_event(
        $program_id: ID!
        $event: InputIrrigationEvent!
        $stored_as_template: Boolean
        $template_name: String
        ) {
        create_irrigation_event(
            program_id: $program_id
            event: $event
            stored_as_template: $stored_as_template
            template_name: $template_name
        ) {
            id
            duration
        }
    }
    """
    
    variables ={
    "program_id": program_id,
        "event": {
            "area_id": area_id,
            "name": "9kSg-blyR",
            "strict_time": False,
            "dtstart": dtstart,
            "irrigation_method": 0,
            "quantity": quantity,
            "nutrients_mixing_program": {
                "name": "",
                "mixing_type": 1,
                "ph_setpoint": ph_setpoint,
                "ec_setpoint": ec_setpoint,
                "rates": [3.0, 5.0, 0.0, 0.0, 5.0]
            },
            "recurrence": "INTERVAL=1;FREQ=DAILY;UNTIL=20260621T165959Z"
        },
        "stored_as_template": False,
        "template_name": ""
    }

    
    payload = {
        "query": query,
        "variables": variables
    }
    
    payload = json.dumps(payload)
    
    return payload