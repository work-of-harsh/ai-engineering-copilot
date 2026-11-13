
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.rate_limit import RateLimitMiddleware


def test_rate_limit_blocks_excess_requests():
    test_app = FastAPI()

    test_app.add_middleware(
        RateLimitMiddleware,
        max_requests=2,
        window_seconds=60,
    )

    @test_app.post("/chat")
    def chat():
        return {"answer": "success"}

    client = TestClient(test_app)

    first = client.post("/chat")
    second = client.post("/chat")
    third = client.post("/chat")

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429


def test_health_endpoint_is_not_rate_limited():
    test_app = FastAPI()

    test_app.add_middleware(
        RateLimitMiddleware,
        max_requests=1,
        window_seconds=60,
    )

    @test_app.get("/health")
    def health():
        return {"status": "healthy"}

    client = TestClient(test_app)

    assert client.get("/health").status_code == 200
    assert client.get("/health").status_code == 200
