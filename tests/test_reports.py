from fastapi.testclient import TestClient


def create_sample_product(client: TestClient, sku: str = "PROD-REP-1", stock: int = 10, unit_price_paise: int = 5000):
    payload = {
        "sku": sku,
        "name": "Report Item",
        "unit_price_paise": unit_price_paise,
        "stock_quantity": stock,
        "low_stock_threshold": 3,
    }
    client.post("/products", json=payload)


def test_get_receipt_success(client: TestClient):
    create_sample_product(client, "REC-SKU-001", 10, 2500)
    sale_resp = client.post(
        "/sales",
        json={"sku": "REC-SKU-001", "quantity": 2},
        headers={"Idempotency-Key": "key-receipt-test"},
    )
    sale_id = sale_resp.json()["id"]

    response = client.get(f"/reports/receipts/{sale_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["sale_id"] == sale_id
    assert data["item"]["sku"] == "REC-SKU-001"
    assert data["item"]["quantity"] == 2
    assert data["item"]["unit_price_paise"] == 2500
    assert data["item"]["total_paise"] == 5000
    assert "₹50.00" in data["item"]["total_formatted"]


def test_get_receipt_not_found(client: TestClient):
    response = client.get("/reports/receipts/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Sale not found"


def test_z_report_reconciliation(client: TestClient):
    create_sample_product(client, "Z-SKU-001", 10, 5000)

    # Sale 1
    client.post(
        "/sales",
        json={"sku": "Z-SKU-001", "quantity": 1},
        headers={"Idempotency-Key": "key-z-1"},
    )
    # Sale 2
    client.post(
        "/sales",
        json={"sku": "Z-SKU-001", "quantity": 2},
        headers={"Idempotency-Key": "key-z-2"},
    )
    # Retry Sale 1 (Should NOT duplicate revenue)
    client.post(
        "/sales",
        json={"sku": "Z-SKU-001", "quantity": 1},
        headers={"Idempotency-Key": "key-z-1"},
    )

    response = client.get("/reports/z-report")
    assert response.status_code == 200

    data = response.json()
    assert data["summary"]["total_transactions"] >= 2
    assert data["summary"]["total_items_sold"] >= 3
    assert data["summary"]["total_revenue_paise"] >= 15000


def test_stock_alerts(client: TestClient):
    create_sample_product(client, "ALERT-ZERO", 0, 1000)
    create_sample_product(client, "ALERT-LOW", 2, 1000)
    create_sample_product(client, "ALERT-OK", 20, 1000)

    response = client.get("/reports/stock-alerts")
    assert response.status_code == 200

    data = response.json()
    assert data["stock_out_count"] >= 1
    assert data["low_stock_count"] >= 1
