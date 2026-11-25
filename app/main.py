from fastapi import FastAPI

from .models import User  #noqa: F401
from .routes.auth import router

app = FastAPI()


app.include_router(router)

