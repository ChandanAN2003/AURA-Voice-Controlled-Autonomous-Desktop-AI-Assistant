from utils.helpers import setup_logger

logger = setup_logger("EmailCalendar")

class EmailCalendarAgent:
    """
    Mock agent for interacting with Emails and Calendars.
    """
    def __init__(self):
        pass

    def check_unread_emails(self) -> str:
        logger.info("Checking unread emails...")
        # In a real app, use imaplib or Google API here.
        return "You have 3 unread emails. One from your professor regarding the project update, and two newsletters."

    def read_todays_schedule(self) -> str:
        logger.info("Reading today's schedule...")
        return "You have a project review meeting at 2 PM, and a coding session scheduled at 5 PM."

    def send_quick_reply(self, recipient: str, message: str) -> str:
        logger.info(f"Sending email to {recipient}: {message}")
        return f"Message sent to {recipient}."
