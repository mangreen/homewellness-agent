from pathlib import Path

import yaml

from homewellness.api.export_openapi import build_document

DOC = Path(__file__).resolve().parents[3] / "docs" / "api" / "openapi.yaml"


def should_match_the_committed_openapi_document_when_the_api_changes():
    """Docs follow code. If this fails, run `make openapi` and commit the file."""
    assert yaml.safe_load(DOC.read_text()) == yaml.safe_load(yaml.safe_dump(build_document()))


def should_describe_the_idempotency_header_and_the_error_model():
    document = yaml.safe_load(DOC.read_text())
    post = document["paths"]["/elders/{elder_id}/messages"]["post"]
    assert any(p["name"] == "Idempotency-Key" for p in post["parameters"])
    assert {"400", "404", "409", "422", "503"} <= post["responses"].keys()


def should_print_the_document_when_the_export_command_runs(capsys):
    from homewellness.api.export_openapi import main

    main()
    assert yaml.safe_load(capsys.readouterr().out)["info"]["title"] == "HomeWellness Companion API"
