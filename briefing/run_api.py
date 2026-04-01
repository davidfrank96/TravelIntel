"""Run the TravelIntel briefing API with Uvicorn."""
import os

import uvicorn


if __name__ == "__main__":
    host = os.getenv("BRIEFING_API_HOST", "0.0.0.0")
    port = int(os.getenv("BRIEFING_API_PORT", "8000"))
    uvicorn.run("briefing.api:app", host=host, port=port, reload=False)
