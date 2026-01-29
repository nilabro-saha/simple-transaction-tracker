from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app.api import router as api_router
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title='Personal Finance Dashboard')

app.include_router(api_router, prefix='/api')

app.mount('/static', StaticFiles(directory='static'), name='static')

@app.get('/', response_class=HTMLResponse)
def dashboard():
    return (BASE_DIR/'static'/'dashboard.html').read_text()