import os
import uuid

import pytest

from homewellness.stores.dynamodb import stores as dynamo
from homewellness.stores.dynamodb.table import DynamoTable

pytestmark = pytest.mark.integration


def should_forget_all_data_and_keep_working_when_the_table_is_reset():
    endpoint = os.environ.get("DYNAMODB_ENDPOINT")
    if not endpoint:
        pytest.skip("DYNAMODB_ENDPOINT is not set")
    table = DynamoTable(f"hw-reset-{uuid.uuid4().hex[:8]}", endpoint_url=endpoint)
    table.ensure_table()
    claims = dynamo.DynamoClaimStore(table)
    assert claims.try_claim("k") is True and claims.try_claim("k") is False
    table.reset()
    assert claims.try_claim("k") is True  # Same handle, empty table.
