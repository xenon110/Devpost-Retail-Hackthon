from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product
from app.schemas import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    sku_upper = payload.sku.strip().upper()

    existing = db.scalar(select(Product).where(Product.sku == sku_upper))
    if existing:
        raise HTTPException(
            status_code=409, detail="A product with this SKU already exists"
        )

    product = Product(
        sku=sku_upper,
        name=payload.name,
        stock_quantity=payload.stock_quantity,
        low_stock_threshold=payload.low_stock_threshold,
    )

    db.add(product)
    try:
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="A product with this SKU already exists"
        )

    return product


@router.get("", response_model=list[ProductResponse])
def list_products(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    statement = select(Product).order_by(Product.id).offset(offset).limit(limit)
    return list(db.scalars(statement).all())


@router.get("/{sku}", response_model=ProductResponse)
def get_product(sku: str, db: Session = Depends(get_db)):
    product = db.scalar(select(Product).where(Product.sku == sku.upper()))

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@router.patch("/{sku}", response_model=ProductResponse)
def update_product(
    sku: str, payload: ProductUpdate, db: Session = Depends(get_db)
):
    product = db.scalar(select(Product).where(Product.sku == sku.upper()))

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    if payload.name is not None:
        product.name = payload.name
    if payload.low_stock_threshold is not None:
        product.low_stock_threshold = payload.low_stock_threshold

    db.commit()
    db.refresh(product)
    return product
