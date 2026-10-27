import os
import uuid

import pytest


@pytest.fixture
def elder_id() -> str:
    """Unique per test. Shared DynamoDB state never leaks between tests."""
    return f"t-{uuid.uuid4().hex[:10]}"


@pytest.fixture(scope="session")
def dynamo_table():
    endpoint = os.environ.get("DYNAMODB_ENDPOINT")
    if not endpoint:
        pytest.skip("DYNAMODB_ENDPOINT is not set")
    from homewellness.stores.dynamodb.table import DynamoTable

    table = DynamoTable("homewellness-test", endpoint_url=endpoint, region_name="ap-northeast-1")
    table.ensure_table()
    return table
