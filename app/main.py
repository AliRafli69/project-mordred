from typing import Annotated, Literal

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, StringConstraints

from app.auth import require_backend_api_key
from app.chat import LMStudioChatClient
from app.config import Settings, get_settings
from app.inference import (
    InferenceAuthenticationError,
    InferenceMalformedResponseError,
    InferenceModelUnavailableError,
    InferenceTimeoutError,
    InferenceUnavailableError,
    LMStudioClient,
)
from app.prompts import PromptConfigurationError, load_system_prompt


APP_VERSION = "0.3.0"


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str


class ReadyResponse(BaseModel):
    status: Literal["ready"]
    inference: Literal["available"]
    model: str


class UnreadyResponse(BaseModel):
    status: Literal["not_ready"]
    inference: Literal["unavailable"]
    reason: Literal[
        "inference_unavailable",
        "timeout",
        "authentication_failed",
        "malformed_response",
        "model_unavailable",
    ]


class ChatRequest(BaseModel):
    message: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=8000),
    ]


class ChatResponse(BaseModel):
    reply: str
    model: str


class ChatUnavailableResponse(BaseModel):
    status: Literal["unavailable"]
    reason: Literal[
        "inference_unavailable",
        "timeout",
        "authentication_failed",
        "malformed_response",
        "prompt_configuration_error",
    ]


def get_inference_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> LMStudioClient:
    """Create the configured private inference-readiness client."""

    return LMStudioClient(settings=settings)


def get_chat_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> LMStudioChatClient:
    """Create the configured private chat client."""

    return LMStudioChatClient(settings=settings)


def unready_response(
    reason: Literal[
        "inference_unavailable",
        "timeout",
        "authentication_failed",
        "malformed_response",
        "model_unavailable",
    ],
) -> JSONResponse:
    payload = UnreadyResponse(
        status="not_ready",
        inference="unavailable",
        reason=reason,
    )

    return JSONResponse(
        status_code=503,
        content=payload.model_dump(),
    )


def chat_unavailable_response(
    reason: Literal[
        "inference_unavailable",
        "timeout",
        "authentication_failed",
        "malformed_response",
        "prompt_configuration_error",
    ],
) -> JSONResponse:
    payload = ChatUnavailableResponse(
        status="unavailable",
        reason=reason,
    )

    return JSONResponse(
        status_code=503,
        content=payload.model_dump(),
    )


app = FastAPI(
    title="Mordred Backend",
    version=APP_VERSION,
    description="Shared backend service for Project Mordred.",
)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["service"],
    summary="Check backend health",
)
async def health() -> HealthResponse:
    """Report whether the Mordred backend process is operating."""

    return HealthResponse(
        status="ok",
        service="mordred-backend",
        version=APP_VERSION,
    )


@app.get(
    "/ready",
    response_model=ReadyResponse,
    responses={503: {"model": UnreadyResponse}},
    tags=["service"],
    summary="Check private inference readiness",
)
async def ready(
    client: Annotated[LMStudioClient, Depends(get_inference_client)],
) -> ReadyResponse | JSONResponse:
    """Report LM Studio and configured-model availability."""

    try:
        model = await client.check_ready()
    except InferenceTimeoutError:
        return unready_response("timeout")
    except InferenceAuthenticationError:
        return unready_response("authentication_failed")
    except InferenceMalformedResponseError:
        return unready_response("malformed_response")
    except InferenceModelUnavailableError:
        return unready_response("model_unavailable")
    except InferenceUnavailableError:
        return unready_response("inference_unavailable")

    return ReadyResponse(
        status="ready",
        inference="available",
        model=model,
    )


@app.post(
    "/chat",
    response_model=ChatResponse,
    responses={503: {"model": ChatUnavailableResponse}},
    tags=["chat"],
    summary="Generate an authenticated Mordred response",
)
async def chat(
    request: ChatRequest,
    _: Annotated[None, Depends(require_backend_api_key)],
    client: Annotated[LMStudioChatClient, Depends(get_chat_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ChatResponse | JSONResponse:
    """Generate one response using Mordred's server-held personality."""

    try:
        system_prompt = load_system_prompt()
    except PromptConfigurationError:
        return chat_unavailable_response("prompt_configuration_error")

    try:
        reply = await client.generate(
            system_prompt=system_prompt,
            user_input=request.message,
        )
    except InferenceTimeoutError:
        return chat_unavailable_response("timeout")
    except InferenceAuthenticationError:
        return chat_unavailable_response("authentication_failed")
    except InferenceMalformedResponseError:
        return chat_unavailable_response("malformed_response")
    except InferenceUnavailableError:
        return chat_unavailable_response("inference_unavailable")

    return ChatResponse(
        reply=reply,
        model=settings.lm_studio_model,
    )
