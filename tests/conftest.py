import os
import subprocess

import pytest
from redis.asyncio import Redis

VECTOR_TYPES = ["vector", "halfvec"]

try:
    from testcontainers.compose import DockerCompose

    TESTCONTAINERS_AVAILABLE = True
except ImportError:
    TESTCONTAINERS_AVAILABLE = False

if TESTCONTAINERS_AVAILABLE:

    @pytest.fixture(scope="session", autouse=True)
    def redis_container() -> DockerCompose:
        # Set the default Redis version if not already set
        os.environ.setdefault("REDIS_VERSION", "edge")

        try:
            compose = DockerCompose(
                "tests", compose_file_name="docker-compose.yml", pull=True
            )
            compose.start()

            redis_host, redis_port = compose.get_service_host_and_port("redis", 6379)
            redis_url = f"redis://{redis_host}:{redis_port}"
            os.environ["DEFAULT_REDIS_URI"] = redis_url

            yield compose

            compose.stop()
        except subprocess.CalledProcessError:
            yield None


@pytest.fixture(scope="session")
def redis_url() -> str:
    return os.getenv("DEFAULT_REDIS_URI", "redis://localhost:6379")


@pytest.fixture(autouse=True)
async def clear_redis(redis_url: str) -> None:
    """Clear Redis before each test."""
    client = Redis.from_url(redis_url)
    await client.flushall()
    await client.aclose()  # type: ignore[attr-defined]
