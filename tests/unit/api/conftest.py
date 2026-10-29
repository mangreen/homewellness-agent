import pytest
from fastapi.testclient import TestClient

from builders import taipei
from homewellness.api.app import create_app
from homewellness.bootstrap import build_container
from homewellness.services.clock import FixedClock
from homewellness.settings import Settings
from tests_support import LoopbackPublisher


@pytest.fixture
def container():
    return build_container(
        Settings(store_backend="memory", demo_mode=True), clock=FixedClock(taipei(15, 0))
    )


@pytest.fixture
def publisher(container):
    return LoopbackPublisher(container)


@pytest.fixture
def app(container, publisher):
    return create_app(container, publisher=publisher)


@pytest.fixture
def client(app):
    return TestClient(app, raise_server_exceptions=False)
