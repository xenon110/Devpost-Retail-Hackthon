
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, Sale
from app.sales_schemas import SaleCreate, SaleResponse

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.post("", response_model=SaleResponse, status_code=201)
def create_sale(
    payload: SaleCreate,
    idempotency_key: str = Header(
        alias="Idempotency-Key", min_length=1, max_length=128
    ),
    db: Session = Depends(get_db),
):
    key = idempotency_key.strip()
    if not key:
        raise HTTPException(status_code=400, detail="Idempotency-Key cannot be blank")

    sku = payload.sku.strip().upper()

    existing = db.scalar(
        select(Sale).where(Sale.idempotency_key == key)
    )

    if existing:
        if (
            existing.sku != sku
            or existing.quantity != payload.quantity
            or existing.unit_price_paise != payload.unit_price_paise
        ):
            raise HTTPException(
                status_code=409,
                detail="Idempotency key was already used for a different request",
            )
        return existing

    product = db.scalar(select(Product).where(Product.sku == sku))
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    result = db.execute(
        update(Product)
        .where(
            Product.id == product.id,
            Product.stock_quantity >= payload.quantity,
        )
        .values(
            stock_quantity=Product.stock_quantity - payload.quantity
        )
    )

    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(status_code=409, detail="Insufficient stock")

    sale = Sale(
        idempotency_key=key,
        product_id=product.id,
        sku=sku,
        quantity=payload.quantity,
        unit_price_paise=payload.unit_price_paise,
        total_paise=payload.quantity * payload.unit_price_paise,
    )
    db.add(sale)

    try:
        db.commit()
        db.refresh(sale)
        return sale
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(Sale).where(Sale.idempotency_key == key)
        )

        if existing:
            if (
                existing.sku == sku
                and existing.quantity == payload.quantity
                and existing.unit_price_paise == payload.unit_price_paise
            ):
                return existing

            raise HTTPException(
                status_code=409,
                detail="Idempotency key was already used for a different request",
            )

        raise HTTPException(
            status_code=409,
            detail="Sale conflicted with another transaction; retry safely",
        )