# FIR FastAPI Gateway

Minimal chat gateway with hashed API keys, request logging, provider fallback, cache, rate limiting, and a browser UI. It defaults to fake-provider mode so any reviewer can boot and test it locally without external API keys, but it can also call OpenAI or Anthropic if those keys are configured.

## Architecture

- FastAPI app exposes `GET /healthz`, `GET /readyz`, and `POST /v1/chat/completions`
- SQLAlchemy stores `api_keys` and `request_logs` in SQLite or PostgreSQL
- Provider routing tries the primary provider first and falls back to the secondary provider on handled failures
- Cache and rate limiting use Redis when available, otherwise in-memory fallbacks

```text
Client
  |
  v
FastAPI /v1/chat/completions
  |
  +--> API key validation --> api_keys table
  |
  +--> rate limiter -------> Redis or in-memory
  |
  +--> cache --------------> Redis or in-memory
  |
  +--> provider router ----> primary provider -> fallback provider
  |
  +--> request_logs table
```

## Setup

Fastest local setup:

```bash
./scripts/bootstrap.sh
```

Or manually:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
make run
```

Local app command:

```bash
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Browser UI:

```text
http://127.0.0.1:8000/
```

## Environment Variables

| Name | Purpose | Default |
| --- | --- | --- |
| `APP_ENV` | App environment label | `development` |
| `HOST` | Uvicorn bind host | `0.0.0.0` |
| `PORT` | Uvicorn bind port | `8000` |
| `DATABASE_URL` | SQLAlchemy database URL | `sqlite:///./local.db` |
| `REDIS_URL` | Optional Redis URL | empty for local fallback |
| `COMPOSE_DATABASE_URL` | Optional compose-only DB override | PostgreSQL service default |
| `COMPOSE_REDIS_URL` | Optional compose-only Redis override | Redis service default |
| `PRIMARY_PROVIDER` | Primary provider name | `fake` |
| `SECONDARY_PROVIDER` | Secondary provider name | `fake` |
| `PROVIDER_TIMEOUT_SECONDS` | Provider timeout budget | `5` |
| `FAKE_RESPONSE_PREFIX` | Fake provider response prefix | `Fake response` |
| `FAKE_PRIMARY_FORCE_FAILURE` | Force primary fake failure | `false` |
| `FAKE_SECONDARY_FORCE_FAILURE` | Force secondary fake failure | `false` |
| `OPENAI_API_KEY` | Reserved for future real OpenAI integration | empty |
| `OPENAI_BASE_URL` | OpenAI API base URL | `https://api.openai.com/v1` |
| `ANTHROPIC_API_KEY` | Reserved for future real Anthropic integration | empty |
| `ANTHROPIC_BASE_URL` | Anthropic API base URL | `https://api.anthropic.com/v1` |
| `ANTHROPIC_MAX_TOKENS` | Anthropic max output tokens | `256` |
| `CACHE_TTL_SECONDS` | Cache TTL | `60` |
| `RATE_LIMIT_PER_MINUTE` | Requests per API key per minute | `10` |

## Create an API Key

```bash
.venv/bin/python scripts/create_api_key.py --owner local-dev
```

## Tests

```bash
make test
```

Direct pytest command:

```bash
.venv/bin/python -m pytest -q
```

Live smoke test against a running server:

```bash
.venv/bin/python scripts/live_smoke_test.py --base-url http://127.0.0.1:8000 --api-key YOUR_RAW_KEY
```

## Example Requests

```bash
curl http://127.0.0.1:8000/healthz
```

```bash
curl http://127.0.0.1:8000/readyz
```

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: REPLACE_WITH_RAW_KEY' \
  -d '{"prompt":"hello","model":"fake-model"}'
```

## Fake Provider Mode

- The default fake provider mode is deterministic and safe for tests
- Set `FAKE_PRIMARY_FORCE_FAILURE=true` to verify fallback behavior
- Keep `PRIMARY_PROVIDER=fake` and `SECONDARY_PROVIDER=fake` for fully local runs

## Real Provider Mode

OpenAI example:

```bash
export PRIMARY_PROVIDER=openai
export SECONDARY_PROVIDER=fake
export OPENAI_API_KEY=your_key_here
make run
```

Anthropic example:

```bash
export PRIMARY_PROVIDER=anthropic
export SECONDARY_PROVIDER=fake
export ANTHROPIC_API_KEY=your_key_here
make run
```

## Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

After startup:

```bash
curl http://127.0.0.1:8000/healthz
docker compose exec app python scripts/create_api_key.py --owner docker-smoke
```

Suggested reviewer flow:

```bash
make setup
make test
.venv/bin/python scripts/create_api_key.py --owner reviewer
make run
```
