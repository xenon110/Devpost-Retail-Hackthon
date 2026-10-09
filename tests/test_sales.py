import concurrent.futures
from fastapi.testclient import TestClient


def create_sample_product(client: TestClient, sku: str = "SHOES-101", stock: int = 10, unit_price_paise: int = 15000) -> dict:
    payload = {
        "sku": sku,
        "name": "Sample Product",
        "unit_price_paise": unit_price_paise,
        "stock_quantity": stock,
        "low_stock_threshold": 2,
    }
    resp = client.post("/products", json=payload)
    assert resp.status_code == 201
    return resp.json()


def test_create_sale_success(client: TestClient):
    create_sample_product(client, "SALE-001", 10, 15000)

    sale_payload = {
        "sku": "SALE-001",
        "quantity": 2,
    }
    headers = {"Idempotency-Key": "key-sale-001"}

    response = client.post("/sales", json=sale_payload, headers=headers)
    assert response.status_code == 201

    data = response.json()
    assert data["sku"] == "SALE-001"
    assert data["quantity"] == 2
    assert data["unit_price_paise"] == 15000
    assert data["total_paise"] == 30000
    assert data["idempotency_key"] == "key-sale-001"

    prod_resp = client.get("/products/SALE-001")
    assert prod_resp.json()["stock_quantity"] == 8


def test_sale_idempotency_retry_same_payload(client: TestClient):
    create_sample_product(client, "RETRY-001", 10, 1000)

    sale_payload = {
        "sku": "RETRY-001",
        "quantity": 3,
        "unit_price_paise": 1000,
    }
    headers = {"Idempotency-Key": "key-retry-unique"}

    resp1 = client.post("/sales", json=sale_payload, headers=headers)
    assert resp1.status_code == 201
    data1 = resp1.json()

    resp2 = client.post("/sales", json=sale_payload, headers=headers)
    assert resp2.status_code == 201
    data2 = resp2.json()

    assert data1["id"] == data2["id"]

    prod_resp = client.get("/products/RETRY-001")
    assert prod_resp.json()["stock_quantity"] == 7


def test_sale_idempotency_conflict_different_payload(client: TestClient):
    create_sample_product(client, "CONFLICT-001", 10, 1000)

    headers = {"Idempotency-Key": "key-conflict-test"}

    resp1 = client.post("/sales", json={"sku": "CONFLICT-001", "quantity": 1, "unit_price_paise": 1000}, headers=headers)
    assert resp1.status_code == 201

    resp2 = client.post("/sales", json={"sku": "CONFLICT-001", "quantity": 2, "unit_price_paise": 1000}, headers=headers)
    assert resp2.status_code == 409
    assert "already used for a different request" in resp2.json()["detail"]


def test_sale_product_not_found(client: TestClient):
    headers = {"Idempotency-Key": "key-404"}
    response = client.post("/sales", json={"sku": "MISSING-SKU", "quantity": 1, "unit_price_paise": 500}, headers=headers)
    assert response.status_code == 404


def test_sale_insufficient_stock(client: TestClient):
    create_sample_product(client, "LOWSTOCK-001", 2, 500)
    headers = {"Idempotency-Key": "key-lowstock"}

    response = client.post("/sales", json={"sku": "LOWSTOCK-001", "quantity": 5, "unit_price_paise": 500}, headers=headers)
    assert response.status_code == 409
    assert response.json()["detail"] == "Insufficient stock"


def test_sale_missing_idempotency_header(client: TestClient):
    response = client.post("/sales", json={"sku": "ANY", "quantity": 1, "unit_price_paise": 100})
    assert response.status_code == 422


def test_list_and_get_sales(client: TestClient):
    create_sample_product(client, "LIST-SALE-001", 10, 1000)
    resp = client.post("/sales", json={"sku": "LIST-SALE-001", "quantity": 1}, headers={"Idempotency-Key": "key-list-1"})
    sale_id = resp.json()["id"]

    list_resp = client.get("/sales")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    get_resp = client.get(f"/sales/{sale_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == sale_id


def test_concurrent_sales(client: TestClient):
    create_sample_product(client, "RACE-001", 5, 1000)

    def attempt_sale(index: int):
        headers = {"Idempotency-Key": f"key-race-{index}"}
        payload = {"sku": "RACE-001", "quantity": 1}
        return client.post("/sales", json=payload, headers=headers)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(attempt_sale, i) for i in range(10)]
        results = [f.result() for f in futures]

    status_codes = [r.status_code for r in results]
    successes = status_codes.count(201)
    failures = status_codes.count(409)

    assert successes == 5
    assert failures == 5

    prod_resp = client.get("/products/RACE-001")
    assert prod_resp.json()["stock_quantity"] == 0
