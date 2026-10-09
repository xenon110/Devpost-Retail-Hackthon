def test_create_product_success(client):
    response = client.post(
        "/products",
        json={
            "sku": "SHOES-101",
            "name": "Running Shoes",
            "stock_quantity": 10,
            "low_stock_threshold": 3,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["sku"] == "SHOES-101"
    assert data["name"] == "Running Shoes"
    assert data["stock_quantity"] == 10
    assert data["low_stock_threshold"] == 3
    assert "id" in data
    assert "created_at" in data


def test_create_product_negative_stock_validation(client):
    response = client.post(
        "/products",
        json={
            "sku": "SHOES-102",
            "name": "Trail Shoes",
            "stock_quantity": -5,
            "low_stock_threshold": 3,
        },
    )
    assert response.status_code == 422


def test_create_duplicate_sku(client):
    payload = {
        "sku": "SHOES-101",
        "name": "Running Shoes",
        "stock_quantity": 10,
        "low_stock_threshold": 3,
    }
    client.post("/products", json=payload)
    response = client.post("/products", json=payload)
    assert response.status_code == 409
    assert response.json()["detail"] == "A product with this SKU already exists"


def test_get_product_by_sku(client):
    client.post(
        "/products",
        json={
            "sku": "SHOES-101",
            "name": "Running Shoes",
            "stock_quantity": 10,
            "low_stock_threshold": 3,
        },
    )
    response = client.get("/products/SHOES-101")
    assert response.status_code == 200
    assert response.json()["sku"] == "SHOES-101"


def test_get_nonexistent_product(client):
    response = client.get("/products/NONEXISTENT")
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_list_products(client):
    client.post(
        "/products",
        json={"sku": "SKU-1", "name": "Item 1", "stock_quantity": 5},
    )
    client.post(
        "/products",
        json={"sku": "SKU-2", "name": "Item 2", "stock_quantity": 15},
    )
    response = client.get("/products")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2
    assert items[0]["sku"] == "SKU-1"
    assert items[1]["sku"] == "SKU-2"
