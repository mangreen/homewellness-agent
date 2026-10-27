import urllib.error
import urllib.request

import pytest

from homewellness.health import start_health_server


def get(server, path="/healthz"):
    url = f"http://127.0.0.1:{server.server_address[1]}{path}"
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code


@pytest.fixture
def make_server():
    servers = []

    def build(is_ready=lambda: True):
        server = start_health_server(0, is_ready)
        servers.append(server)
        return server

    yield build
    for server in servers:
        server.shutdown()


def should_answer_200_when_the_worker_is_ready(make_server):
    assert get(make_server()) == 200


def should_answer_503_when_the_worker_is_not_ready(make_server):
    assert get(make_server(lambda: False)) == 503


def should_answer_404_when_the_path_is_unknown(make_server):
    assert get(make_server(), "/other") == 404
