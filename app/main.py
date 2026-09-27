from fastapi import FastAPI

from app.database import Base, engine

from .models import User  #noqa: F401
from .routes.auth import router

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(router)

