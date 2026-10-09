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

---

## 🐳 Docker & Containerization Guide

### 1. Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v20.10+)
- Docker Compose (v2.0+)

### 2. Required Environment Variables
Configuration is managed via environment variables. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default parameters:
- `ENVIRONMENT`: `production` (or `development`)
- `PORT`: `8000`
- `DATABASE_URL`: `sqlite:////app/data/retailcore.db`

### 3. Build & Run Services
To build the container image and start RetailCore in the background:
```bash
docker compose up -d --build
```

### 4. Local Access URLs
- **Interactive POS Operations Console:** [http://localhost:8000/demo](http://localhost:8000/demo)
- **OpenAPI / Swagger Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Liveness Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
- **Database Readiness Check:** [http://localhost:8000/ready](http://localhost:8000/ready)

### 5. Inspect Logs & Health Status
```bash
# View service container status & health check results
docker compose ps

# Follow live application container logs
docker compose logs -f retailcore
```

### 6. Database Volume Persistence
Database storage is maintained inside a dedicated, persistent named volume (`retailcore_data:/app/data`).
- Stopping or restarting containers via `docker compose stop` or `docker compose down` **preserves** all saved products and completed sales history.
- ⚠️ *Note on Data Safety:* Avoid running `docker compose down -v` unless you explicitly intend to purge all persistent database records.

### 7. Stopping Services
```bash
docker compose down
```

---

## 🧪 Comprehensive Automated Test Suite

Run the full 19-test automated suite:

```cmd
python -m pytest -v
```

### Verified Test Suite (19/19 Passing):
- `test_create_product_success` (HTTP 201)
- `test_create_product_negative_stock_validation` (HTTP 422)
- `test_create_duplicate_sku` (HTTP 409)
- `test_get_product_by_sku` & `test_list_products`
- `test_update_product` (HTTP 200)
- `test_create_sale_success` (Stock atomically decrements from 10 to 8)
- `test_sale_idempotency_retry_same_payload` (Returns original sale; stock remains 8)
- `test_sale_idempotency_conflict_different_payload` (HTTP 409 Conflict)
- `test_sale_insufficient_stock` (HTTP 409 Conflict; stock unaffected)
- `test_concurrent_sales` (10 simultaneous threads purchasing 5 items; exactly 5 succeed, 5 fail, final stock = 0)
- `test_get_receipt_success` (Receipt ID `REC-000001`, formatted currency)
- `test_z_report_reconciliation` (Reconciles transaction count & revenue total)
- `test_stock_alerts` (Identifies low-stock and stock-out products)

---

## 📜 Hackathon Track
- **Event:** The Bounty Sprint — NextGen POS: Offline-First Developer Sprint
- **Track:** Track 3 — Real-Time Retail Microservices
- **License:** MIT License
