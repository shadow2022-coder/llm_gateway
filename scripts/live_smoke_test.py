from __future__ import annotations

import argparse
import json
import sys

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a live smoke test against the FIR gateway.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Gateway base URL")
    parser.add_argument("--api-key", required=True, help="Raw API key for the protected endpoint")
    parser.add_argument("--model", default="fake-model", help="Model name to request")
    parser.add_argument("--prompt", default="hello from smoke test", help="Prompt to send")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    with httpx.Client(timeout=10.0) as client:
        checks = [
            ("GET /healthz", client.get(f"{base_url}/healthz")),
            ("GET /readyz", client.get(f"{base_url}/readyz")),
            (
                "POST /v1/chat/completions (unauthorized)",
                client.post(
                    f"{base_url}/v1/chat/completions",
                    json={"prompt": args.prompt, "model": args.model},
                ),
            ),
            (
                "POST /v1/chat/completions (authorized)",
                client.post(
                    f"{base_url}/v1/chat/completions",
                    headers={"X-API-Key": args.api_key},
                    json={"prompt": args.prompt, "model": args.model},
                ),
            ),
        ]

    failures = 0
    for label, response in checks:
        try:
            body = response.json()
        except json.JSONDecodeError:
            body = response.text

        print(f"{label}: HTTP {response.status_code}")
        print(json.dumps(body, indent=2) if isinstance(body, dict) else body)
        print()

        if label.endswith("(unauthorized)") and response.status_code != 401:
            failures += 1
        elif label.endswith("(authorized)") and response.status_code != 200:
            failures += 1
        elif label.startswith("GET") and response.status_code != 200:
            failures += 1

    if failures:
        print(f"Smoke test failed with {failures} unexpected result(s).", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
