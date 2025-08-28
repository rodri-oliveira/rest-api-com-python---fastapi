# uvicorn main:app --reload // para rodar o projeto

from fastapi import FastAPI
from routes.auth_routes import auth_router
from routes.order_routes import order_router
from passlib.context import CryptContext
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

app = FastAPI()

app.include_router(auth_router)
app.include_router(order_router)