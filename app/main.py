from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.products import router as products_router
from app.api.sales import router as sales_router
from app.api.reports import router as reports_router
from app.database import Base, engine
from app import models


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="RetailCore API",
    description="Reliable retail transaction, inventory microservice & analytics",
    version="0.1.0",
    lifespan=lifespan,
)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(products_router)
app.include_router(sales_router)
app.include_router(reports_router)


@app.get("/demo")
@app.get("/pos")
def get_demo_ui():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Demo UI HTML file not found"}


@app.get("/")
def health_check():
    return {"status": "healthy", "service": "RetailCore", "demo_ui": "/demo"}


@app.get("/health")
def health():
    return {"status": "ok"}
