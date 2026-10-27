"""Fixed demo data: one elder and her medicine schedule."""

from datetime import time

from homewellness.models.elder import ElderProfile
from homewellness.models.medication import Dose, MedicationSchedule

DEMO_ELDER_ID = "demo-elder-001"


def demo_profile() -> ElderProfile:
    return ElderProfile(
        elder_id=DEMO_ELDER_ID,
        display_name="王奶奶",
        family_contact_name="小美",
        timezone="Asia/Taipei",
        medication_schedule=MedicationSchedule(
            medication_name="降血壓藥",
            doses=(Dose("am", "早上", time(8, 0)), Dose("pm", "晚上", time(20, 0))),
        ),
    )
