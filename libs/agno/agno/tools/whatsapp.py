import json
import os
from typing import Any, Dict, List, Optional

import httpx

from agno.tools import Toolkit
from agno.utils.log import logger


class WhatsAppTools(Toolkit):
    """WhatsApp Business API toolkit for sending messages."""

    base_url = "https://graph.facebook.com"

    def __init__(
        self,
        access_token: Optional[str] = None,
        phone_number_id: Optional[str] = None,
        version: str = "v22.0",
        recipient_waid: Optional[str] = None,
        async_mode: bool = False,
    ):
        """Initialize WhatsApp toolkit.

        Args:
            access_token: WhatsApp Business API access token
            phone_number_id: WhatsApp Business Account phone number ID
            version: API version to use
            recipient_waid: Default recipient WhatsApp ID (optional)
            async_mode: Whether to use async methods (default: False)
        """
        super().__init__(name="whatsapp")

        # Core credentials
        self.access_token = access_token or os.getenv("WHATSAPP_ACCESS_TOKEN") or os.getenv("WHATSAPP_ACCESS_TOKEN")
        if not self.access_token:
            logger.error("WHATSAPP_ACCESS_TOKEN not set. Please set the WHATSAPP_ACCESS_TOKEN environment variable.")

        self.phone_number_id = (
            phone_number_id or os.getenv("WHATSAPP_PHONE_NUMBER_ID") or os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        )
        if not self.phone_number_id:
            logger.error(
                "WHATSAPP_PHONE_NUMBER_ID not set. Please set the WHATSAPP_PHONE_NUMBER_ID environment variable."
            )

        # Optional default recipient
        self.default_recipient = (
            recipient_waid or os.getenv("WHATSAPP_RECIPIENT_WAID") or os.getenv("WHATSAPP_RECIPIENT_WAID")
        )

        # API version and mode
        self.version = version or os.getenv("WHATSAPP_VERSION") or os.getenv("WHATSAPP_VERSION", "v22.0")
        self.async_mode = async_mode

        # Register methods that can be used by the agent based on mode
        if self.async_mode:
            self.register(self.send_text_message_async)
            self.register(self.send_template_message_async)
        else:
            self.register(self.send_text_message_sync)
            self.register(self.send_template_message_sync)

        # Log configuration status
        self._log_config_status()

    def _log_config_status(self):
        """Log the configuration status of the WhatsApp toolkit."""
        config_status = {
            "Core credentials": {
                "access_token": bool(self.access_token),
                "phone_number_id": bool(self.phone_number_id),
            },
            "Optional settings": {
                "default_recipient": bool(self.default_recipient),
                "api_version": self.version,
                "async_mode": self.async_mode,
            },
        }
        logger.debug(f"WhatsApp toolkit configuration status: {json.dumps(config_status, indent=2)}")

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

    def _get_messages_url(self) -> str:
        """Get the messages endpoint URL."""
        return f"{self.base_url}/{self.version}/{self.phone_number_id}/messages"

    async def _send_message_async(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message asynchronously using the WhatsApp API.

        Args:
            data: Message data to send

        Returns:
            API response as dictionary
        """
        url = self._get_messages_url()
        headers = self._get_headers()

        logger.debug(f"Sending WhatsApp request to URL: {url}")
        logger.debug(f"Request data: {json.dumps(data, indent=2)}")
        logger.debug(f"Headers: {json.dumps(headers, indent=2)}")

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)

            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            logger.debug(f"Response body: {response.text}")

            response.raise_for_status()
            return response.json()

    def _send_message_sync(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message synchronously using the WhatsApp API.

        Args:
            data: Message data to send

        Returns:
            API response as dictionary
        """
        url = self._get_messages_url()
        headers = self._get_headers()

        logger.debug(f"Sending WhatsApp request to URL: {url}")
        logger.debug(f"Request data: {json.dumps(data, indent=2)}")
        logger.debug(f"Headers: {json.dumps(headers, indent=2)}")

        response = httpx.post(url, headers=headers, json=data)

        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")
        logger.debug(f"Response body: {response.text}")

        response.raise_for_status()
        return response.json()

    def send_text_message_sync(
        self,
        text: str = "",
        recipient: Optional[str] = None,
        preview_url: bool = False,
        recipient_type: str = "individual",
    ) -> str:
        """Send a text message to a WhatsApp user (synchronous version).

        Args:
            text: The text message to send
            recipient: Recipient's WhatsApp ID or phone number (e.g., "+1234567890"). If not provided, uses default_recipient
            preview_url: Whether to generate previews for links in the message

        Returns:
            Success message with message ID
        """
        # Use default recipient if none provided
        if recipient is None:
            if not self.default_recipient:
                raise ValueError("No recipient provided and no default recipient set")
            recipient = self.default_recipient
            logger.debug(f"Using default recipient: {recipient}")

        logger.debug(f"Sending WhatsApp message to {recipient}: {text}")
        logger.debug(f"Current config - Phone Number ID: {self.phone_number_id}, Version: {self.version}")

        data = {
            "messaging_product": "whatsapp",
            "recipient_type": recipient_type,
            "to": recipient,
            "type": "text",
            "text": {"preview_url": preview_url, "body": text},
        }

        try:
            response = self._send_message_sync(data)
            message_id = response.get("messages", [{}])[0].get("id", "unknown")
            logger.debug(f"Full API response: {json.dumps(response, indent=2)}")
            return f"Message sent successfully! Message ID: {message_id}"
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            logger.error(f"Error response: {e.response.text if hasattr(e, 'response') else 'No response text'}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp message: {str(e)}")
            raise

    def send_template_message_sync(
        self,
        recipient: Optional[str] = None,
        template_name: str = "",
        language_code: str = "en_US",
        components: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Send a template message to a WhatsApp user (synchronous version).

        Args:
            recipient: Recipient's WhatsApp ID or phone number (e.g., "+1234567890"). If not provided, uses default_recipient
            template_name: Name of the template to use
            language_code: Language code for the template (e.g., "en_US")
            components: Optional list of template components (header, body, buttons)

        Returns:
            Success message with message ID
        """
        # Use default recipient if none provided
        if recipient is None:
            if not self.default_recipient:
                raise ValueError("No recipient provided and no default recipient set")
            recipient = self.default_recipient

        logger.debug(f"Sending WhatsApp template message to {recipient}: {template_name}")

        data = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "template",
            "template": {"name": template_name, "language": {"code": language_code}},
        }

        if components:
            data["template"]["components"] = components  # type: ignore[index]

        try:
            response = self._send_message_sync(data)
            message_id = response.get("messages", [{}])[0].get("id", "unknown")
            return f"Template message sent successfully! Message ID: {message_id}"
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to send WhatsApp template message: {e}")
            raise

    async def send_text_message_async(
        self,
        text: str = "",
        recipient: Optional[str] = None,
        preview_url: bool = False,
        recipient_type: str = "individual",
    ) -> str:
        """Send a text message to a WhatsApp user (asynchronous version).

        Args:
            text: The text message to send
            recipient: Recipient's WhatsApp ID or phone number (e.g., "+1234567890"). If not provided, uses default_recipient
            preview_url: Whether to generate previews for links in the message

        Returns:
            Success message with message ID
        """
        # Use default recipient if none provided
        if recipient is None:
            if not self.default_recipient:
                raise ValueError("No recipient provided and no default recipient set")
            recipient = self.default_recipient
            logger.debug(f"Using default recipient: {recipient}")

        logger.debug(f"Sending WhatsApp message to {recipient}: {text}")
        logger.debug(f"Current config - Phone Number ID: {self.phone_number_id}, Version: {self.version}")

        data = {
            "messaging_product": "whatsapp",
            "recipient_type": recipient_type,
            "to": recipient,
            "type": "text",
            "text": {"preview_url": preview_url, "body": text},
        }

        try:
            response = await self._send_message_async(data)
            message_id = response.get("messages", [{}])[0].get("id", "unknown")
            logger.debug(f"Full API response: {json.dumps(response, indent=2)}")
            return f"Message sent successfully! Message ID: {message_id}"
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            logger.error(f"Error response: {e.response.text if hasattr(e, 'response') else 'No response text'}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp message: {str(e)}")
            raise

    async def send_template_message_async(
        self,
        recipient: Optional[str] = None,
        template_name: str = "",
        language_code: str = "en_US",
        components: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Send a template message to a WhatsApp user (asynchronous version).

        Args:
            recipient: Recipient's WhatsApp ID or phone number (e.g., "+1234567890"). If not provided, uses default_recipient
            template_name: Name of the template to use
            language_code: Language code for the template (e.g., "en_US")
            components: Optional list of template components (header, body, buttons)

        Returns:
            Success message with message ID
        """
        # Use default recipient if none provided
        if recipient is None:
            if not self.default_recipient:
                raise ValueError("No recipient provided and no default recipient set")
            recipient = self.default_recipient

        logger.debug(f"Sending WhatsApp template message to {recipient}: {template_name}")

        data = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "template",
            "template": {"name": template_name, "language": {"code": language_code}},
        }

        if components:
            data["template"]["components"] = components  # type: ignore[index]

        try:
            response = await self._send_message_async(data)
            message_id = response.get("messages", [{}])[0].get("id", "unknown")
            return f"Template message sent successfully! Message ID: {message_id}"
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to send WhatsApp template message: {e}")
            raise
    async def send_image_message_async(self, image: any = None, text: Optional[str] = None, recipient: Optional[str] = None) -> str:
        """Send an image message to a WhatsApp user (asynchronous version).

        Args:
            image: The media id or file reference for the image to send
            text: Caption for the image
            recipient: Recipient's WhatsApp ID or phone number (e.g., "+1234567890"). If not provided, uses default_recipient

        Returns:
            Success message with message ID
        """
        # Use default recipient if none provided
        if recipient is None:
            if not self.default_recipient:
                raise ValueError("No recipient provided and no default recipient set")
            recipient = self.default_recipient
            logger.debug(f"Using default recipient: {recipient}")

        logger.debug(f"Sending WhatsApp image to {recipient}: {text}")
        logger.debug(f"Current config - Phone Number ID: {self.phone_number_id}, Version: {self.version}")

        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "image",
            "image": {"id": image, "caption": text},
        }

        try:
            response = await self._send_message_async(data)
            message_id = response.get("messages", [{}])[0].get("id", "unknown")
            logger.debug(f"Full API response: {json.dumps(response, indent=2)}")
            return f"Message sent successfully! Message ID: {message_id}"
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to send WhatsApp image message: {e}")
            logger.error(f"Error response: {e.response.text if hasattr(e, 'response') else 'No response text'}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp image message: {str(e)}")
            raise
    def send_image_message_sync(self, image:str = None, text: Optional[str] = None, recipient: Optional[str] = None) -> str:
        """Send an image message to a WhatsApp user (synchronous version).

        Args:
            image: The media id or file reference for the image to send
            text: Caption for the image
            recipient: Recipient's WhatsApp ID or phone number (e.g., "+1234567890"). If not provided, uses default_recipient

        Returns:
            Success message with message ID
        """
        # Use default recipient if none provided
        if recipient is None:
            if not self.default_recipient:
                raise ValueError("No recipient provided and no default recipient set")
            recipient = self.default_recipient
            logger.debug(f"Using default recipient: {recipient}")

        logger.debug(f"Sending WhatsApp image to {recipient}: {text}")
        logger.debug(f"Current config - Phone Number ID: {self.phone_number_id}, Version: {self.version}")

        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "image",
            "image": {"id": image, "caption": text},
        }

        try:
            response = self._send_message_sync(data)
            message_id = response.get("messages", [{}])[0].get("id", "unknown")
            logger.debug(f"Full API response: {json.dumps(response, indent=2)}")
            return f"Message sent successfully! Message ID: {message_id}"
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to send WhatsApp image message: {e}")
            logger.error(f"Error response: {e.response.text if hasattr(e, 'response') else 'No response text'}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp image message: {str(e)}")
            raise
