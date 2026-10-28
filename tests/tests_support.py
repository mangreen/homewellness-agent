"""Shared test doubles."""


class FakeActions:
    """Test double for the AgentActions interface. It records every call."""

    def __init__(self):
        self.calls = []

    def get_latest_vitals(self, elder_id):
        self.calls.append(("get_latest_vitals", elder_id))
        return {"available": True, "blood_pressure": "158/98", "level": "elevated",
                "heart_rate_bpm": 80, "measured_minutes_ago": 1}

    def get_medication_status(self, elder_id):
        self.calls.append(("get_medication_status", elder_id))
        return {"medication": "降血壓藥", "doses": []}

    def log_medication_intake(self, elder_id):
        self.calls.append(("log_medication_intake", elder_id))
        return {"status": "recorded", "dose": "早上"}

    def escalate_emergency(self, elder_id, symptoms):
        self.calls.append(("escalate_emergency", elder_id, list(symptoms)))
        return {"status": "sent", "action": "notify_family", "reason": "symptom_with_abnormal_bp"}
