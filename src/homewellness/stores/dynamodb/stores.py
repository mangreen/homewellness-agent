"""DynamoDB stores. They keep the same contracts as the in-memory stores."""

import uuid
from datetime import UTC, date, datetime

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from homewellness.models.interaction import ConversationTurn
from homewellness.models.medication import MedicationIntake
from homewellness.models.vitals import SleepSummary, VitalsSnapshot
from homewellness.stores.dynamodb import serialization as ser
from homewellness.stores.dynamodb.table import DynamoTable


def _put_if_absent(table: DynamoTable, item: dict) -> bool:
    """Atomic write. Return False if the key already exists."""
    try:
        table.table.put_item(Item=item, ConditionExpression="attribute_not_exists(PK)")
    except ClientError as error:
        if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise
    return True


def _query(table: DynamoTable, pk: str, prefix: str, *, newest_first: bool = False,
           limit: int | None = None) -> list[dict]:
    args: dict = {
        "KeyConditionExpression": Key("PK").eq(pk) & Key("SK").begins_with(prefix),
        "ScanIndexForward": not newest_first,
        "ConsistentRead": True,  # Read-after-write is needed for safety decisions.
    }
    if limit is not None:
        args["Limit"] = limit
    return table.table.query(**args)["Items"]


def _elder(elder_id: str) -> str:
    return f"ELDER#{elder_id}"


class DynamoTelemetryStore:
    def __init__(self, table: DynamoTable) -> None:
        self._table = table

    def save_vitals(self, snapshot: VitalsSnapshot) -> None:
        self._table.table.put_item(Item={
            "PK": _elder(snapshot.elder_id), "SK": f"VITALS#{ser.time_key(snapshot.measured_at)}",
            "data": ser.encode_vitals(snapshot),
        })

    def latest_vitals(self, elder_id: str) -> VitalsSnapshot | None:
        items = _query(self._table, _elder(elder_id), "VITALS#", newest_first=True, limit=1)
        return ser.decode_vitals(items[0]["data"]) if items else None

    def save_sleep(self, summary: SleepSummary) -> None:
        self._table.table.put_item(Item={
            "PK": _elder(summary.elder_id), "SK": f"SLEEP#{summary.woke_on.isoformat()}",
            "data": ser.encode_sleep(summary),
        })

    def latest_sleep(self, elder_id: str) -> SleepSummary | None:
        items = _query(self._table, _elder(elder_id), "SLEEP#", newest_first=True, limit=1)
        return ser.decode_sleep(items[0]["data"]) if items else None


class DynamoIntakeStore:
    def __init__(self, table: DynamoTable) -> None:
        self._table = table

    def add(self, intake: MedicationIntake) -> bool:
        return _put_if_absent(self._table, {
            "PK": _elder(intake.elder_id),
            "SK": f"INTAKE#{intake.local_date.isoformat()}#{intake.dose_id}",
            "data": ser.encode_intake(intake),
        })

    def list_for_date(self, elder_id: str, local_date: date) -> list[MedicationIntake]:
        items = _query(self._table, _elder(elder_id), f"INTAKE#{local_date.isoformat()}#")
        return [ser.decode_intake(item["data"]) for item in items]


class DynamoClaimStore:
    def __init__(self, table: DynamoTable) -> None:
        self._table = table

    def try_claim(self, key: str) -> bool:
        return _put_if_absent(self._table, {
            "PK": f"CLAIM#{key}", "SK": "CLAIM", "claimed_at": datetime.now(UTC).isoformat(),
        })

    def release(self, key: str) -> None:
        self._table.table.delete_item(Key={"PK": f"CLAIM#{key}", "SK": "CLAIM"})


class DynamoConversationStore:
    def __init__(self, table: DynamoTable) -> None:
        self._table = table

    def append(self, elder_id: str, turn: ConversationTurn) -> None:
        self._table.table.put_item(Item={
            "PK": _elder(elder_id), "SK": f"TURN#{ser.time_key(turn.at)}#{uuid.uuid4().hex[:8]}",
            "data": ser.encode_turn(turn),
        })

    def recent(self, elder_id: str, limit: int) -> list[ConversationTurn]:
        items = _query(self._table, _elder(elder_id), "TURN#", newest_first=True, limit=limit)
        return [ser.decode_turn(item["data"]) for item in reversed(items)]
