# November 17: reviewed repairs and web workspace

Base: main `e69f42883af0217b4c2d00f615993010b08f2f40`. This is an explicitly authorized implementation,
PR and hosting task, separate from the read-only nightly review. No merge or course submission is authorized.
Sudhansh remains the sole scheduled November17 owner; no additional member/day assignment or human effort is inferred.

## Code acceptance and course mapping

| Finding / requirement | Implemented behavior | Success and relevant failure | Concept / viva |
| --- | --- | --- | --- |
| F23, R7/R12/R13, common A-G | Recompute redundant manifest readiness against current controls; validate unique ledger case IDs, run/variant/benchmark/input/control hashes and result digests before skipping or scoring | Unchanged partial resume runs missing cases; readiness edits, foreign/duplicate/corrupt/changed outputs refuse | Reproducible AI controls: why must output identity be checked separately from the manifest? |
| F27, R3/R5/R6/R12 | Match selected comparative period when no supplied plan; revalidate returned calculator programs against actual included facts; web planner derives periods from prepared source records | Matching FY2021 margin succeeds on injected facts; FY2020 request over FY2021 cells refuses, no stale output | KR typed facts/predicates license an inference only for the requested issuer/scope/period |
| F29, R7/R12 | Preserve explicit currency, reject ambiguous/cross-currency and percent/point units; bind explicit labelled periods when gold declares one; preserve 1% scale normalization | 100M USD equals0.1B USD; EUR/JPY/wrong scale, period or percent/point failures | Comparable quantities must match meaning, not only numbers |
| F35, R8/R12/R13 | Replace unsupported signature/submitted/completed states with prepared/partial and null receipt/time; retain genuine historical contributions and closed gates | Preparation files exist; no official upload/receipt is inferred | Ethics/accountability: a field called acknowledgement is not an observed receipt |
| F36, R8/R13 | Require complete independent path inventory/count/schema/digests, root containment and mandatory manifest in verify mode | Complete inventory passes; empty/incomplete/missing/tampered/escaping coverage refuses | Supporting engineering: hashes bind bytes, not correctness or delivery |
| R6/R13 web UI/API | Monochrome Geist workspace, real filing inventory, request controls, source/calculation desk, copy/export, explicit not-ready states; Node gateway validates request/evidence and never invents answers | Node tests exercise matching evidence, wrong source/period/citations, missing provider and missing/expired auth | Explainable interface for typed KR and transformer pipeline; UI status is not experiment acceptance |
| Supabase persistence | Private saved-question schema, owner index, per-operation RLS and no anon/update grants; server uses publishable key plus verified user JWT | Remote migration applied; transactional owner read/write, cross-owner insert/read/delete refusal and anonymous denial all passed; fixtures rolled back | Ownership predicates and privacy; personal notes are separate from accepted facts and benchmark outputs |

## Commands
```
python -m pytest -q tests/test_web_api.py tests/test_nov17_review_repairs.py tests/test_nov16_request_binding.py tests/test_nov16_runner_capacity_gates.py tests/test_nov16_scoring_and_inputs.py tests/test_experiment_scaffold.py tests/test_typed_calculator.py tests/test_benchmark_runner.py tests/test_benchmark_loaders.py
python -m ruff check src tests scripts app.py
cd web
npm run check
```

Use `python scripts/serve_web_api.py --help` from a complete prepared repository for the authenticated
existing-engine service. `web/README.md` documents Vercel Hobby and Supabase settings. No local inference
weights, credentials, runtime data or private addresses are published.

## Scope and unavailable proof
The frontend is deployable on free Vercel without package installation. It does not bundle a local model
or replace exact FAISS with a cloud vector database. Supabase stores user-owned questions only.
The financial API stays not-ready until a prepared authenticated BGE/FAISS/Gemma/tokenizer service and
independent artifact gates exist. No paid model calls or downloads were made.

Current full A-G/benchmark context binding, authentic datasets, actual RAGAS and Llama comparison,
independent chart/caption acceptance and fifty-output faithfulness audit remain mandatory unmet scope.
The runner labels authentic-but-unbound execution blocked instead of final-evaluation eligible.
The50chart questions remain distinct from50generated audited outputs. R9 remains unscheduled Phase2.

The original review environment lacked full dependencies; an isolated checkout now runs the release checks. Current model/provider execution, clean full-data restore, real browser sign-in/email delivery and final course submission still need actual resources.
No generated human signature, approval, official metric or completion percentage is supplied.

The original slide binary is retained as a historical draft; package byte verification does not certify
its visual correctness or make the written demo procedure a recorded end-to-end demonstration.
Read the PR's live checks and deployment result for current evidence after this handoff was written.

## Connected deployment evidence

Vercel Hobby project `finrag-research`, deployment `dpl_F3kKkHS6gcGdgnTPqWBUkCNo9ydJ` reached READY. Stable URL: https://finrag-research.vercel.app (Vercel protection retained). HTTP checks observed HTML200, health200, all18filing inventory200, no-engine answer503, invalid query400 and unauthenticated saved queries401.

Supabase free project `inygweteeaaozryxvmeh` in ap-south-1 is ACTIVE_HEALTHY. Migration `20261116194117_finrag_private_saved_queries` is applied. SQL fixtures rolled back after verifying own read/write, cross-owner insert/read/delete refusal and anonymous denial. Security/performance advisors returned no findings. Only the URL and publishable key are configured in Vercel; no service role key is used.

Email sign-in is explicitly gated off until the exact production Auth redirect allowlist and delivery are verified (`SUPABASE_AUTH_READY=true` only afterward). No email was sent and no fake user sign-in is claimed. The available database connector cannot edit Auth redirect configuration. Browser QA was blocked by a CUA runtime path-initialization error before any deployed-page interaction, so responsive layout, keyboard flows, console and live sign-in remain unverified.

Automatic approval review rejected weakening Vercel SSO protection to make production public. The existing protection remains; a temporary share link can provide review access. Public access needs explicit user approval. No paid tier, custom domain, billable database branch or model call was enabled.

## Check results for PR16

- Node gateway suite:10passed; frontend syntax and full Ruff passed.
- Release manifest:37requiredfiles, canonical LF on Windows/Linux; GitHub web-contracts job passed.
- CI first full run identified two regressions (legacy supplied-plan adapter and an invalid new fixture selector). Both were corrected; the related58tests passed on the corrected version. The full corrected CI run is the authoritative final status.
- Hosted final gateway returned health200 with database configured/auth_setup_required, no-engine answer503, malformed query400, anonymous saved401, expired user401 and unverified email activation503 without sending email. Direct anonymous Supabase REST access returned401/permission denied.
- SQL owner isolation checks passed with rollback; security/performance advisors reported no findings. These are real database checks, separate from browser/email sign-in.
