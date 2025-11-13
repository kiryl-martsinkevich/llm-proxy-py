"""Anthropic-compatible API router."""

import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from ..clients.anthropic import AnthropicClient
from ..models import AnthropicMessageRequest, ErrorResponse
from ..utils.streaming import stream_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["anthropic"])


async def get_client_for_model(request: Request, model_name: str) -> AnthropicClient:
    """Get Anthropic client for model.

    Args:
        request: FastAPI request
        model_name: Name of the model

    Returns:
        AnthropicClient instance

    Raises:
        HTTPException: If model not found or not an Anthropic model
    """
    app_config = request.app.state.config
    model_config = app_config.get_model_config(model_name)

    if not model_config:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_name}' not found in configuration",
        )

    if model_config.provider.lower() != "anthropic":
        raise HTTPException(
            status_code=400,
            detail=f"Model '{model_name}' is not an Anthropic model",
        )

    retry_config = app_config.get_retry_config(model_name)

    # Get middleware components
    header_manipulator = request.app.state.header_manipulator
    content_transformer = request.app.state.content_transformer
    request_logger = request.app.state.request_logger

    return AnthropicClient(
        model_config=model_config,
        retry_config=retry_config,
        header_manipulator=header_manipulator,
        content_transformer=content_transformer,
        request_logger=request_logger,
        log_requests=app_config.server.log_requests,
        log_responses=app_config.server.log_responses,
    )


@router.post("/messages")
async def create_message(
    request: Request,
    req_data: AnthropicMessageRequest,
):
    """Anthropic messages endpoint.

    Args:
        request: FastAPI request
        req_data: Message request

    Returns:
        Message response or streaming response
    """
    try:
        client = await get_client_for_model(request, req_data.model)

        # Convert request to dict
        data = req_data.model_dump(exclude_none=True)

        # Get model config to check for actual_model_name override
        app_config = request.app.state.config
        model_config = app_config.get_model_config(req_data.model)
        if model_config and model_config.actual_model_name:
            # Override the model name in the request
            data["model"] = model_config.actual_model_name

        if req_data.stream:
            # Streaming response
            response_iter = await client.create_message(data, stream=True)

            async def generate():
                try:
                    async for chunk in stream_response(response_iter, provider="anthropic"):
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
                response = await client.create_message(data, stream=False)
                return response.json()
            finally:
                await client.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.from_exception(
                error_type="internal_error",
                message=str(e),
            ).model_dump(),
        )
