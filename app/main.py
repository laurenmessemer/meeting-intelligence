"""FastAPI application entry point."""
from fastapi import FastAPI
from app.api import chat, ui

app = FastAPI(title="Meeting Intelligence Agent", version="1.0.0")

# Include routers
app.include_router(chat.router)
app.include_router(ui.router)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
