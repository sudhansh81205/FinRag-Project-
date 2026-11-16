# FinRAG web workspace

Black/white, self-hosted Geist typography, keyboard navigation, responsive filing library,
evidence/calculation inspector, JSON export, clear failure states and optional private Supabase saved questions.
The DoTA design reference informed hairlines, spacing and restrained motion. No analytics or external asset requests.

## Local
Node22+; no npm dependencies or installation:
```
cd web
npm run dev
npm test
```

## Vercel Hobby
Deploy this `web` directory as the project root. `vercel.json` serves `public` and the standard Node Function API.
Use default Hobby compute, no build-machine overrides, no paid model/Gateway calls.
The Node gateway never bundles local model weights or invents answers.

Configure server-only `FINRAG_BACKEND_URL` (HTTPS) and `FINRAG_BACKEND_TOKEN` to the authenticated prepared Python service.
The token must match that service's `FINRAG_API_TOKEN`. Missing runtime returns `index_not_ready` with empty answer.
Run `python scripts/serve_web_api.py --help` from the repository for the prepared-machine route.
Enable the engine only with current independent acceptance gates, a matching BGE/FAISS store, actual local weights,
the pinned provider and a real local generator tokenizer. No download or silent fallback occurs on startup.

## Supabase
Use the explicitly selected free FinRAG project. Inspect its existing schema first, apply `../supabase/schema.sql`,
then run `../supabase/verify_rls.sql` and advisors. Add `SUPABASE_URL` and a publishable key as
`SUPABASE_PUBLISHABLE_KEY` to Vercel. Legacy `SUPABASE_ANON_KEY` is supported; service-role keys are not used.
Configure the exact production origin as the Auth site URL/allowed redirect. The application requests a magic link
only when the visitor explicitly submits the sign-in form. Auth tokens are session-only; the server verifies `/auth/v1/user`
on every private request. RLS limits select/insert/delete to the owner; updates are not granted. Saved questions
are not accepted source records, benchmark gold or verified outputs.

Database provisioning, auth email delivery and two-real-user isolation require the actual account/runtime.
The committed SQL is not a claim that a database was created or those checks passed.

Provisioned project: `inygweteeaaozryxvmeh` (ap-south-1, free). Migration `20261116194117_finrag_private_saved_queries` is applied; transaction-based owner/cross-owner/anonymous checks passed and both advisors returned no findings.

Email activation is a separate release gate: set the Supabase Auth Site URL and redirect allowlist to the exact Vercel origin, configure permitted test recipients or SMTP and verify a complete sign-in. Then set `SUPABASE_AUTH_READY=true` in Vercel and redeploy. The default UI explicitly disables sign-in until this is verified. Database connection alone does not certify email delivery.
