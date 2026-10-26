# Vercel serverless entry: exposes the FastAPI app (static frontend is served by Vercel's CDN).
from backend.app.main import app  # noqa: F401
