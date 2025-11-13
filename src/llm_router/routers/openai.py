"""OpenAI-compatible API router."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from ..clients.openai import OpenAIClient
from ..clients.ollama import OllamaClient
from ..models import (
    ErrorResponse,
    OpenAIChatCompletionRequest,
    OpenAICompletionRequest,
)
from ..utils.streaming import stream_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["openai"])


async def get_client_for_model(request: Request, model_name: str) -> OpenAIClient | OllamaClient:
    """Get appropriate client for model.

    Args:
        request: FastAPI request
        model_name: Name of the model

    Returns:
        Client instance

    Raises:
        HTTPException: If model not found or configuration error
    """
    app_config = request.app.state.config
    model_config = app_config.get_model_config(model_name)

    if not model_config:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_name}' not found in configuration",
        )

    retry_config = app_config.get_retry_config(model_name)

    # Get middleware components
    header_manipulator = request.app.state.header_manipulator
    content_transformer = request.app.state.content_transformer
    request_logger = request.app.state.request_logger

    # Create appropriate client based on provider
    if model_config.provider.lower() == "ollama":
        return OllamaClient(
            model_config=model_config,
            retry_config=retry_config,
            header_manipulator=header_manipulator,
            content_transformer=content_transformer,
            request_logger=request_logger,
            log_requests=app_config.server.log_requests,
            log_responses=app_config.server.log_responses,
        )
    else:
        return OpenAIClient(
            model_config=model_config,
            retry_config=retry_config,
            header_manipulator=header_manipulator,
            content_transformer=content_transformer,
            request_logger=request_logger,
            log_requests=app_config.server.log_requests,
            log_responses=app_config.server.log_responses,
        )


@router.post("/chat/completions")
async def chat_completions(
    request: Request,
    req_data: OpenAIChatCompletionRequest,
):
    """OpenAI chat completions endpoint.

    Args:
        request: FastAPI request
        req_data: Chat completion request

    Returns:
        Chat completion response or streaming response
    """
    try:
        client = await get_client_for_model(request, req_data.model)

        # Convert request to dict
        data = req_data.model_dump(exclude_none=True)

        if req_data.stream:
            # Streaming response
            response_iter = await client.chat_completion(data, stream=True)

            async def generate():
                try:
                    async for chunk in stream_response(response_iter, provider="openai"):
                        yield chunk
                finally:
                    await client.close()

            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                },
            )
        else:
            # Non-streaming response
            try:
                response = await client.chat_completion(data, stream=False)
                return response.json()
            finally:
                await client.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat_completions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.from_exception(
                error_type="internal_error",
                message=str(e),
            ).model_dump(),
        )


@router.post("/completions")
async def completions(
    request: Request,
    req_data: OpenAICompletionRequest,
):
    """OpenAI completions endpoint.

    Args:
        request: FastAPI request
        req_data: Completion request

    Returns:
        Completion response or streaming response
    """
    try:
        client = await get_client_for_model(request, req_data.model)

        # Convert request to dict
        data = req_data.model_dump(exclude_none=True)

        if req_data.stream:
            # Streaming response
            response_iter = await client.completion(data, stream=True)

            async def generate():
                try:
                    async for chunk in stream_response(response_iter, provider="openai"):
                        yield chunk
                finally:
                    await client.close()

            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                },
            )
        else:
            # Non-streaming response
            try:
                response = await client.completion(data, stream=False)
                return response.json()
            finally:
                await client.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in completions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.from_exception(
                error_type="internal_error",
                message=str(e),
            ).model_dump(),
        )
