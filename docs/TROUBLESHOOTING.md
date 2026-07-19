# Troubleshooting

## Database connection errors

**Symptom:** `ConnectionRefusedError` / `OSError: Multiple exceptions` when
starting the backend or running `alembic upgrade head`.

- If running manually (not Docker), confirm Postgres is actually running
  and `POSTGRES_HOST`/`POSTGRES_PORT` in `.env` point at it (`localhost`
  for a local install, `postgres` for the Docker Compose service name).
- Confirm `DATABASE_URL` uses the `asyncpg` driver and `DATABASE_URL_SYNC`
  uses `psycopg` — mixing them up causes cryptic driver errors.
- `docker compose ps` — if `postgres` shows `unhealthy`, check
  `docker compose logs postgres`.

## Ollama not running / connection errors from AI endpoints

**Symptom:** `ExternalServiceError: Could not connect to Ollama at
http://localhost:11434. Is \`ollama serve\` running?`

- Install Ollama (https://ollama.com) and run `ollama serve` (or just open
  the desktop app, which runs it in the background).
- Pull the default model: `ollama pull llama3.1` (or whatever
  `OLLAMA_DEFAULT_MODEL` is set to in `.env`).
- If running the backend in Docker but Ollama on the host machine, set
  `OLLAMA_BASE_URL=http://host.docker.internal:11434` (Mac/Windows) rather
  than `http://ollama:11434` (which assumes an `ollama` service in
  docker-compose — not included by default since Ollama models are large;
  add it yourself if you want it containerized too).

## Clerk misconfiguration

**Symptom:** Every API request returns `401 Unauthorized` with "Invalid
authentication token", or the frontend build fails with "Missing
publishableKey".

- Confirm `CLERK_JWKS_URL` / `CLERK_ISSUER` point at YOUR Clerk instance
  (`https://<your-instance>.clerk.accounts.dev/...`), not the placeholder
  values in `.env.example`.
- `CLERK_SECRET_KEY` (backend) and `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
  (frontend) must belong to the SAME Clerk application.
- If `CLERK_AUDIENCE` is set but doesn't match the `aud` claim Clerk
  actually issues, verification fails — leave it blank unless you've
  explicitly configured a custom audience in Clerk's JWT template.
- The frontend's `next build` performs static generation for every page,
  which requires a valid `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` at build
  time (not just runtime) because `<ClerkProvider>` renders during
  prerendering. Missing/placeholder keys cause build failures — this is
  expected and documented, not a bug in the scaffold.

## Port conflicts

**Symptom:** `Error: listen EADDRINUSE: address already in use :::8000`
(or `:::3000`, `:::5432`, `:::6379`, `:::9000`).

- Something else on your machine is already using that port. Either stop
  it, or override the port in `.env` (`APP_PORT`) / docker-compose.yml
  port mappings and restart.
- `lsof -i :8000` (macOS/Linux) to find the offending process.

## Alembic issues

**Symptom:** `alembic upgrade head` fails with a dialect-specific error, or
autogenerate produces an empty migration.

- This scaffold's `alembic/env.py` picks the DB URL from
  `Settings.DATABASE_URL_SYNC` by default (PostgreSQL, `psycopg` driver).
  For a quick SQLite smoke-test of the migration path (no Postgres
  needed), set `ALEMBIC_USE_SQLITE=1` in the environment before running
  Alembic commands.
- If you add a new model but forget to import it in
  `backend/app/models/__init__.py`, it won't be part of `Base.metadata`
  and Alembic's `--autogenerate` won't see it. Always add new model
  modules to that `__init__.py`.
- PostgreSQL-only conveniences (server-side `gen_random_uuid()`, native
  `ARRAY`/`JSONB` operators) are intentionally NOT used directly in
  migrations — the models use cross-dialect `TypeDecorator`s
  (`app/core/db_types.py`) instead, so the same migration works against
  both PostgreSQL and SQLite. If you hand-write a migration that uses a
  Postgres-only type/function directly, it will NOT run against SQLite.

## Backend tests fail with "table already exists" or fixture errors

- The test suite uses a fresh in-memory SQLite database per test function
  (`backend/tests/conftest.py::async_engine` fixture, function-scoped).
  If you see cross-test pollution, check that a new test isn't
  accidentally sharing a module-scoped fixture.

## Frontend: `npm run build` fails only on your machine

- Confirm you're on Node 20+ (`node --version`).
- Delete `node_modules` and `package-lock.json` and reinstall if you
  suspect a corrupted lockfile from an interrupted install.
- On some sandboxed/networked filesystems, `npm install` can fail with
  `ENOTEMPTY`/rename errors due to filesystem restrictions on atomic
  renames — if this happens, install into a plain local directory and
  copy `node_modules` back rather than installing in-place.
