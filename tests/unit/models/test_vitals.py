from datetime import UTC, date, datetime, timedelta

import pytest

from homewellness.models.errors import InvalidVitalsError
from homewellness.models.vitals import BloodPressure, SleepSummary, VitalsSnapshot

NOW = datetime(2026, 10, 27, 0, 0, tzinfo=UTC)


@pytest.mark.parametrize(("systolic", "diastolic"), [(120, 120), (80, 90), (49, 30), (301, 80),
                                                       (120, 29), (300, 201)])
def should_raise_invalid_vitals_when_bp_is_out_of_range_or_inverted(systolic, diastolic):
    with pytest.raises(InvalidVitalsError):
        BloodPressure(systolic, diastolic)


@pytest.mark.parametrize(("systolic", "diastolic"), [(50, 30), (300, 200), (121, 120)])
def should_accept_blood_pressure_when_values_are_on_the_valid_boundary(systolic, diastolic):
    assert BloodPressure(systolic, diastolic).systolic == systolic


def should_format_blood_pressure_as_slash_text_when_converted_to_string():
    assert str(BloodPressure(158, 98)) == "158/98"


def should_raise_invalid_vitals_when_measured_time_has_no_time_zone():
    with pytest.raises(InvalidVitalsError):
        VitalsSnapshot("e1", datetime(2026, 10, 27, 8, 0), heart_rate_bpm=70)


def should_raise_invalid_vitals_when_snapshot_has_no_measurement():
    with pytest.raises(InvalidVitalsError):
        VitalsSnapshot("e1", NOW)


@pytest.mark.parametrize("heart_rate", [19, 251])
def should_raise_invalid_vitals_when_heart_rate_is_out_of_range(heart_rate):
    with pytest.raises(InvalidVitalsError):
        VitalsSnapshot("e1", NOW, heart_rate_bpm=heart_rate)


@pytest.mark.parametrize("temperature", [-21.0, 61.0])
def should_raise_invalid_vitals_when_room_temperature_is_out_of_range(temperature):
    with pytest.raises(InvalidVitalsError):
        VitalsSnapshot("e1", NOW, room_temperature_c=temperature)


def should_be_fresh_when_age_equals_max_age():
    snapshot = VitalsSnapshot("e1", NOW, heart_rate_bpm=70)
    assert snapshot.is_fresh(NOW + timedelta(minutes=30), timedelta(minutes=30)) is True


def should_not_be_fresh_when_age_is_above_max_age():
    snapshot = VitalsSnapshot("e1", NOW, heart_rate_bpm=70)
    assert snapshot.is_fresh(NOW + timedelta(minutes=30, seconds=1), timedelta(minutes=30)) is False


@pytest.mark.parametrize("hours", [-0.1, 24.1])
def should_raise_invalid_vitals_when_sleep_hours_are_out_of_range(hours):
    with pytest.raises(InvalidVitalsError):
        SleepSummary("e1", date(2026, 10, 27), hours)


def should_accept_sleep_summary_when_hours_are_on_the_boundary():
    assert SleepSummary("e1", date(2026, 10, 27), 0.0).hours_asleep == 0.0
    assert SleepSummary("e1", date(2026, 10, 27), 24.0).hours_asleep == 24.0
