"""Symptoms that an elder can report."""

from enum import StrEnum


class Symptom(StrEnum):
    DIZZINESS = "dizziness"
    CHEST_PAIN = "chest_pain"
    SHORTNESS_OF_BREATH = "shortness_of_breath"
    FAINTING = "fainting"


# NOTE: Red flags need fast action. A clinician must review this list.
RED_FLAG_SYMPTOMS: frozenset[Symptom] = frozenset(
    {Symptom.CHEST_PAIN, Symptom.SHORTNESS_OF_BREATH, Symptom.FAINTING}
)
