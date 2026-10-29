from builders import ELDER_ID, TODAY, make_sleep, make_vitals, taipei
from homewellness.models.interaction import ConversationTurn, Role
from homewellness.models.medication import MedicationIntake
from homewellness.stores.memory import (
    InMemoryClaimStore,
    InMemoryConversationStore,
    InMemoryIntakeStore,
    InMemoryTelemetryStore,
)


def should_forget_vitals_and_sleep_when_the_telemetry_store_is_cleared():
    store = InMemoryTelemetryStore()
    store.save_vitals(make_vitals(taipei(8, 0)))
    store.save_sleep(make_sleep(5.0))
    store.clear()
    assert (store.latest_vitals(ELDER_ID), store.latest_sleep(ELDER_ID)) == (None, None)


def should_accept_the_same_intake_again_when_the_intake_store_is_cleared():
    store = InMemoryIntakeStore()
    intake = MedicationIntake(ELDER_ID, "am", TODAY, taipei(8, 5))
    store.add(intake)
    store.clear()
    assert store.add(intake) is True


def should_grant_the_same_claim_again_when_the_claim_store_is_cleared():
    store = InMemoryClaimStore()
    store.try_claim("k")
    store.clear()
    assert store.try_claim("k") is True


def should_forget_all_turns_when_the_conversation_store_is_cleared():
    store = InMemoryConversationStore()
    store.append(ELDER_ID, ConversationTurn(Role.ELDER, "hi", taipei(8, 0)))
    store.clear()
    assert store.recent(ELDER_ID, 10) == []
