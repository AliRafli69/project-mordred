from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from app.config import Settings
from app.inference import (
    InferenceAuthenticationError,
    InferenceMalformedResponseError,
    InferenceTimeoutError,
    InferenceUnavailableError,
)


class ChatOutputRecord(BaseModel):
    type: str
    content: str | None = None


class ChatResponse(BaseModel):
    output: list[ChatOutputRecord]


class LMStudioChatClient:
    """Bounded asynchronous client for LM Studio chat generation."""

    def __init__(
        self,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._transport = transport

    async def generate(
        self,
        *,
        system_prompt: str,
        user_input: str,
    ) -> str:
        """Generate one non-streaming response using the configured model."""

        endpoint = (
            f"{str(self._settings.lm_studio_base_url).rstrip('/')}"
            "/api/v1/chat"
        )
        timeout = httpx.Timeout(
            timeout=self._settings.read_timeout_seconds,
            connect=self._settings.connect_timeout_seconds,
        )
        headers = {
            "Authorization": (
                "Bearer "
                f"{self._settings.lm_studio_api_key.get_secret_value()}"
            )
        }
        payload = {
            "model": self._settings.lm_studio_model,
            "system_prompt": system_prompt,
            "input": user_input,
            "reasoning": "off",
            "temperature": self._settings.chat_temperature,
            "max_output_tokens": self._settings.chat_max_output_tokens,
            "stream": False,
            "store": False,
        }

        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                transport=self._transport,
            ) as client:
                response = await client.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                )
        except httpx.TimeoutException as exc:
            raise InferenceTimeoutError from exc
        except httpx.RequestError as exc:
            raise InferenceUnavailableError from exc

        if response.status_code in {401, 403}:
            raise InferenceAuthenticationError

        if response.status_code != 200:
            raise InferenceUnavailableError

        try:
            raw_payload: Any = response.json()
            chat_response = ChatResponse.model_validate(raw_payload)
        except (ValueError, TypeError, ValidationError) as exc:
            raise InferenceMalformedResponseError from exc

        for record in chat_response.output:
            if record.type == "message" and record.content:
                content = record.content.strip()

                if content:
                    return content

        raise InferenceMalformedResponseError
