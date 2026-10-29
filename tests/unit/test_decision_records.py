"""The decision records are part of the product. These tests keep them complete and linked."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ADRS = sorted((ROOT / "docs" / "adr").glob("ADR-*.md"))
MEMS = sorted((ROOT / ".agents" / "memories").glob("MEM-*.md"))
ERRS = sorted((ROOT / ".agents" / "errors").glob("ERR-*.md"))
INDEX = ROOT / "docs" / "adr" / "README.md"
RECORDS = ADRS + MEMS
BY_NAME = {p.name: p for p in RECORDS}
NAME = re.compile(r"\b((?:ADR|MEM)-\d{4}-[a-z0-9-]+\.md)")
HEADINGS = {
    "ADR": ["## Context", "## Decision", "## Alternatives Considered", "## [Trade-off Analysis]",
            "## Consequences", "## Verification"],
    "MEM": ["## Summary", "### Context & Evolution", "### Specification", "## When to Use"],
    "ERR": ["## Description", "## Root Cause", "## Solution", "## Prevention"],
}


def references(path: Path) -> set[str]:
    return set(NAME.findall(path.read_text())) - {path.name}


def should_find_records_of_every_kind():
    assert ADRS and MEMS and ERRS and INDEX.exists()


@pytest.mark.parametrize("record", RECORDS, ids=lambda p: p.name)
def should_point_only_to_records_that_exist(record):
    assert references(record) <= BY_NAME.keys()


@pytest.mark.parametrize("record", RECORDS, ids=lambda p: p.name)
def should_link_back_when_a_record_points_to_another_record(record):
    """Two-way links: if A names B, then B names A."""
    missing = [
        other for other in references(record)
        if record.name not in references(BY_NAME[other])
    ]
    assert missing == []


@pytest.mark.parametrize("record", [*RECORDS, *ERRS], ids=lambda p: p.name)
def should_have_a_date_and_the_template_headings(record):
    text = record.read_text()
    assert re.search(r"^Date: \d{4}-\d{2}-\d{2}$", text, re.M)
    assert re.search(r"^(Status|Severity): \S", text, re.M)
    assert [h for h in HEADINGS[record.name[:3]] if h not in text] == []


@pytest.mark.parametrize("record", RECORDS, ids=lambda p: p.name)
def should_name_an_existing_record_when_the_status_says_superseded(record):
    status = re.search(r"^Status: (.*)$", record.read_text(), re.M).group(1)
    for target in re.findall(r"[Ss]uperseded by (\S+\.md)", status):
        assert target in BY_NAME


@pytest.mark.parametrize("record", [*RECORDS, *ERRS], ids=lambda p: p.name)
def should_be_listed_in_the_index(record):
    assert record.name in INDEX.read_text()


@pytest.mark.parametrize("record", [*RECORDS, *ERRS], ids=lambda p: p.name)
def should_have_no_unfinished_marker(record):
    text = record.read_text().lower()
    markers = ("short form", "expand after the demo", "short memo")
    assert not any(marker in text for marker in markers)
