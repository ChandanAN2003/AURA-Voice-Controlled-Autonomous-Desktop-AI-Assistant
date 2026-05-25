from utils.helpers import setup_logger

logger = setup_logger("SmartHome")

class SmartHomeManager:
    """
    Mock integration for Smart Home devices (Hue, Home Assistant, etc.)
    """
    def __init__(self):
        self.lights_on = True

    def toggle_lights(self, state: bool) -> str:
        self.lights_on = state
        status = "on" if state else "off"
        logger.info(f"Smart home lights turned {status}.")
        return f"I have turned the room lights {status}."

    def dim_lights(self, percentage: int) -> str:
        logger.info(f"Smart home lights dimmed to {percentage}%.")
        return f"Lights dimmed to {percentage} percent."

    def set_temperature(self, temp: int) -> str:
        logger.info(f"Thermostat set to {temp} degrees.")
        return f"Thermostat is now set to {temp} degrees."
