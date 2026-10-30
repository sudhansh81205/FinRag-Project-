# FinRAG nightly review instructions

Run at 23:59 Asia/Kolkata for review dates October 30 through November 17, 2026. Read this file, docs/plan/PRD.md and docs/plan/schedule.json from the repository root, the editable PRD when needed, and previous reports in output/daily_reviews. Resolve all paths from the repository root. Human corrections in the chat override older documents. Seven members only and one scheduled worker per day; the reviewer does not assign additional same-day work to teammates. Do not modify application code, create GitHub issues/comments, commit, merge or push during this review.

## Source and time coverage

Read the current remote `main` versions of `docs/plan/PRD.md`, `schedule.json` and
the latest `docs/handoffs/` entries before using cached local planning copies.
October 30 clarification: November 17 is an internal team completion target.
The first Sudhansh/Shanay tasks were authorized together on October 30; compare
their completion report with code evidence rather than assigning them twice.
Review https://github.com/sudhansh81205/FinRag-Project- using the GitHub connector first; use a non-destructive fetch and git show/diff as fallback. Check default branch, recently active branches, open/merged PRs and available check results. Never check out, reset, stash or overwrite the user's work. Do not silently review only the stale local branch. Identify unpushed local changes separately; they are not GitHub-delivered work.

Record scheduled date, actual run timestamp and cutoff in Asia/Kolkata with UTC equivalents. The snapshot at 23:59 is not the entire remaining minute of that date. For a delayed run reconstruct the scheduled cutoff if evidence permits; otherwise disclose actual coverage. Preserve prior reviewed branch/PR hashes, last successful cutoff and observed commits in output/daily_reviews/review_state.json. Include late-pushed/backdated commits newly visible since the last review, distinguish them from genuinely new same-day work, and do not double-count merged PR commits across branches. On first run, record a local setup baseline and clearly label older changes as backlog. The main revision inspected during planning was b3bb02fb54c68ff7fc3bda9c0959df3d61b0acbf; fetch current remote revisions before drawing conclusions. If history was rewritten, explain instead of assuming a linear diff. If GitHub access fails, produce a coverage-limited report, not a claim that nothing changed.

## Evidence and attribution
For each candidate completion read the actual changes and surrounding code. Record commit SHA/URL, branch or PR, author/coauthors, timestamps, files and checks. Compare the schedule's expected owner with verified GitHub identity; do not guess identity from task ownership or email fragments. Use unknown/unverified attribution until the team confirms a mapping. Commit authorship does not prove sole implementation, hours worked or academic contribution. Distinguish merged, PR-only, branch-only, local-only and no-evidence work. Zero visible GitHub changes means no GitHub-visible evidence, not proof of no work. Assess the actual PRD acceptance check as complete, partial, blocked, not started or unverified.

## Technical review and verification
Prioritize correctness, evidence provenance, ingestion coverage, stable IDs/persistence, table headers/years/units, retrieval filters, context loss, real-provider versus mock behavior, arithmetic, config and executable setup. Check regression impact on existing functionality. Each finding must have severity P0/P1/P2/P3, precise immutable file/line or diff links where verified, observed behavior, consequence, minimal repair, verification check and confidence. Separate verified defects from hypotheses and missing runtime proof. Run only relevant safe checks on the reviewed revision in an isolated disposable review location if necessary, after inspecting what those checks execute; never attribute local-branch test results to another SHA. No paid model calls, downloads, dependency installs or production writes are implied by this recurring review. If a check needs these, mark it not run. Test success does not establish financial answer accuracy or real provider availability.

## Required dated report
Write output/daily_reviews/YYYY-MM-DD_review.md and a matching small JSON record, plus output/daily_reviews/YYYY-MM-DD_whatsapp.txt. Preserve earlier report versions on reruns. Include:
1. Snapshot metadata, evidence coverage and comparison to the previous review.
2. Today's scheduled owner, planned tasks/hours and actual verified contributors with links; note mismatches without blame.
3. Work completed today with code evidence and acceptance-check status; keep unmerged work separate.
4. Current project position: a cumulative PRD requirement table and milestone status. Calculate completion only from explicit acceptance checks and show the denominator, or state that percentage is not defensible.
5. Prioritized review findings and tests actually run/not run, with reviewed revisions.
6. Where the system is lacking and which prior findings are fixed, still open or regressed.
7. Tomorrow's date, sole scheduled owner, time budget, dependencies, ordered steps, acceptance checks and runnable verification commands. Fold essential prior defects into that task. If prerequisite work does not fit, propose a clearly labeled scope reduction or future slot without silently reassigning the schedule. On November 17 give release follow-up only, not a new development day.
8. Tomorrow's tech stack: existing modules/packages/provider/configuration, exact verified versions or unknown, essential proposed additions with reasons and documentation links for version-sensitive advice. Never invent model availability, package versions or credentials.
9. Copy-ready prompts: one implementation prompt and one verification/handoff prompt tailored to tomorrow's actual owner and findings. Do not send unneeded work to other members. Refer to MASTER_PROMPT.md as the reusable base.
10. Improvement bridge: for each priority improvement explain current defect -> tomorrow's planned change -> expected behavior -> acceptance check, and separately list deferred improvements.
11. Blockers, missing evidence, deadline risk and delivery status.

Produce a report every scheduled review day even if no code changed: say that clearly, retain cumulative gaps, and still give tomorrow's concrete plan. A compact WhatsApp summary should contain date, expected owner versus verified contributors, completed work, top gaps, tomorrow owner/task/stack, and the critical tailored prompt or report attachment. A local path is not a downloadable link for a phone; send full report text in numbered messages or attach a verified readable file via a supported UI. Never publish the report publicly merely to create a link.

## Delivery and private configuration
The review produces files and a completion message in the configured chat. Recipient addresses, phone numbers, account/browser profiles, delivery state and credentials belong in private local configuration and must not be committed. External delivery is optional and requires explicit user authorization and a verified sending route. Never claim sent, delivered or read without the corresponding evidence. Save the report even if delivery fails. A local file path is not a phone-accessible download link. Do not publish reports publicly merely to create a link.

The schedule is an instruction for an external scheduler, not an executable GitHub Actions workflow. The local scheduled task was configured separately; cloning this branch does not install or start it. Local execution requires the review machine, desktop app, repository and any authorized delivery session to be available. Stop regular reviews after the November 17 final report and do not produce a daily report outside the declared date range.
