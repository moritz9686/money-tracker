# India Account Aggregator feasibility and architecture

**Status:** research and design only. No AA integration, credentials, or production claim is introduced. **Reviewed:** 28 September 2026.

## Executive conclusion

India's Account Aggregator (AA) ecosystem can become a future data source, but this app must not connect directly to banks or treat an AA gateway as a regular bank-data API.

An AA is an RBI-regulated NBFC-AA that mediates consent-based data exchange between Financial Information Providers (FIPs) and Financial Information Users (FIUs). Sahamati currently says only entities registered and regulated by RBI, SEBI, IRDAI, or PFRDA may be FIPs or FIUs. Therefore an unregulated personal-finance startup should assume it is not eligible to be an FIU until counsel and the AA/provider confirm it in writing.

The viable routes are: (1) operate within an appropriately regulated FIU entity, or (2) contract with an eligible regulated FIU that is the AA-network data user while this app acts as its authorised technology/data processor. A gateway can reduce technical effort but does not eliminate eligibility, certification, consent-purpose, or data-protection duties.

## Confirmed facts

| Topic | Finding |
| --- | --- |
| Regulation | The [RBI NBFC-AA master directions](https://systemhealth.rbi.org.in/Scripts/BS_ViewMasterDirections.aspx.html) are the controlling AA regulatory source. |
| FIU eligibility | Sahamati currently says FIPs/FIUs must be registered and regulated by RBI, SEBI, IRDAI, or PFRDA. [Source](https://sahamati.org.in/how-to-join-the-account-aggregator-network-to-share-and-access-financial-data/) |
| Consent | Customers approve or decline requests showing information, purpose, frequency, and duration, and may revoke active consent. [Source](https://sahamati.org.in/account-aggregator-apps/) |
| FIU requirements | Sahamati describes consent creation, consent/data-ready notification handling, fetching, decryption, and processing by an FIU. [Source](https://sahamati.org.in/how-to-join-the-account-aggregator-network-to-share-and-access-financial-data/) |
| Standards | ReBIT specifications/schemas apply; Sahamati identifies Central Registry/Token Server services and recommends certification before go-live. [Source](https://sahamati.org.in/how-to-join-the-account-aggregator-network-to-share-and-access-financial-data/) |
| Data types | Coverage is not a guaranteed uniform transaction feed. A current Sahamati template includes deposits, investments, insurance, NPS, and GST-related types; actual availability depends on each FIP and consented type. [CT019](https://sahamati.org.in/aa-fair-use-template-library/ct019-self-use-consent-on-aa-apps/) |
| Sandbox | UAT must use dummy data/accounts; real accounts and production replicas must not be discoverable or linkable. [Source](https://sahamati.org.in/how-to-join-the-account-aggregator-network-to-share-and-access-financial-data/) |

## Provider-specific findings

| Route | Public indication | Confirm before choosing |
| --- | --- | --- |
| Setu AA Gateway | Documents sandbox/production consent, status, data-session, certification, and revocation flows. [Docs](https://docs.setu.co/data/account-aggregator/v1/get-started) | FIU/sponsorship model, FIP/FI-type coverage, key model, SLA, pricing, and processing terms. |
| Finvu, OneMoney, others | Sahamati lists Finvu, OneMoney, Anumati, INK-AA, Protean SurakshAA, Saafe, NADL and others with sandboxes. [Directory](https://sahamati.org.in/how-to-join-the-account-aggregator-network-to-share-and-access-financial-data/) | Production onboarding, coverage, signing/webhook scheme, contract, certification, and price. |

There is no reliable public universal production price card. Obtain written proposals separating onboarding, certification/audit, fixed/minimum fees, consent/fetch/session usage, support, exit, deletion/export, and taxes. Setu notes certification is billed by the provider but publishes no universal amount. [Source](https://docs.setu.co/data/account-aggregator/v1/get-started)

## Assumptions and legal confirmation needed

Assumptions: this product is personal financial visibility/analytics/categorisation/import, not lending, underwriting, distribution, or payment initiation; FastAPI is the server boundary and Flutter gets no AA secret/private key; the current normalized Transaction model and deduplication service remain canonical.

Written legal/compliance confirmation is needed for exact FIU eligibility; regulated-FIU partner/controller-processor and liability terms; applicable regulator and DPDP obligations; approved purpose/template, FI types, date range, frequency, data life and consent expiry; data residency; retention/deletion; audit/breach/grievance rules; and whether AI, exports, joint accounts, minors, or cross-border support change the permitted use.

## Consent and data flow

1. An authenticated user selects **Connect through Account Aggregator**.
2. Flutter asks FastAPI to create a draft connection. FastAPI validates approved purpose, FI types, range, frequency, expiry, and data life.
3. A provider/FIU adapter creates consent and returns a short-lived AA redirect/deep link.
4. The user completes AA-controlled discovery/linking and approval. This app never handles bank passwords, bank OTPs, UPI PINs, or CVVs.
5. AA/provider sends consent-status and data-ready callbacks. FastAPI verifies signature, timestamp, nonce, event ID, and local correlation before changing state.
6. While active consent permits it, a protected worker creates/fetches a data session. Results may be partial or empty for some FIPs.
7. The worker decrypts and validates only the consented payload, normalizes it, and shows safe aggregate preview/import results.
8. Valid observations go through the existing Transaction Engine's deduplication service before storage.

The app needs **Disconnect AA**, expiry/state display, immediate stopping of future fetches, remote revocation where supported, and reconciliation of remote revocation. Setu's [revocation API](https://docs.setu.co/data/account-aggregator/api-integration/consent-flow) is an example, not a universal endpoint. Revocation blocks future sharing; handling of already received data follows the approved retention policy and law.

## Proposed architecture into the Transaction Engine

```text
Flutter AA connection UI (no AA secrets)
               │ authenticated HTTPS
FastAPI: AAConnectionService → ConsentPolicy → AAProviderAdapter
               │                              │
               └→ webhook/fetch worker ← AA gateway / eligible FIU ← AA ← FIPs
                           │
              AAFinancialInformationNormalizer
                           │
FinancialAccountResolver → existing TransactionDeduplicationService → Supabase
```

`AAProviderAdapter` owns provider auth, signing, consent, data sessions, callback verification, and revocation. `ConsentPolicy` owns approved request limits. The normalizer validates decrypted ReBIT/provider records and creates the existing `DeduplicationCandidate`. The resolver maps a protected opaque external account reference only to an account owned by the local authenticated user. API routes and Flutter must not contain provider protocol or transaction business logic.

| Existing field | Mapping rule |
| --- | --- |
| `source` | Always `ACCOUNT_AGGREGATOR`. |
| `user_id` | From validated local connection, never unchecked callback/client input. |
| `account_id` | Existing owned account resolved from protected opaque external mapping. |
| `transaction_date` | Preserve timezone; reject ambiguous values. |
| `amount` | Parse as `Decimal`, never float. |
| debit/credit/mode | Deterministic schema mapping; quarantine unknown debit/credit. |
| merchant/description/reference | Minimal normalization; reliable reference IDs are preferred for deduplication. |
| `confidence` | Parser completeness only, not a consent-validity assertion. |

The existing reference-ID/fingerprint strategy can merge AA, statement, Gmail, SMS, and manual observations into one logical transaction while retaining minimal source provenance.

## Future persistence only — not implemented now

| Record | Keep | Never keep |
| --- | --- | --- |
| `aa_connections` | user, provider, opaque consent ID, approved purpose/version, FI types, state, expiry/revocation timestamps | secrets, bank credentials, unnecessary full account data |
| `aa_import_runs` | opaque session ID, timing, aggregate imported/duplicate/rejected counts, safe error code | raw payload or raw provider error body |
| `aa_external_accounts` | local account, provider/FIP, protected opaque reference, last four only if approved | plaintext full account number |
| audit events | actor, action, correlation ID, time, outcome | payload, headers, access tokens, keys |

Raw AA payloads must be transient in protected server memory and excluded from PostgreSQL, object storage, queues, exception trackers, and logs. Use opaque references and envelope encryption when sensitive correlation data cannot be avoided.

## Security, retention, sandbox, and production gate

- Use TLS, signed callbacks, replay prevention, and provider-required mTLS/IP controls; an IP allow-list alone is insufficient.
- Store client secrets, webhook secrets, signing/private keys, and decryption keys only in cloud secret management. Separate sandbox and production projects/keys.
- Keep existing Supabase-authenticated user scoping for every connection/account/import/transaction. Never trust client or callback user IDs.
- Decrypt only server-side, promptly remove temporary buffers/files, redact logs, apply least privilege, encryption at rest, access review, rate limits, incident response, and a tested provider-disable switch.
- Never send raw AA data to AI. Any later categorisation uses only an approved minimum merchant descriptor.

Illustrative production secret names only: `AA_PROVIDER`, `AA_ENVIRONMENT`, `AA_BASE_URL`, `AA_CLIENT_ID`, `AA_CLIENT_SECRET`, `AA_PRODUCT_INSTANCE_ID`, `AA_WEBHOOK_SECRET`, `AA_SIGNING_KEY_ID`, `AA_PRIVATE_KEY_REFERENCE`, and `AA_PAYLOAD_DECRYPTION_KEY_REFERENCE`. None belongs in Flutter or source control.

Default retention proposal: retain normalized transactions and minimum consent/import audit state; process raw data transiently; purge after success/failure/cancellation/expiry; make deletion configurable, tested, and auditable. CT019's seven-day data-life upper bound is a self-use template, not universal permission to retain data for seven days. [Caveat](https://sahamati.org.in/aa-fair-use-template-library/ct019-self-use-consent-on-aa-apps/)

Sandbox work must use only synthetic users/accounts/fixtures. Test approved, declined, expired, revoked, duplicate-callback, retry, malformed, zero-result, and partial-FIP paths, plus normalization/deduplication without raw payload retention.

Do not implement AA until: (1) counsel approves FIU eligibility or a regulated-FIU partnership; (2) a provider confirms onboarding, coverage, costs, contracts, certification, and production requirements; (3) consent and retention/deletion policy are approved; (4) security/threat/privacy/incident ownership are approved; and (5) synthetic-data sandbox proves the isolated adapter-to-Transaction-Engine path. AA remains optional; Gmail, statement, manual, and Android-only SMS sources must remain independently usable.
