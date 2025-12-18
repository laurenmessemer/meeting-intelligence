"""FastAPI application entry point."""
from fastapi import FastAPI
from app.api import chat, ui
from fastapi.staticfiles import StaticFiles
from app.runtime.mode import get_app_mode

app = FastAPI(title="Meeting Intelligence Agent", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
print(f"⚠️⚠️⚠️ Application starting in APP_MODE={get_app_mode().upper()}⚠️⚠️⚠️")

# Include routers
app.include_router(chat.router)
app.include_router(ui.router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "mode": get_app_mode(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
