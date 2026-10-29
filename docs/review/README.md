# Daily implementation and nightly review

The [revised PRD](../plan/PRD.md) and [schedule](../plan/schedule.json) define the seven-member team, one assigned worker per date and November 17, 2026 delivery deadline. All review dates use Asia/Kolkata.

## For the day's owner

1. Read your dated assignment, dependencies and completion check in the schedule.
2. Read the latest available review report. On October 30 there may be no nightly report yet; use the PRD's starting review findings.
3. Copy [MASTER_PROMPT.md](MASTER_PROMPT.md) into your coding assistant. Fill in your name, date, available time and starting branch, and attach the PRD and latest report.
4. Complete a bounded slice, verify it and leave a handoff with changed files, revision, actual time, checks, blockers and restart instructions. Uploading changes remains an explicit action by the member.

## What the reviewer does

[NIGHTLY_REVIEW_INSTRUCTIONS.md](NIGHTLY_REVIEW_INSTRUCTIONS.md) specifies the review: inspect current GitHub code, branches, pull requests and checks; distinguish the planned owner from verified authors; assess the acceptance checks; review defects and remaining gaps; and give the next owner's steps, stack, prompts and verification plan.

The review covers current code as well as the day's changes. Prior findings remain visible until fixed and verified. No-change days still receive a report. Unpushed work is labeled separately from GitHub-visible delivery. Findings do not authorize the reviewer to change code or post to GitHub.

Use [REPORT_TEMPLATE.md](REPORT_TEMPLATE.md) to organize the report. Store generated files under `output/daily_reviews/` on the review machine:

- `YYYY-MM-DD_review.md`: full report.
- `YYYY-MM-DD_review.json`: structured summary and acceptance status.
- `YYYY-MM-DD_whatsapp.txt`: optional message-ready summary.
- `review_state.json`: reviewed revisions, cutoff and retry/delivery state.

Generated output is ignored by Git. Keep reports locally or in the review chat; deliberately publish a sanitized copy only when needed. No report has been fabricated for a future date.

## Scheduler and delivery

The local desktop automation is configured for **11:59 PM each day from October 30 through November 17, 2026**. That is the start time; a report becomes available after the review completes. The review instructions enforce the date range. The last report covers release follow-up and does not assign a new development day after the deadline.

The scheduled task is app configuration, not a GitHub-hosted workflow. Cloning this repository does not create another scheduled task. A team member setting up their own reviewer must configure its scheduler and local paths separately and keep the machine and app available.

Phone numbers, addresses, account profiles, credentials, notification preferences and delivery receipts stay in private local configuration. External delivery must be authorized and verified. An installed messaging app is not proof that delivery works, and a saved local report is not proof that a phone notification was delivered.
