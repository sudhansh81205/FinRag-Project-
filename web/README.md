# FinRAG web workspace

The current startup and demonstration instructions are in [START_HERE.txt](../START_HERE.txt). The source-checked registry contains18filings/10companies; the financial backend reports which are connected now. Processing, live connectivity and independent acceptance have separate labels.

Node22 is required. There are no npm dependencies. From this directory, `npm run dev` opens http://127.0.0.1:4173/; the full prepared-laptop launcher opens http://127.0.0.1:4180/. Frontend-only startup cannot answer without the authenticated Python backend.

Set private `web/.env` from `.env.example`; do not overwrite existing credentials. Server configuration: FINRAG_BACKEND_URL, FINRAG_BACKEND_TOKEN, SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY and SUPABASE_PASSWORD_AUTH_READY=true. HTTP loopback is development-only. Production requires HTTPS; FINRAG_BACKEND_TOKEN must equal the backend FINRAG_API_TOKEN. Keep legacy SUPABASE_AUTH_READY off unless magic-link delivery/redirects have separately passed.

The existing Supabase schema is already applied. On a new authorized project only, inspect its tables first, then apply ../supabase/schema.sql once, ../supabase/verify_rls.sql and advisors. RLS uses actual auth.uid() ownership for select/insert/delete. No updates or anonymous access are granted. No service-role key belongs in the website.

Use email/password sign-in. New accounts require actual confirmation email; the optional original confirmation-link field verifies only this Supabase project's allowlisted link. The browser keeps only the access token in sessionStorage, so refresh in the same tab preserves sign-in until token expiry. The server verifies the user on every private operation; records are stored in Supabase, not browser storage. On expiry, sign in again to retrieve existing rows. Saved Questions paginates instead of hiding all rows beyond the newest30. Signing out clears the browser token.

The approved protected Vercel project is finrag-workspace in Rushil's existing team. Deploy only this reviewed directory with its existing project link and server settings; no new project/billing is needed. Never upload .env, model files or local auth/session state. The temporary authenticated API tunnel requires the laptop awake. A Git push alone does not publish a file-based deployment.

`npm test` verifies API contracts, persisted server-row reload/delete, pagination, expiry and selection identity using fixtures. Prior actual two-account local/production isolation and fixture cleanup receipts remain in docs/reports/2026-11-18-functional-checks/. These do not establish new-user email delivery. Current verification is in the final completion report.

The browser submits queued requests and polls short-lived random job capabilities. Backend SQLite stores job status, not user accounts. Run one Python service per job store. Results must match the exact question/filing/period and included citations. No sample financial answers or fallback provider is returned as a live result.
