# Money Tracker

A cloud-first personal finance transaction tracker with a FastAPI backend and a
shared Flutter mobile client for Android and iOS. Development uses mock or
anonymized data only; no financial ingestion is implemented in this repository.

## Mobile application

The Flutter app is in `mobile/`. It is a single shared Dart codebase intended for
Android and iOS, with no Java, Gradle, local database, Docker Desktop, or local AI
model requirement. It currently uses safe mock data while backend authentication is
not available.

The app includes Splash, Login, Dashboard, Transactions, Transaction Details,
Accounts, Categories, and Settings screens. The transaction list and transaction
detail view call the FastAPI backend; the dashboard is calculated from the returned
transaction page. Accounts and Categories remain mock reference data because their
backend endpoints do not exist yet. It deliberately does **not** implement SMS,
Gmail, Account Aggregator, or bank-statement parsing.

The mobile layers are intentionally small:

```text
mobile/lib/core/        configuration and HTTP API-client abstraction
mobile/lib/domain/      typed models and repository contracts
mobile/lib/data/        mock repository implementations
mobile/lib/presentation/ reusable widgets and screens
```

Authentication is isolated behind `AuthRepository`, so a future OAuth/backend
implementation can replace the mock repository without changing screen code. The
`ApiClient` uses `GET /transactions` and `GET /transactions/{id}`, surfaces generic
network/API errors, and sends pagination plus supported query filters. Amounts from
the API are parsed into integer minor units, never Dart `double` values.

Configure the non-secret API URL at build time—there is no hardcoded URL:

```bash
cd mobile
flutter pub get
flutter run --dart-define=API_BASE_URL=https://your-api.example.com \
  --dart-define=API_DEVELOPMENT_USER_ID=your-development-user-uuid
```

`API_DEVELOPMENT_USER_ID` is optional and exists only for the backend's temporary
development-user mechanism. It is not authentication and must be replaced by an
auth token provider in the authentication milestone.

For a new clone, generate the standard native runners with a Flutter SDK in a cloud
development environment, then run the shared app:

```bash
cd mobile
flutter create --platforms=android,ios .
flutter pub get
flutter run
```

The generated `android/` and `ios/` folders are platform runners; all application
logic remains in the shared `lib/` directory. Run mobile checks in Codespaces or an
equivalent cloud environment:

```bash
cd mobile
flutter analyze
flutter test
```

`mobile/.env.example` is documentation only. Build-time configuration should use
`--dart-define`; never place API secrets, Supabase database URLs, bank credentials,
or real transaction data in the mobile application.

### Public browser preview

Every push to `main` deploys a Flutter Web preview to GitHub Pages. It is built
with `USE_MOCK_DATA=true` so it can be viewed safely without exposing a backend or
credentials. It is a UI preview only; Android and iOS production builds continue
to use FastAPI when `API_BASE_URL` is supplied. The deployment URL is available in
the **Actions → Deploy mobile preview** workflow after the first successful run.

## Development model

Use **GitHub Codespaces** for day-to-day backend development. The included devcontainer is a remote Python environment; it does not require Docker Desktop, PostgreSQL, Java, Gradle, local AI models, or any bank-related credentials on the developer's Mac.

1. Create a GitHub repository from this directory and push the code.
2. In GitHub, select **Code → Create codespace on main**.
3. Wait for the `postCreateCommand` to install the small Python toolchain.
4. Optionally copy `.env.example` to `.env` for non-secret local settings. Never add credentials or production data.

## Run the API

From the repository root in Codespaces:

```bash
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```

Codespaces will offer to open the forwarded port. Check the service with:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

Interactive API documentation is available at `/docs` while the server is running.

`GET /health` checks that the API process is running. `GET /health/database` also
opens a PostgreSQL connection and returns `{"status":"ok"}`. It returns HTTP 503
with a generic message when the database is unconfigured or unavailable; connection
details are intentionally not exposed.

## Transaction API (development only)

The initial transaction API is available after the schema migration is applied:

```text
POST   /transactions
GET    /transactions
GET    /transactions/{transaction_id}
PATCH  /transactions/{transaction_id}
DELETE /transactions/{transaction_id}
```

