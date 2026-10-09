from contextlib import asynccontextmanager

from fastapi import FastAPI

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

app.include_router(products_router)
app.include_router(sales_router)
app.include_router(reports_router)


@app.get("/")
def health_check():
    return {"status": "healthy", "service": "RetailCore"}


@app.get("/health")
def health():
    return {"status": "ok"}
