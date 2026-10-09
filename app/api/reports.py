from datetime import datetime, date, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, Sale

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])


def format_paise(paise: int) -> str:
    rupees = paise / 100.0
    return f"₹{rupees:,.2f}"


@router.get("/receipts/{sale_id}")
def get_receipt(sale_id: int, db: Session = Depends(get_db)):
    sale = db.scalar(select(Sale).where(Sale.id == sale_id))
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    product = db.scalar(select(Product).where(Product.id == sale.product_id))
    product_name = product.name if product else "Unknown Product"

    return {
        "receipt_id": f"REC-{sale.id:06d}",
        "sale_id": sale.id,
        "store_name": "RetailCore POS",
        "timestamp": sale.created_at.isoformat(),
        "item": {
            "sku": sale.sku,
            "name": product_name,
            "quantity": sale.quantity,
            "unit_price_paise": sale.unit_price_paise,
            "unit_price_formatted": format_paise(sale.unit_price_paise),
            "total_paise": sale.total_paise,
            "total_formatted": format_paise(sale.total_paise),
        },
        "idempotency_key": sale.idempotency_key,
    }


@router.get("/z-report")
def get_z_report(
    report_date: Optional[str] = Query(
        default=None, description="Date in YYYY-MM-DD format. Defaults to today."
    ),
    db: Session = Depends(get_db),
):
    if report_date:
        try:
            target_date = datetime.strptime(report_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        target_date = datetime.now(timezone.utc).date()

    # Query sales for the given target date
    sales = db.scalars(select(Sale)).all()
    filtered_sales = [
        s for s in sales if s.created_at.date() == target_date
    ]

    total_transactions = len(filtered_sales)
    total_items_sold = sum(s.quantity for s in filtered_sales)
    total_revenue_paise = sum(s.total_paise for s in filtered_sales)

    return {
        "report_date": target_date.isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_transactions": total_transactions,
            "total_items_sold": total_items_sold,
            "total_revenue_paise": total_revenue_paise,
            "total_revenue_formatted": format_paise(total_revenue_paise),
        },
        "transactions": [
            {
                "sale_id": s.id,
                "sku": s.sku,
                "quantity": s.quantity,
                "total_paise": s.total_paise,
                "total_formatted": format_paise(s.total_paise),
                "timestamp": s.created_at.isoformat(),
            }
            for s in filtered_sales
        ],
    }


@router.get("/stock-alerts")
def get_stock_alerts(db: Session = Depends(get_db)):
    products = db.scalars(select(Product)).all()

    stock_out = [
        {
            "id": p.id,
            "sku": p.sku,
            "name": p.name,
            "stock_quantity": p.stock_quantity,
            "low_stock_threshold": p.low_stock_threshold,
        }
        for p in products
        if p.stock_quantity == 0
    ]

    low_stock = [
        {
            "id": p.id,
            "sku": p.sku,
            "name": p.name,
            "stock_quantity": p.stock_quantity,
            "low_stock_threshold": p.low_stock_threshold,
        }
        for p in products
        if 0 < p.stock_quantity <= p.low_stock_threshold
    ]

    return {
        "stock_out_count": len(stock_out),
        "low_stock_count": len(low_stock),
        "stock_out_products": stock_out,
        "low_stock_products": low_stock,
    }
