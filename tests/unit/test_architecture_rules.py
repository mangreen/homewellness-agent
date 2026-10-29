"""Import rules for the MVC packages. They replace the layer discipline of the old design."""

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src" / "homewellness"
SDKS = ("boto3", "botocore", "paho")
H = "homewellness."

# package -> modules that it must not import
FORBIDDEN = {
    "models": (H + "controllers", H + "stores", H + "services", H + "views", H + "interfaces",
               H + "bootstrap", "pydantic", *SDKS),
    "views": (H + "controllers", H + "stores", H + "services", H + "bootstrap", *SDKS),
    "controllers": (H + "stores", H + "services", H + "bootstrap", *SDKS),
    "stores": (H + "controllers", H + "views", H + "bootstrap"),
    "services": (H + "controllers", H + "views", H + "stores", H + "bootstrap"),
}


def imported_modules(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


@pytest.mark.parametrize("package", sorted(FORBIDDEN))
def should_follow_the_import_rules_when_a_package_is_scanned(package):
    violations = [
        f"{path.relative_to(SRC)} imports {module}"
        for path in (SRC / package).rglob("*.py")
        for module in imported_modules(path)
        for banned in FORBIDDEN[package]
        if module == banned or module.startswith(banned + ".")
    ]
    assert violations == []


def should_detect_a_violation_when_a_model_imports_a_controller(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text("from homewellness.controllers.chat import ChatController\n")
    assert "homewellness.controllers.chat" in imported_modules(bad)
