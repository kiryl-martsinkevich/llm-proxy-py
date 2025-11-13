"""Main FastAPI application for LLM Router Service."""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .config import AppConfig
from .middleware.headers import HeaderManipulator
from .middleware.logging import RequestLogger
from .middleware.transform import ContentTransformer
from .routers import anthropic, openai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    Args:
        app: FastAPI application
    """
    # Startup
    logger.info("Starting LLM Router Service...")
    logger.info(f"Loaded {len(app.state.config.models)} model(s)")
    logger.info(f"Loaded {len(app.state.config.transformations)} transformation(s)")

    yield

    # Shutdown
    logger.info("Shutting down LLM Router Service...")


def create_app(config_path: str = "config.yaml") -> FastAPI:
    """Create FastAPI application.

    Args:
        config_path: Path to configuration file

    Returns:
        FastAPI application
    """
    # Load configuration
    try:
        config = AppConfig.from_yaml(config_path)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        logger.info("Please create a configuration file. See config.example.yaml for reference.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Create FastAPI app
    app = FastAPI(
        title="LLM Router Service",
        description="Unified interface for multiple LLM providers",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Store configuration and middleware in app state
    app.state.config = config
    app.state.header_manipulator = HeaderManipulator(config.header_rules)
    app.state.content_transformer = ContentTransformer(config.transformations)
    app.state.request_logger = RequestLogger(mask_api_keys=config.server.mask_api_keys)

    # Register routers
    app.include_router(openai.router)
    app.include_router(anthropic.router)

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "internal_error",
                    "message": "An internal error occurred",
                }
            },
        )

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "llm-router",
            "version": "0.1.0",
            "models": list(config.models.keys()),
        }

    return app


def cli():
    """CLI entry point for running the server."""
    import argparse

    parser = argparse.ArgumentParser(description="LLM Router Service")
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "--host",
        type=str,
        help="Host to bind to (overrides config)",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port to bind to (overrides config)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    args = parser.parse_args()

    # Load config to get server settings
    try:
        config = AppConfig.from_yaml(args.config)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {args.config}")
        logger.info("Please create a configuration file. See config.example.yaml for reference.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    host = args.host or config.server.host
    port = args.port or config.server.port

    logger.info(f"Starting server on {host}:{port}")

    # Run server
    uvicorn.run(
        "llm_router.main:create_app",
        host=host,
        port=port,
        reload=args.reload,
        factory=True,
        app_dir=str(Path(__file__).parent.parent),
    )


if __name__ == "__main__":
    cli()
