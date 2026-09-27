# Production deployment

The backend is prepared for a small Render web service. Codespaces is development
only. Render terminates HTTPS for its `https://` service URL; configure a custom
domain and enforce HTTPS before a public mobile release.

## Deploy

1. Create a Render account and choose **New → Blueprint** for this repository.
   The Blueprint explicitly uses Render's `free` web-service plan and does not
   require a payment method. Free services can sleep and are for staging/testing,
   not a public financial-data production launch.
2. Review `render.yaml`; do not place values in it.
3. In Render, set the required secret environment variables below.
4. Set `CORS_ALLOWED_ORIGINS` to exact trusted origins, comma separated. Never use
   `*` in production. Native Android/iOS clients do not require browser CORS.
5. Deploy and verify `GET /health` and authenticated `GET /health/database` from
   the provider dashboard or a trusted monitoring system.
6. Add the resulting HTTPS URL as Flutter `API_BASE_URL` through build config.

## Required environment variables

| Variable | Notes |
| --- | --- |
| `APP_ENV` | `production` |
| `DATABASE_URL` | Supabase transaction-pooler URL with `postgresql+psycopg://` |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_JWT_SECRET` | Server-only legacy HS256 secret; omit when using asymmetric JWKS |
| `GMAIL_CLIENT_ID` | Backend-only Google OAuth web client ID |
| `GMAIL_CLIENT_SECRET` | Backend-only Google OAuth client secret |
| `GMAIL_REDIRECT_URI` | Exact Render HTTPS callback ending in `/auth/gmail/callback` |
| `GMAIL_OAUTH_STATE_SECRET` | Random 32-byte-or-longer state-signing secret |
| `CORS_ALLOWED_ORIGINS` | Exact browser origins only, for example `https://app.example.com` |

Optional: `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW`,
`RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW_SECONDS`, and `API_DOCS_ENABLED=false`.

## Rollback

1. In Render, open the service’s **Events** or deployment history.
2. Select the last known-good deploy and choose rollback/redeploy.
3. Verify `/health`; then verify `/health/database` using authenticated internal
   monitoring.
4. If a migration caused the incident, stop traffic first and run only the reviewed
   Alembic downgrade in a controlled maintenance window. Never rollback blindly.
5. Rotate credentials if logs, an environment variable, or a database URL may have
   been exposed.

## Limits and logging

The application has a basic per-instance request limiter. Configure provider/WAF
rate limits as the authoritative distributed limit. Application logs must contain
only request method/path/status/timing; never log request bodies, authorization
headers, statements, SMS, emails, or financial transaction values.
