# Domain Model and Layers

Status: Phase 1. Update this file before you change the Domain layer.

## Domain classes

```mermaid
classDiagram
    class ElderProfile {
        elder_id
        display_name
        family_contact_name
        timezone
        local_now(now)
    }
    class MedicationSchedule {
        medication_name
        doses
    }
    class Dose {
        dose_id
        label
        time_of_day
    }
    class MedicationIntake {
        elder_id
        dose_id
        local_date
        taken_at
    }
    class VitalsSnapshot {
        elder_id
        measured_at
        heart_rate_bpm
        room_temperature_c
        is_fresh(now, max_age)
    }
    class BloodPressure {
        systolic
        diastolic
    }
    class SleepSummary {
        elder_id
        woke_on
        hours_asleep
    }
    class ProactiveTrigger {
        kind
        dedup_key
    }
    class EscalationDecision {
        action
        reason
    }
    ElderProfile "1" --> "1" MedicationSchedule
    MedicationSchedule "1" --> "1..*" Dose
    VitalsSnapshot "1" --> "0..1" BloodPressure
    MedicationIntake ..> Dose : refers to
```

## Domain rules (pure functions, no I/O)

| Function | Input | Output |
| --- | --- | --- |
| `assess_blood_pressure` | BloodPressure, thresholds | AlertLevel (LOW, NORMAL, ELEVATED, HIGH, CRITICAL) |
| `decide_escalation` | AlertLevel or None, symptoms | EscalationDecision (NONE, NOTIFY_FAMILY, CALL_EMERGENCY) |
| `dose_states` | schedule, taken dose ids, local time | state per dose (UPCOMING, DUE, TAKEN, MISSED) |
| `resolve_intake` | schedule, taken dose ids, local time | which dose to record, or ALREADY_TAKEN, or NO_DOSE_DUE |
| `evaluate_triggers` | local time, schedule, vitals, sleep | list of ProactiveTrigger |

All thresholds are demo values. A clinician must review them before real use.

## Use cases and ports

```mermaid
flowchart LR
    subgraph Application
        EvaluateTelemetry
        HandleElderMessage
        RecordMedicationIntake
        EscalateEmergency
    end
    subgraph Ports
        ElderRepository
        TelemetryRepository
        IntakeRepository
        ClaimStore
        Notifier
        ConversationRepository
        AgentRunner
        Clock
    end
    EvaluateTelemetry --> ElderRepository & TelemetryRepository & IntakeRepository & ClaimStore & Clock
    RecordMedicationIntake --> ElderRepository & IntakeRepository & Clock
    EscalateEmergency --> ElderRepository & TelemetryRepository & ClaimStore & Notifier & Clock
    HandleElderMessage --> ElderRepository & TelemetryRepository & IntakeRepository & ConversationRepository & AgentRunner & Clock
```

## Impact notes

- Phase 1 is new code. No upstream or downstream code exists yet.
- Phase 2 adds DynamoDB and MQTT adapters. They must pass the same port contracts as the in-memory adapters.
- Phase 3 adds the agent tools. Each tool calls one use case. No tool calls a repository directly.
