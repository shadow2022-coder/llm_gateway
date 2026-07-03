from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.auth import create_api_key_record
from app.db import get_session_factory, init_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a hashed API key and store it in the database.")
    parser.add_argument("--owner", default="local-dev", help="Owner label for the new key")
    args = parser.parse_args()

    init_db()
    session_factory = get_session_factory()
    with session_factory() as session:
        raw_key, api_key = create_api_key_record(session, owner=args.owner)

    print(f"Created API key id={api_key.id} owner={api_key.owner}")
    print(f"Raw API key (shown once): {raw_key}")


if __name__ == "__main__":
    main()
