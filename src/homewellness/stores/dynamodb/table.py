"""DynamoDB single-table access.

Table layout (PK, SK):
  ELDER#<id>   VITALS#<utc time>        one reading
  ELDER#<id>   SLEEP#<woke_on date>     last night summary
  ELDER#<id>   INTAKE#<date>#<dose_id>  one dose taken (conditional write = no double record)
  ELDER#<id>   TURN#<utc time>#<rand>   one conversation turn
  CLAIM#<key>  CLAIM                    idempotency and de-duplication key
"""

import threading
import time

import boto3
from botocore.exceptions import BotoCoreError


class DynamoTable:
    def __init__(
        self,
        table_name: str,
        *,
        endpoint_url: str | None = None,
        region_name: str = "ap-northeast-1",
    ) -> None:
        self._table_name = table_name
        self._endpoint_url = endpoint_url  # None means the real AWS endpoint.
        self._region_name = region_name
        self._local = threading.local()

    @property
    def table(self):
        """Return a table handle for the current thread."""
        # NOTE: boto3 sessions and resources are not thread-safe. Use one per thread.
        handle = getattr(self._local, "handle", None)
        if handle is None:
            resource = boto3.session.Session().resource(
                "dynamodb", endpoint_url=self._endpoint_url, region_name=self._region_name
            )
            handle = self._local.handle = resource.Table(self._table_name)
        return handle

    def ensure_table(self, timeout_s: float = 60.0) -> None:
        """Create the table if needed. Retry while the DynamoDB endpoint starts."""
        client = boto3.session.Session().client(
            "dynamodb", endpoint_url=self._endpoint_url, region_name=self._region_name
        )
        deadline = time.monotonic() + timeout_s
        while True:
            try:
                try:
                    client.create_table(
                        TableName=self._table_name,
                        KeySchema=[
                            {"AttributeName": "PK", "KeyType": "HASH"},
                            {"AttributeName": "SK", "KeyType": "RANGE"},
                        ],
                        AttributeDefinitions=[
                            {"AttributeName": "PK", "AttributeType": "S"},
                            {"AttributeName": "SK", "AttributeType": "S"},
                        ],
                        BillingMode="PAY_PER_REQUEST",
                    )
                except client.exceptions.ResourceInUseException:
                    pass
                client.get_waiter("table_exists").wait(TableName=self._table_name)
                return
            except (BotoCoreError, OSError):
                if time.monotonic() >= deadline:
                    raise
                time.sleep(1.0)
