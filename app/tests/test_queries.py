def test_get_all_users(client):
    response = client.get("/api/query?filter_type=all")
    assert response.status_code == 200
    body = response.json()
    assert "results" in body
    assert isinstance(body["results"], list)
    assert len(body["results"]) >= 2


def test_filter_by_status_active(client):
    response = client.get("/api/query?filter_type=status&status=active")
    assert response.status_code == 200
    results = response.json()["results"]
    assert all(u["status"] == "active" for u in results)


def test_filter_by_status_inactive(client):
    response = client.get("/api/query?filter_type=status&status=inactive")
    assert response.status_code == 200
    results = response.json()["results"]
    assert all(u["status"] == "inactive" for u in results)


def test_filter_by_country(client):
    response = client.get("/api/query?filter_type=country&country=UK")
    assert response.status_code == 200
    results = response.json()["results"]
    assert all(u["country"] == "UK" for u in results)


def test_search_by_name(client):
    response = client.get("/api/query?filter_type=name_search&name_search=Alice")
    assert response.status_code == 200
    results = response.json()["results"]
    assert any("Alice" in u["name"] for u in results)


def test_filter_by_date_range(client):
    response = client.get(
        "/api/query?filter_type=date_range&date_from=2025-01-01&date_to=2025-03-01"
    )
    assert response.status_code == 200
    body = response.json()
    assert "results" in body


def test_result_shape(client):
    response = client.get("/api/query?filter_type=all")
    results = response.json()["results"]
    assert len(results) > 0
    u = results[0]
    for key in ("id", "name", "email", "status", "country", "created_at"):
        assert key in u
