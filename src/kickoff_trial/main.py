"""The HTTP API: `create_app()` builds the FastAPI application."""

from fastapi import FastAPI


def create_app() -> FastAPI:
    """Build the app. Tests call this to get a fresh instance."""
    app = FastAPI(title="kickoff-trial")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
