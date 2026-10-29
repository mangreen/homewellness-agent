import json
import logging

from homewellness.observability import JsonFormatter, bind_context, new_trace_id


def format_record(message="hello", **extra):
    record = logging.LogRecord("t", logging.INFO, __file__, 1, message, (), None)
    record.__dict__.update(extra)
    return json.loads(JsonFormatter().format(record))


def should_write_required_fields_when_no_context_is_bound():
    entry = format_record()
    assert {"timestamp", "level", "message", "trace_id", "user_id"} <= entry.keys()
    assert (entry["trace_id"], entry["user_id"]) == ("-", "-")


def should_include_trace_and_user_id_when_context_is_bound():
    with bind_context(trace_id="abc", user_id="elder-1"):
        entry = format_record()
    assert (entry["trace_id"], entry["user_id"]) == ("abc", "elder-1")


def should_restore_the_previous_context_when_the_block_ends():
    with bind_context(trace_id="abc", user_id="elder-1"):
        pass
    assert format_record()["trace_id"] == "-"


def should_include_event_fields_when_extra_values_are_given():
    assert format_record(event="proactive_trigger", kind="poor_sleep")["kind"] == "poor_sleep"


def should_not_leak_a_stack_trace_when_an_error_is_logged():
    try:
        raise ValueError("secret detail")
    except ValueError:
        record = logging.LogRecord("t", logging.ERROR, __file__, 1, "failed", (), None)
        record.exc_info = __import__("sys").exc_info()
    entry = json.loads(JsonFormatter().format(record))
    assert entry["error_type"] == "ValueError" and "secret detail" not in json.dumps(entry)


def should_create_unique_32_character_trace_ids():
    first, second = new_trace_id(), new_trace_id()
    assert first != second and len(first) == 32
