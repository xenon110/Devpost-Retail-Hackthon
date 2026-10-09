def test_get_receipt_success(client):
    # 1. Create product
    client.post(
        "/products",
        json={"sku": "SHOES-101", "name": "Running Shoes", "stock_quantity": 10},
    )

    # 2. Perform sale
    sale_resp = client.post(
        "/sales",
        json={"sku": "SHOES-101", "quantity": 2, "unit_price_paise": 25000},
        headers={"Idempotency-Key": "receipt-test-key-1"},
    )
    sale_id = sale_resp.json()["id"]

    # 3. Retrieve receipt
    response = client.get(f"/reports/receipts/{sale_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["sale_id"] == sale_id
    assert data["receipt_id"] == f"REC-{sale_id:06d}"
    assert data["store_name"] == "RetailCore POS"
    assert data["item"]["sku"] == "SHOES-101"
    assert data["item"]["name"] == "Running Shoes"
    assert data["item"]["quantity"] == 2
    assert data["item"]["unit_price_formatted"] == "₹250.00"
    assert data["item"]["total_formatted"] == "₹500.00"


def test_get_receipt_not_found(client):
    response = client.get("/reports/receipts/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Sale not found"


def test_z_report_reconciliation(client):
    client.post(
        "/products",
        json={"sku": "SHIRT-1", "name": "Cotton Shirt", "stock_quantity": 50},
    )

    client.post(
        "/sales",
        json={"sku": "SHIRT-1", "quantity": 3, "unit_price_paise": 15000},
        headers={"Idempotency-Key": "z-key-1"},
    )
    client.post(
        "/sales",
        json={"sku": "SHIRT-1", "quantity": 2, "unit_price_paise": 15000},
        headers={"Idempotency-Key": "z-key-2"},
    )

    response = client.get("/reports/z-report")
    assert response.status_code == 200
    data = response.json()

    summary = data["summary"]
    assert summary["total_transactions"] == 2
    assert summary["total_items_sold"] == 5
    assert summary["total_revenue_paise"] == 75000
    assert summary["total_revenue_formatted"] == "₹750.00"


def test_stock_alerts(client):
    # Product 1: Out of stock (0)
    client.post(
        "/products",
        json={"sku": "OUT-1", "name": "Out of Stock Item", "stock_quantity": 0, "low_stock_threshold": 5},
    )
    # Product 2: Low stock (2 <= 5)
    client.post(
        "/products",
        json={"sku": "LOW-1", "name": "Low Stock Item", "stock_quantity": 2, "low_stock_threshold": 5},
    )
    # Product 3: Normal stock (20 > 5)
    client.post(
        "/products",
        json={"sku": "NORM-1", "name": "Normal Item", "stock_quantity": 20, "low_stock_threshold": 5},
    )

    response = client.get("/reports/stock-alerts")
    assert response.status_code == 200
    data = response.json()

    assert data["stock_out_count"] == 1
    assert data["low_stock_count"] == 1
    assert data["stock_out_products"][0]["sku"] == "OUT-1"
    assert data["low_stock_products"][0]["sku"] == "LOW-1"
