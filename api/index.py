import traceback
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

try:
    from app.main import app
except Exception as e:
    err_msg = traceback.format_exc()
    app = FastAPI()
    
    @app.get("/{full_path:path}")
    def catch_all(full_path: str):
        return PlainTextResponse(f"Startup Error:\n{err_msg}", status_code=500)
