import concurrent.futures

def test_create_sale_success(client):
    # Create product with stock 10
    client.post(
        "/products",
        json={
            "sku": "SHOES-101",
            "name": "Running Shoes",
            "stock_quantity": 10,
            "low_stock_threshold": 3,
        },
    )

    # Perform sale of 2 items
    response = client.post(
        "/sales",
        json={
            "sku": "SHOES-101",
            "quantity": 2,
            "unit_price_paise": 25000,
        },
        headers={"Idempotency-Key": "checkout-001"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["sku"] == "SHOES-101"
    assert data["quantity"] == 2
    assert data["unit_price_paise"] == 25000
    assert data["total_paise"] == 50000
    assert data["idempotency_key"] == "checkout-001"

    # Verify inventory was atomically deducted from 10 to 8
    prod_resp = client.get("/products/SHOES-101")
    assert prod_resp.status_code == 200
    assert prod_resp.json()["stock_quantity"] == 8


def test_sale_idempotency_retry_same_payload(client):
    client.post(
        "/products",
        json={"sku": "SHOES-101", "name": "Running Shoes", "stock_quantity": 10},
    )

    payload = {"sku": "SHOES-101", "quantity": 2, "unit_price_paise": 25000}
    headers = {"Idempotency-Key": "checkout-001"}

    # First request
    res1 = client.post("/sales", json=payload, headers=headers)
    assert res1.status_code == 201
    sale1_id = res1.json()["id"]

    # Duplicate request with same idempotency key
    res2 = client.post("/sales", json=payload, headers=headers)
    assert res2.status_code in (200, 201)
    assert res2.json()["id"] == sale1_id

    # Verify stock quantity was deducted ONLY ONCE (10 - 2 = 8)
    prod_resp = client.get("/products/SHOES-101")
    assert prod_resp.json()["stock_quantity"] == 8


def test_sale_idempotency_conflict_different_payload(client):
    client.post(
        "/products",
        json={"sku": "SHOES-101", "name": "Running Shoes", "stock_quantity": 10},
    )

    headers = {"Idempotency-Key": "checkout-001"}

    # First request with quantity 2
    res1 = client.post(
        "/sales",
        json={"sku": "SHOES-101", "quantity": 2, "unit_price_paise": 25000},
        headers=headers,
    )
    assert res1.status_code == 201

    # Second request with SAME idempotency key but quantity 5
    res2 = client.post(
        "/sales",
        json={"sku": "SHOES-101", "quantity": 5, "unit_price_paise": 25000},
        headers=headers,
    )
    assert res2.status_code == 409
    assert "already used for a different request" in res2.json()["detail"]


def test_sale_product_not_found(client):
    response = client.post(
        "/sales",
        json={"sku": "NONEXISTENT", "quantity": 1, "unit_price_paise": 1000},
        headers={"Idempotency-Key": "checkout-999"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_sale_insufficient_stock(client):
    client.post(
        "/products",
        json={"sku": "SHOES-101", "name": "Running Shoes", "stock_quantity": 1},
    )

    response = client.post(
        "/sales",
        json={"sku": "SHOES-101", "quantity": 5, "unit_price_paise": 25000},
        headers={"Idempotency-Key": "checkout-002"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Insufficient stock"

    # Stock remains 1
    prod_resp = client.get("/products/SHOES-101")
    assert prod_resp.json()["stock_quantity"] == 1


def test_sale_missing_idempotency_header(client):
    response = client.post(
        "/sales",
        json={"sku": "SHOES-101", "quantity": 1, "unit_price_paise": 1000},
    )
    assert response.status_code == 422


def test_concurrent_sales(client):
    # Initial stock is 5
    client.post(
        "/products",
        json={"sku": "LIMITED-1", "name": "Limited Edition", "stock_quantity": 5},
    )

    def attempt_sale(index):
        return client.post(
            "/sales",
            json={"sku": "LIMITED-1", "quantity": 1, "unit_price_paise": 10000},
            headers={"Idempotency-Key": f"concurrent-key-{index}"},
        )

    # 10 threads trying to purchase 1 item each
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(attempt_sale, i) for i in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    successes = [r for r in results if r.status_code == 201]
    failures = [r for r in results if r.status_code == 409]

    assert len(successes) == 5
    assert len(failures) == 5

    # Verify final stock is exactly 0 and never negative
    prod_resp = client.get("/products/LIMITED-1")
    assert prod_resp.json()["stock_quantity"] == 0
