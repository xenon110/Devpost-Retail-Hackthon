from fastapi.testclient import TestClient


def test_create_product_success(client: TestClient):
    payload = {
        "sku": "shoes-101",
        "name": "Running Shoes",
        "stock_quantity": 10,
        "low_stock_threshold": 3,
    }

    response = client.post("/products", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["sku"] == "SHOES-101"
    assert data["name"] == "Running Shoes"
    assert data["stock_quantity"] == 10
    assert data["low_stock_threshold"] == 3
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_product_negative_stock_validation(client: TestClient):
    payload = {
        "sku": "BAD-STOCK",
        "name": "Invalid Item",
        "stock_quantity": -5,
        "low_stock_threshold": 3,
    }

    response = client.post("/products", json=payload)
    assert response.status_code == 422


def test_create_duplicate_sku(client: TestClient):
    payload = {
        "sku": "DUPLICATE-SKU",
        "name": "Item A",
        "stock_quantity": 5,
        "low_stock_threshold": 1,
    }

    resp1 = client.post("/products", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/products", json=payload)
    assert resp2.status_code == 409
    assert resp2.json()["detail"] == "A product with this SKU already exists"


def test_get_product_by_sku(client: TestClient):
    payload = {
        "sku": "GET-SKU-001",
        "name": "Test Item",
        "stock_quantity": 20,
        "low_stock_threshold": 5,
    }
    client.post("/products", json=payload)

    response = client.get("/products/GET-SKU-001")
    assert response.status_code == 200
    assert response.json()["sku"] == "GET-SKU-001"


def test_get_nonexistent_product(client: TestClient):
    response = client.get("/products/NONEXISTENT-SKU")
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_list_products(client: TestClient):
    client.post("/products", json={"sku": "P1", "name": "Prod 1", "stock_quantity": 10})
    client.post("/products", json={"sku": "P2", "name": "Prod 2", "stock_quantity": 20})

    response = client.get("/products?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_update_product(client: TestClient):
    client.post("/products", json={"sku": "UPDATE-001", "name": "Original Name", "stock_quantity": 10, "low_stock_threshold": 2})

    response = client.patch("/products/UPDATE-001", json={"name": "Updated Name", "low_stock_threshold": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["low_stock_threshold"] == 5
