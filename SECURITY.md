# Security

## Security model

FastAPI requires a verified Supabase Bearer token for user data routes. The JWT
subject is the sole user scope; client-supplied user identifiers are never trusted.
Every transaction lookup, list, update, delete, account validation, category
validation, and deduplication source lookup is scoped to that authenticated user.

Financial amounts use PostgreSQL `NUMERIC` and Python `Decimal`. SQLAlchemy
parameterizes user input; no user-provided SQL, file path, or shell command is used.

## Sensitive-data rules

Never store or log passwords, UPI PINs, OTPs, CVVs, bank login credentials, OAuth
client secrets, access/refresh tokens, raw unrelated SMS, raw Gmail messages, or
raw bank statements. Current statement parsing is in memory only. Environment
files with real values are ignored; only examples are committed.

## Audit status (2026-09-28)

Fixed high-severity issue: deduplication source-fingerprint lookups are now scoped
to the authenticated user, preventing cross-user record association.

Residual deployment controls required before production:

- Configure HTTPS, a reverse-proxy request-body limit, and distributed rate limiting.
- Use Supabase asymmetric JWT signing/JWKS where possible; legacy JWT secrets stay
  server-only and must be at least 32 characters.
- Configure Supabase RLS policies before exposing database APIs directly.
- Do not enable Android SMS permissions until Play policy eligibility and the
  Permissions Declaration are approved.
- Gmail `gmail.readonly` is a restricted scope and requires Google verification
  and applicable assessment before public production use.
- Statement upload APIs are not implemented; when added they must enforce MIME
  sniffing, size/page limits, timeouts, authentication, and memory limits.

## Reporting

Do not file secrets or personal financial data in issues. Report vulnerabilities
privately to the repository owner with a minimal reproduction and redact all data.
