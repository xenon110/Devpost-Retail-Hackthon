# RetailCore 🛍️
> **Real-Time Retail POS Microservice with Idempotent Checkout, Atomic Stock Control, & Financial Reconciliation**
> 
> *Built for The Bounty Sprint Hackathon — Track 3: Real-Time Retail Microservices*
> **GitHub Repository:** [xenon110/Devpost-Retail-Hackthon](https://github.com/xenon110/Devpost-Retail-Hackthon)

---

## 📌 Problem Statement

In fast-paced physical retail environments (such as shoe stores, clothing shops, or high-volume supermarkets with multiple cash registers):

1. **Inventory Over-selling & Race Conditions:**
   When two cash registers simultaneously attempt to sell the last remaining unit of an item, standard backend logic can lead to race conditions where both sales succeed. This results in negative stock, unfulfillable customer orders, and inventory discrepancies.

2. **Duplicate Billing & Stock Deductions on Network Retries:**
   In offline-first or poor network environments, a cashier's request might successfully process on the server, but the network connection drops before the client receives the HTTP response. When the cashier retries the checkout request, naive APIs execute a second sale—deducting stock twice and overcharging the customer.

3. **Lack of Real-Time Auditability & Reconciliation:**
   Retail managers require instant visibility into daily sales totals (Z-Reports), itemized receipts, and real-time alerts when high-demand inventory hits critically low levels or goes out of stock.

---

## 💡 The Solution: RetailCore

**RetailCore** is a high-performance backend microservice engineered to guarantee transaction safety, inventory accuracy, and financial auditability under all network and concurrency conditions.

### Core Architectural Pillars:

1. **Atomic Inventory Decrement:**
   Executes conditional SQL updates (`WHERE id = ? AND stock_quantity >= ?`) at the database engine level. This guarantees stock can **never** drop below `0`, regardless of how many cash registers attempt concurrent checkouts.

2. **Strict Idempotency Engine:**
   Every sales transaction requires a unique `Idempotency-Key` HTTP header. 
   - **Identical Retries:** Returns the original sale response instantly without re-executing inventory deductions or duplicating charges.
   - **Payload Mismatches:** Detects if an idempotency key is reused with modified items or quantities and returns HTTP `409 Conflict`.

3. **Transaction Rollback & Isolation:**
   Product updates and sale record insertions execute inside single atomic database transactions. If any step fails, the entire transaction rolls back automatically.

4. **Track 3 Retail Analytics & Reconciliation:**
   - **Itemized Receipts (`GET /reports/receipts/{sale_id}`):** Generates structured POS receipts with SKU, quantity, unit price, formatted INR currency (`₹250.00`), and receipt serial numbers (`REC-000001`).
   - **Daily Z-Report Reconciliation (`GET /reports/z-report`):** Reconciles daily transaction counts, total items sold, and total revenue.
   - **Stock-Out & Low-Stock Alerts (`GET /reports/stock-alerts`):** Real-time monitoring of items at or below low-stock thresholds or completely depleted.

---

## 🛠️ Technology Stack

- **Language:** Python 3.14+
- **Framework:** FastAPI (ASGI async microservice framework)
- **ORM & DB:** SQLAlchemy 2.0+ (SQLite with thread isolation & WAL mode)
- **Validation:** Pydantic v2
- **Testing:** Pytest, HTTPX, ThreadPoolExecutor (10-thread concurrency testing)
- **Containerization:** Docker & Docker Compose

---

## 📂 Project Architecture

```text
RetailCore/
├── app/
│   ├── api/
│   │   ├── products.py      # POST /products, GET /products, GET /products/{sku}
│   │   ├── sales.py         # POST /sales (Atomic stock deduction + Idempotency engine)
│   │   └── reports.py       # Receipts, Z-Report Reconciliation, Stock-out Alerts
│   ├── database.py          # SQLAlchemy Engine, Session, SQLite adapters
│   ├── main.py              # FastAPI application & router registration
│   ├── models.py            # Product & Sale ORM Models (Check Constraints & UTC timestamps)
│   ├── schemas.py           # Product Pydantic schemas
│   └── sales_schemas.py     # Sale Pydantic schemas
├── tests/
│   ├── conftest.py          # Isolated SQLite database fixtures with WAL mode
│   ├── test_products.py     # Product creation & validation tests
│   ├── test_sales.py        # Idempotency, 10-thread race condition, & inventory tests
│   └── test_reports.py      # Receipts, Z-Report, & stock alert tests
├── Dockerfile               # Container definition
├── docker-compose.yml       # Local multi-container orchestration
└── requirements.txt         # Dependencies
```

---

## 🚀 Quick Start Guide

### 1. Local Setup
```cmd
cd C:\Users\yashs\RetailCore
.venv\Scripts\activate
python -m uvicorn app.main:app --reload
```
Interactive OpenAPI / Swagger Documentation available at:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

---

## 🧪 Comprehensive Test Suite

Run the full automated test suite:

```cmd
pytest -v
```

### Verified Test Suite (17/17 Passing):
- `test_create_product_success` (HTTP 201)
- `test_create_product_negative_stock_validation` (HTTP 422)
- `test_create_duplicate_sku` (HTTP 409)
- `test_get_product_by_sku` & `test_list_products`
- `test_create_sale_success` (Stock atomically decrements from 10 to 8)
- `test_sale_idempotency_retry_same_payload` (Returns original sale; stock remains 8)
- `test_sale_idempotency_conflict_different_payload` (HTTP 409 Conflict)
- `test_sale_insufficient_stock` (HTTP 409 Conflict; stock unaffected)
- `test_concurrent_sales` (10 simultaneous threads purchasing 5 items; exactly 5 succeed, 5 fail, final stock = 0)
- `test_get_receipt_success` (Receipt ID `REC-000001`, formatted currency)
- `test_z_report_reconciliation` (Reconciles transaction count & revenue total)
- `test_stock_alerts` (Identifies low-stock and stock-out products)

---

## 🐳 Docker Containerization

```cmd
docker-compose up --build
```

---

## 📜 Hackathon Track
- **Event:** The Bounty Sprint — NextGen POS: Offline-First Developer Sprint
- **Track:** Track 3 — Real-Time Retail Microservices
- **License:** MIT License