Authentication is intentionally not implemented yet. Every request is isolated to
the fixed development user by default. To test a separate user scope, send an
`X-Development-User-Id` header containing a UUID. This temporary mechanism must
be replaced with real authentication before production use.

`GET /transactions` supports `limit`, `offset`, `start_date`, `end_date`,
`transaction_type`, `payment_mode`, `category_id`, `bank_name`, `account_id`,
`merchant`, and `sort` (`asc` or `desc`). Transaction amounts are validated and
returned as exact decimal values; floating point values are not used for money.

All API errors use this shape:

```json
{"detail":{"code":"VALIDATION_ERROR","message":"Invalid request"}}
```

## Deduplication service

`TransactionDeduplicationService` is a source-independent internal service for
future SMS, Gmail, bank-statement, and Account Aggregator adapters. It does not
perform ingestion itself. It resolves an incoming normalized observation in this
order: an identical source observation, a reliable transaction reference ID, then
a deterministic fingerprint built from account, exact decimal amount, currency,
transaction direction, payment mode, normalized merchant, and UTC transaction
minute.

The `transaction_source_records` table preserves the minimal source provenance
for every matched observation. Re-importing the same source observation is
idempotent, and similar-but-distinct transactions two or more minutes apart do
not merge merely because their amounts match.

## Supabase PostgreSQL

PostgreSQL is hosted by Supabase. Neither local PostgreSQL nor Docker Desktop is
needed. In the Supabase project dashboard, open **Connect** and copy the
**Transaction pooler** connection string. Set it in a local ignored `.env` (or in
Codespaces secrets) after changing the URL scheme to `postgresql+psycopg://`.

Required database environment variable:

| Variable | Required | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | Yes, for database operations | Supabase PostgreSQL URI using the `psycopg` driver. |
| `DATABASE_POOL_SIZE` | No (default `5`) | Persistent application connections. |
| `DATABASE_MAX_OVERFLOW` | No (default `5`) | Short-lived connections permitted above the pool size. |
| `DATABASE_POOL_RECYCLE_SECONDS` | No (default `1800`) | Recycles aging connections. |
| `DATABASE_CONNECT_TIMEOUT_SECONDS` | No (default `10`) | PostgreSQL connection timeout. |

Application environment variables are also documented in `.env.example`:

| Variable | Required | Purpose |
| --- | --- | --- |
| `APP_ENV` | No (default `development`) | Environment label. |
| `APP_HOST` | No (default `0.0.0.0`) | Uvicorn bind host. |
| `APP_PORT` | No (default `8000`) | Uvicorn bind port. |

URL-encode special characters in the Supabase database password before placing it
in `DATABASE_URL`. Store the actual value only in an ignored `.env` file or a
Codespaces secret—never in the repository, CI logs, or issue trackers.

The small, pre-ping-enabled application pool prevents stale connections while
leaving primary pooling to Supabase. Keep pool limits conservative for the
Supabase plan and the expected number of API workers.

Run migrations in Codespaces only after setting `DATABASE_URL`:

```bash
alembic upgrade head
```

The initial schema migration creates `users`, `financial_accounts`, `categories`,
and `transactions`. Financial amounts are PostgreSQL `NUMERIC(18,2)` and are
represented in Python as `Decimal`; floating-point values must not be used for
money. The schema includes per-user fingerprint uniqueness and indexes for common
account, category, merchant, reference, and date-based transaction queries.

## Quality checks

```bash
ruff format backend
ruff check --fix backend
pytest
```

CI runs format verification, linting, and tests for every push and pull request.

## Project layout

```text
.devcontainer/       Codespaces configuration
.github/workflows/   CI checks
backend/app/         FastAPI application code
backend/alembic/     Alembic migration environment
backend/tests/       API tests
alembic.ini          Alembic configuration
pyproject.toml       Python dependencies and tool configuration
```

## Security baseline

Environment files containing values are ignored by Git; only safe templates are committed. Never store or commit passwords, OAuth secrets or tokens, OTPs, UPI PINs, CVVs, banking credentials, or real financial records.

Future milestones will add the normalized financial domain and hosted database integration without requiring a local PostgreSQL server.
