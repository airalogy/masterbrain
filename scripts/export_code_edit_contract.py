"""Export the public code-edit JSON Schema from the Python source models."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SOURCE = REPO_ROOT / "packages" / "masterbrain" / "src"
TARGET = REPO_ROOT / "packages" / "client" / "schema" / "code-edit.v1.schema.json"

sys.path.insert(0, str(PYTHON_SOURCE))

from masterbrain.endpoints.code_edit.types import (  # noqa: E402
    CodeEditInput,
    CodeEditOutput,
)


def render_contract() -> str:
    payload = {
        "contract_version": "1",
        "request": CodeEditInput.model_json_schema(),
        "response": CodeEditOutput.model_json_schema(),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when the committed schema differs from the Python models.",
    )
    args = parser.parse_args()
    rendered = render_contract()

    if args.check:
        if not TARGET.exists() or TARGET.read_text(encoding="utf-8") != rendered:
            print(
                "Code-edit contract is stale. Run `npm run contract:generate`.",
                file=sys.stderr,
            )
            return 1
        print(f"Code-edit contract is current: {TARGET.relative_to(REPO_ROOT)}")
        return 0

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(rendered, encoding="utf-8")
    print(f"Wrote {TARGET.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
