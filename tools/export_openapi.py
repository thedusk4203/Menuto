"""Export or verify the real FastAPI OpenAPI document."""

import argparse
import json
from pathlib import Path

from app.main import create_app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = Path(__file__).resolve().parents[1] / "packages/contracts/openapi.json"
    content = json.dumps(create_app().openapi(), indent=2, sort_keys=True) + "\n"
    if args.check:
        if not target.exists() or target.read_text(encoding="utf-8") != content:
            raise SystemExit("OpenAPI snapshot differs; run tools/export_openapi.py")
        print("OpenAPI snapshot matches.")
    else:
        target.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
