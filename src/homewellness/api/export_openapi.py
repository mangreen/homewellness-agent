"""Write the OpenAPI document: `python -m homewellness.api.export_openapi > docs/api/openapi.yaml`.

NOTE: Needs PyYAML (a dev dependency). A test checks that the committed file is up to date.
"""

import sys

import yaml

from homewellness.api.app import create_app


def build_document() -> dict:
    return create_app(container=None).openapi()


def main() -> None:
    yaml.safe_dump(build_document(), sys.stdout, allow_unicode=True, sort_keys=False)


if __name__ == "__main__":
    main()  # pragma: no cover
