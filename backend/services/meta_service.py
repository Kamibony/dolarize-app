import httpx
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

META_API_VERSION = "v18.0"

class MetaService:
    def __init__(self):
        self.access_token = os.environ.get("META_ACCESS_TOKEN")
        self.phone_number_id = os.environ.get("META_PHONE_NUMBER_ID") # For WhatsApp
        # For Instagram, we typically use the Page Access Token.
        # We might need the Page ID or IG Account ID to be explicit, but 'me' often works with Page Token.

    async def send_whatsapp_message(self, to: str, text: str):
        """
        Sends a text message via WhatsApp Cloud API.
        """
        if not self.access_token or not self.phone_number_id:
            logger.error("Meta credentials (access token or phone number ID) missing for WhatsApp.")
            return

        url = f"https://graph.facebook.com/{META_API_VERSION}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": text}
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                logger.info(f"WhatsApp message sent to {to}")
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to send WhatsApp message: {e.response.text}")
            except Exception as e:
                logger.error(f"Error sending WhatsApp message: {e}")

    async def send_instagram_message(self, to: str, text: str):
        """
        Sends a text message via Instagram Graph API.
        Assumes the Access Token is a valid Page Access Token linked to the Instagram account.
        """
        if not self.access_token:
            logger.error("Meta access token missing for Instagram.")
            return

        # Using the Generic Send API for Instagram (via Page)
        url = f"https://graph.facebook.com/{META_API_VERSION}/me/messages"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "recipient": {"id": to},
            "message": {"text": text}
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                logger.info(f"Instagram message sent to {to}")
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to send Instagram message: {e.response.text}")
            except Exception as e:
                logger.error(f"Error sending Instagram message: {e}")

meta_service = MetaService()
