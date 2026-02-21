import os
import datetime
import logging
import random
from typing import List, Tuple, Optional, Dict, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Configure logging
logger = logging.getLogger(__name__)

# Scopes required for Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

class CalendarService:
    def __init__(self):
        self.client_id = os.environ.get("GOOGLE_CLIENT_ID")
        self.client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8080/admin/calendar/callback")

        # Mock mode is enabled if credentials are not present
        self.mock_mode = not (self.client_id and self.client_secret)
        if self.mock_mode:
            logger.warning("CalendarService initialized in MOCK MODE (Missing GOOGLE_CLIENT_ID/SECRET).")

    def get_authorization_url(self, user_id: str) -> str:
        """
        Generates the Google OAuth2 authorization URL.
        """
        if self.mock_mode:
            # Return a dummy URL that points to the callback with a fake code
            return f"{self.redirect_uri}?code=mock_auth_code_for_{user_id}&state={user_id}"

        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                },
                scopes=SCOPES
            )
            flow.redirect_uri = self.redirect_uri
            auth_url, _ = flow.authorization_url(prompt='consent', state=user_id)
            return auth_url
        except Exception as e:
            logger.error(f"Error generating auth URL: {e}")
            return "#error"

    def exchange_code(self, code: str) -> Dict[str, Any]:
        """
        Exchanges the authorization code for credentials.
        Returns the credentials dictionary (token, refresh_token, etc).
        """
        if self.mock_mode or "mock_auth_code" in code:
            logger.info("Mocking token exchange.")
            return {
                "token": "mock_access_token",
                "refresh_token": "mock_refresh_token",
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": "mock_client_id",
                "client_secret": "mock_client_secret",
                "scopes": SCOPES
            }

        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                },
                scopes=SCOPES
            )
            flow.redirect_uri = self.redirect_uri
            flow.fetch_token(code=code)
            creds = flow.credentials
            return {
                "token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": creds.scopes
            }
        except Exception as e:
            logger.error(f"Error exchanging code: {e}")
            raise

    def get_free_slots(self, user_id: str, date_str: str = "today") -> str:
        """
        Fetches free slots for the given user.
        Args:
            user_id: The ID of the user (host).
            date_str: "today" or "tomorrow".
        Returns:
            A natural language string of available slots.
        """
        # Determine date
        now = datetime.datetime.now()
        target_date = now
        if date_str.lower() == "tomorrow":
            target_date = now + datetime.timedelta(days=1)
        elif date_str.lower() == "today":
            target_date = now

        # In a real implementation, we would fetch the user's credentials from DB,
        # build the service, and query the FreeBusy API.

        # Mock Logic: Generate realistic slots (e.g., 10:00, 14:00, 16:30)
        # We'll pretend the user is busy in the morning and has slots in the afternoon.

        weekday = target_date.weekday() # 0=Mon, 6=Sun

        if weekday >= 5: # Weekend
            return "Não tenho horários disponíveis no fim de semana. Podemos agendar para segunda-feira?"

        # Generate random slots for demo
        # Fixed set of potential slots
        potential_slots = ["10:00", "11:00", "14:00", "15:30", "16:00", "17:00"]

        # Randomly select 2-3 slots
        available_slots = sorted(random.sample(potential_slots, k=random.randint(2, 3)))

        date_formatted = target_date.strftime("%d/%m")
        return f"Para {date_str} ({date_formatted}), tenho os seguintes horários livres: {', '.join(available_slots)}. Qual prefere?"

    def create_meeting(self, user_id: str, lead_email: str, start_time_str: str, description: str = "") -> str:
        """
        Creates a meeting on the calendar.
        Args:
            user_id: Host ID.
            lead_email: Guest email.
            start_time_str: e.g. "tomorrow at 14:00" or just "14:00" (needs parsing logic in real app).
                            For this mock, we assume the agent passes something understandable.
            description: Event description.
        Returns:
            The meeting link.
        """
        # In a real app, we'd parse start_time_str to a datetime object,
        # use the user's credentials to call calendar.events.insert with conferenceData.

        logger.info(f"Booking meeting for {lead_email} at {start_time_str}")

        # Generate a mock Meet link
        meet_id = f"{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(100,999)}"
        meet_link = f"https://meet.google.com/{meet_id}"

        return f"Agendado! O link da reunião é: {meet_link}. Enviei um convite para {lead_email}."

# Singleton instance
calendar_service = CalendarService()
