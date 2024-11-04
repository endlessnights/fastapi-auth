# app/csrf.py

from fastapi_csrf_protect import CsrfProtect
from pydantic import BaseModel
import os

class CsrfSettings(BaseModel):
    secret_key: str = os.getenv("CSRF_SECRET_KEY", "YOUR_SECRET_KEY_HERE")

@CsrfProtect.load_config
def get_config():
    return CsrfSettings()
