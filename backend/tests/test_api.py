"""API integration tests using in-memory SQLite."""
import pytest
import pytest_asyncio


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_create_farmer(client):
    response = await client.post("/api/v1/farmers/", json={
        "name": "Ravi Kumar",
        "phone": "+91-9876543210",
        "location_name": "Bangalore Rural, Karnataka",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Ravi Kumar"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_farm(client):
    # Create farmer first
    farmer_resp = await client.post("/api/v1/farmers/", json={"name": "Test Farmer"})
    farmer_id = farmer_resp.json()["id"]

    response = await client.post("/api/v1/farms/", json={
        "farmer_id": farmer_id,
        "name": "Test Farm",
        "latitude": 13.08,
        "longitude": 77.59,
        "area_hectares": 1.5,
        "soil_type": "loam",
        "irrigation_method": "drip",
        "water_storage_litres": 50000,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Farm"
    assert data["area_hectares"] == 1.5


@pytest.mark.asyncio
async def test_create_crop(client):
    farmer_resp = await client.post("/api/v1/farmers/", json={"name": "Crop Test Farmer"})
    farmer_id = farmer_resp.json()["id"]
    farm_resp = await client.post("/api/v1/farms/", json={
        "farmer_id": farmer_id,
        "name": "Crop Farm",
        "area_hectares": 1.0,
        "irrigation_method": "drip",
    })
    farm_id = farm_resp.json()["id"]

    response = await client.post("/api/v1/crops/", json={
        "farm_id": farm_id,
        "crop_type": "wheat",
        "growth_stage": "mid",
        "soil_moisture_pct": 45.0,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["crop_type"] == "wheat"


@pytest.mark.asyncio
async def test_record_water_storage(client):
    farmer_resp = await client.post("/api/v1/farmers/", json={"name": "Water Test Farmer"})
    farmer_id = farmer_resp.json()["id"]
    farm_resp = await client.post("/api/v1/farms/", json={
        "farmer_id": farmer_id, "name": "Water Farm", "area_hectares": 1.0,
    })
    farm_id = farm_resp.json()["id"]

    response = await client.post("/api/v1/water/", json={
        "farm_id": farm_id,
        "storage_litres": 35000,
        "source": "farm pond",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["storage_litres"] == 35000


@pytest.mark.asyncio
async def test_recommendation_missing_farm(client):
    response = await client.post("/api/v1/recommendations/", json={"farm_id": 99999})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_recommendation(client):
    """Full recommendation pipeline with demo weather fallback."""
    farmer_resp = await client.post("/api/v1/farmers/", json={"name": "Rec Test Farmer"})
    farmer_id = farmer_resp.json()["id"]
    farm_resp = await client.post("/api/v1/farms/", json={
        "farmer_id": farmer_id,
        "name": "Rec Farm",
        "latitude": 13.08,
        "longitude": 77.59,
        "area_hectares": 1.0,
        "soil_type": "loam",
        "irrigation_method": "drip",
        "water_storage_litres": 50000,
    })
    farm_id = farm_resp.json()["id"]
    await client.post("/api/v1/crops/", json={
        "farm_id": farm_id,
        "crop_type": "wheat",
        "growth_stage": "mid",
    })

    response = await client.post("/api/v1/recommendations/", json={"farm_id": farm_id})
    assert response.status_code == 201
    data = response.json()
    assert "recommended_action" in data
    assert "reason" in data
    assert data["farm_id"] == farm_id


@pytest.mark.asyncio
async def test_knowledge_search(client):
    response = await client.post("/api/v1/knowledge/search", json={
        "query": "drip irrigation water efficiency",
        "top_k": 3,
    })
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0


@pytest.mark.asyncio
async def test_scenario_simulation(client):
    farmer_resp = await client.post("/api/v1/farmers/", json={"name": "Scenario Farmer"})
    farmer_id = farmer_resp.json()["id"]
    farm_resp = await client.post("/api/v1/farms/", json={
        "farmer_id": farmer_id,
        "name": "Scenario Farm",
        "latitude": 13.08,
        "longitude": 77.59,
        "area_hectares": 0.5,
        "irrigation_method": "sprinkler",
        "water_storage_litres": 25000,
    })
    farm_id = farm_resp.json()["id"]
    await client.post("/api/v1/crops/", json={
        "farm_id": farm_id,
        "crop_type": "maize",
        "growth_stage": "mid",
    })

    response = await client.post("/api/v1/scenarios/", json={"farm_id": farm_id})
    assert response.status_code == 201
    data = response.json()
    assert "scenarios" in data
    assert len(data["scenarios"]) == 4


@pytest.mark.asyncio
async def test_invalid_farm_coordinates(client):
    """Recommendation with invalid coordinates should fall back gracefully."""
    farmer_resp = await client.post("/api/v1/farmers/", json={"name": "Bad Coord Farmer"})
    farmer_id = farmer_resp.json()["id"]
    farm_resp = await client.post("/api/v1/farms/", json={
        "farmer_id": farmer_id,
        "name": "Bad Coord Farm",
        "latitude": None,
        "longitude": None,
        "area_hectares": 1.0,
        "irrigation_method": "flood",
        "water_storage_litres": 10000,
    })
    farm_id = farm_resp.json()["id"]
    await client.post("/api/v1/crops/", json={
        "farm_id": farm_id,
        "crop_type": "rice",
        "growth_stage": "mid",
    })

    response = await client.post("/api/v1/recommendations/", json={"farm_id": farm_id})
    assert response.status_code == 201  # Should not crash
