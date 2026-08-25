from rules.audit_trail import AuditTrail


def test_audit_trail_initializes():
    audit = AuditTrail()

    assert audit is not None


def test_record_event():
    audit = AuditTrail()

    audit.record_event(
        "Decision Generated",
        {
            "incident_id": "INC-001",
            "decision": "PB-DB-001",
        },
    )

    events = audit.get_events()

    assert len(events) == 1
    assert events[0]["event_type"] == "Decision Generated"
    assert events[0]["details"]["incident_id"] == "INC-001"
    assert events[0]["details"]["decision"] == "PB-DB-001"


def test_multiple_events_are_recorded():
    audit = AuditTrail()

    audit.record_event(
        "Decision Generated",
        {
            "incident_id": "INC-001",
            "decision": "PB-DB-001",
        },
    )

    audit.record_event(
        "Validation Completed",
        {
            "incident_id": "INC-001",
            "status": "Validation Passed",
        },
    )

    events = audit.get_events()

    assert len(events) == 2
    assert events[0]["event_type"] == "Decision Generated"
    assert events[1]["event_type"] == "Validation Completed"


def test_event_contains_id_and_timestamp():
    audit = AuditTrail()

    audit.record_event(
        "Decision Generated",
        {
            "incident_id": "INC-001",
        },
    )

    event = audit.get_events()[0]

    assert event["event_id"].startswith("EVT-")
    assert "timestamp" in event