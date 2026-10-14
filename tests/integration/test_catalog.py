import pytest

pytestmark = pytest.mark.integration


def test_search_combines_filters_and_paginates(client, job_data, prefix):
    for suffix, mode in [("b", "remote"), ("a", "remote"), ("c", "onsite")]:
        response = client.post("/api/v1/jobs", json=job_data | {"id": prefix + suffix, "workMode": mode})
        assert response.status_code == 201, response.text
    params = {"q": "  " + job_data["company"].upper() + "  ",
              "location": job_data["location"].upper(), "workMode": "remote", "limit": 1}
    first = client.get("/api/v1/jobs", params=params)
    assert first.status_code == 200, first.text
    assert first.json()["total"] == 2
    assert first.json()["items"][0]["id"] == prefix + "a"
    second = client.get("/api/v1/jobs", params=params | {"offset": 1}).json()
    assert second["total"] == 2
    assert second["items"][0]["id"] == prefix + "b"
    assert client.get("/api/v1/jobs", params=params | {"offset": 20}).json()["items"] == []
    assert client.get("/api/v1/jobs", params=params | {"location": prefix + "other"}).json()["total"] == 0


@pytest.mark.parametrize("field", ["title", "description"])
def test_search_title_or_description(client, job_data, prefix, field):
    assert client.post("/api/v1/jobs", json=job_data | {field: prefix + "Needle"}).status_code == 201
    results = client.get("/api/v1/jobs", params={"q": prefix + "needle"}).json()
    assert results["total"] == 1
    assert results["items"][0]["id"] == job_data["id"]


def test_search_treats_query_as_data(client, prefix):
    response = client.get("/api/v1/jobs", params={"q": prefix + "' MATCH (n) DETACH DELETE n //"})
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 51}, {"offset": -1},
                                   {"workMode": "any"}, {"q": "a" * 201}])
def test_catalog_validates_filters(client, params):
    response = client.get("/api/v1/jobs", params=params)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
