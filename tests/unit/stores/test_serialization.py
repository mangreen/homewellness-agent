from datetime import UTC, date, datetime, timedelta, timezone

from builders import taipei
from homewellness.models.interaction import ConversationTurn, Role
from homewellness.models.medication import MedicationIntake
from homewellness.models.vitals import BloodPressure, SleepSummary, VitalsSnapshot
from homewellness.stores.dynamodb import serialization as ser


def should_round_trip_vitals_when_all_fields_are_set():
    original = VitalsSnapshot("e1", taipei(8, 4), BloodPressure(158, 98), 80, 24.5)
    assert ser.decode_vitals(ser.encode_vitals(original)) == original


def should_round_trip_vitals_when_only_heart_rate_is_set():
    original = VitalsSnapshot("e1", taipei(8, 4), heart_rate_bpm=70)
    assert ser.decode_vitals(ser.encode_vitals(original)) == original


def should_round_trip_sleep_summary():
    original = SleepSummary("e1", date(2026, 10, 27), 4.5)
    assert ser.decode_sleep(ser.encode_sleep(original)) == original


def should_round_trip_medication_intake():
    original = MedicationIntake("e1", "am", date(2026, 10, 27), taipei(8, 5))
    assert ser.decode_intake(ser.encode_intake(original)) == original


def should_round_trip_conversation_turn():
    original = ConversationTurn(Role.ELDER, "我今天頭有點暈", taipei(8, 6))
    assert ser.decode_turn(ser.encode_turn(original)) == original


def should_build_fixed_width_sort_keys_when_times_have_different_precision():
    early = ser.time_key(datetime(2026, 10, 27, 0, 0, 0, tzinfo=UTC))
    later = ser.time_key(datetime(2026, 10, 27, 0, 0, 0, 500, tzinfo=UTC))
    assert len(early) == len(later) and early < later


def should_build_the_same_sort_key_when_the_same_instant_has_another_time_zone():
    utc = datetime(2026, 10, 27, 0, 5, tzinfo=UTC)
    assert ser.time_key(utc) == ser.time_key(utc.astimezone(timezone(timedelta(hours=8))))
