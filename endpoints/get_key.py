import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import json

from dotenv import load_dotenv
load_dotenv()

router = APIRouter()

templates = Jinja2Templates(directory="templates")



aikey= os.environ.get("ONZEENVKEY")

@router.get("/get_key")
def index():
    aikey= os.environ.get("ONZEENVKEY")
    return aikey

index()