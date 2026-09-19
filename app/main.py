from functools import lru_cache
from typing import Annotated, Literal

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, StringConstraints

from app.auth import require_backend_api_key
from app.chat import LMStudioChatClient
from app.config import Settings, get_settings
from app.conversations import ConversationStore, InMemoryConversationStore
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


ConversationId = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$",
    ),
]


class ChatRequest(BaseModel):
    message: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=8000,
        ),
    ]
    conversation_id: ConversationId | None = None


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


@lru_cache
def build_conversation_store(
    max_messages: int,
    max_characters: int,
) -> InMemoryConversationStore:
    """Create the process-wide temporary conversation store."""

    return InMemoryConversationStore(
        max_messages=max_messages,
        max_characters=max_characters,
    )


def get_conversation_store(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ConversationStore:
    """Return the configured temporary conversation store."""

    return build_conversation_store(
        settings.conversation_max_messages,
        settings.conversation_max_characters,
    )


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
    client: Annotated[
        LMStudioClient,
        Depends(get_inference_client),
    ],
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
    client: Annotated[
        LMStudioChatClient,
        Depends(get_chat_client),
    ],
    store: Annotated[
        ConversationStore,
        Depends(get_conversation_store),
    ],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ChatResponse | JSONResponse:
    """Generate a response with optional temporary conversation context."""

    try:
        system_prompt = load_system_prompt()
    except PromptConfigurationError:
        return chat_unavailable_response("prompt_configuration_error")

    history = (
        store.get_messages(request.conversation_id)
        if request.conversation_id is not None
        else ()
    )

    try:
        reply = await client.generate(
            system_prompt=system_prompt,
            user_input=request.message,
            history=history,
        )
    except InferenceTimeoutError:
        return chat_unavailable_response("timeout")
    except InferenceAuthenticationError:
        return chat_unavailable_response("authentication_failed")
    except InferenceMalformedResponseError:
        return chat_unavailable_response("malformed_response")
    except InferenceUnavailableError:
        return chat_unavailable_response("inference_unavailable")

    if request.conversation_id is not None:
        store.append_exchange(
            request.conversation_id,
            user_message=request.message,
            assistant_message=reply,
        )

    return ChatResponse(
        reply=reply,
        model=settings.lm_studio_model,
    )


class ConversationResetResponse(BaseModel):
    status: Literal["reset"]
    conversation_id: str


@app.delete(
    "/conversations/{conversation_id}",
    response_model=ConversationResetResponse,
    tags=["chat"],
    summary="Reset one temporary conversation",
)
async def reset_conversation(
    conversation_id: ConversationId,
    _: Annotated[None, Depends(require_backend_api_key)],
    store: Annotated[
        ConversationStore,
        Depends(get_conversation_store),
    ],
) -> ConversationResetResponse:
    """Delete the selected temporary conversation history."""

    store.clear(conversation_id)

    return ConversationResetResponse(
        status="reset",
        conversation_id=conversation_id,
    )
