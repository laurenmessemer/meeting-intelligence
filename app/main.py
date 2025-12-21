"""FastAPI application entry point."""
from fastapi import FastAPI
from app.api import chat, ui
from fastapi.staticfiles import StaticFiles
from app.runtime.mode import get_app_mode
from app.middleware.demo_auth import DemoBasicAuthMiddleware
from init_db import init_db
import os


app = FastAPI(title="Meeting Intelligence Agent", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
print(f"⚠️⚠️⚠️ Application starting in APP_MODE={get_app_mode().upper()}⚠️⚠️⚠️")
app.add_middleware(DemoBasicAuthMiddleware)

# Include routers
app.include_router(chat.router)
app.include_router(ui.router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "mode": get_app_mode(),
    }

@app.on_event("startup")
def on_startup():
    init_db()


if __name__ == "__main__":
    import uvicorn

    # Heroku sets PORT; local defaults to 8000.
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)