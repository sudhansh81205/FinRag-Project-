# Submit Likhit's November 2 work

The prepared checkout is `C:\Users\likhit\Desktop\Ai\FinRag-Nov02`, branch
`likhit/day-04-filing-parser`, based on team main `6f9f236` as fetched November 3.
The earlier BGE/FAISS draft remains in the separate `FinRag-Project` folder. Do
not submit that draft as part of this reduced-scope assignment.

These commands document the manual submission workflow. After the initial local
handoff, Likhit connected GitHub and authorized branch publication and a PR.
Check the branch and existing pull requests before repeating any
submission steps. A PR asks the team to review and merge your branch; `git pull`
downloads and integrates remote changes into a checkout. Merging requires the
team's review process.

If PowerShell reports that `git` is not recognized, Git is unavailable on that
terminal's PATH. On Likhit's current machine, this session-only helper exposes
the bundled executable without changing Windows settings:

```powershell
function git { & 'C:\Users\likhit\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe' @args }
git --version
```

The GitHub connector can publish without a local Git sign-in. Ordinary CLI
pushes use separate Git authentication and may still request browser sign-in.

## 1 Review and verify locally

Open PowerShell:

```powershell
cd C:\Users\likhit\Desktop\Ai\FinRag-Nov02
git branch --show-current
git status --short
.\.venv\Scripts\python.exe scripts\parse_filing.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pip check
git diff --check
```

The branch command should show `likhit/day-04-filing-parser`. A fresh teammate
checkout needs the environment setup in `docs/PARSING.md` first. On this machine
the isolated environment and parsed data have already been prepared.

## 2 Stage and commit this assignment

Stage the explicit task files, then inspect the staged patch:

```powershell
git add README.md data/filing_manifest.json data/source docs/PARSING.md docs/GITHUB_SUBMISSION.md docs/handoffs/2026-11-03_day-04_likhit.md docs/reports/2026-11-03_day-04_completion.md docs/reports/2026-11-03_day-04_parsing-summary.json docs/reports/2026-11-03_day-04_pr-body.md requirements-parser.txt requirements-dev.txt requirements.txt scripts/parse_filing.py src/ingestion tests/test_filing_parser.py
git diff --cached --stat
git diff --cached
git commit -m "feat: parse the supported Apple 2021 filing with source provenance"
```

Generated `data/raw`, `data/processed`, `.venv` and `.env` must not be staged.
The small compressed public source snapshot under `data/source` is intentional.
If Git needs your identity, configure your own name/email for this repository
and repeat the commit. Use your GitHub-provided noreply address if preferred.

## 3 Bring in any newer team changes

With your work safely committed and `git status` clean:

```powershell
git fetch origin
git merge origin/main
```

If Git reports conflicts, resolve the marked files, review the combined result,
then `git add` the resolved paths and `git commit`. Do not choose one side for
every conflict blindly. Rerun parsing, tests and lint after the merge. If main
has not advanced, Git reports that the branch is already up to date.

## 4 Push using the route you have access to

If you are a collaborator with write access to the team repository:

```powershell
git push -u origin likhit/day-04-filing-parser
```

If you do not have write access, open the team repository on GitHub, choose
**Fork**, and create/use a fork under your account. Copy its HTTPS clone URL.
Replace `YOUR_GITHUB_USERNAME` below with your actual account name:

```powershell
git remote add fork https://github.com/YOUR_GITHUB_USERNAME/FinRag-Project-.git
git push -u fork likhit/day-04-filing-parser
```

If a `fork` remote already exists, inspect `git remote -v` and use it only if it
points to your fork; do not add a duplicate. Keep `origin` pointing to the team
repository so later `git fetch origin` still gets the team's updates. Complete
Git's normal browser sign-in if prompted. Never put an access token in a remote URL.

## 5 Open the pull request

On the [team repository](https://github.com/sudhansh81205/FinRag-Project-), select
**Pull requests > New pull request** (or **Compare & pull request** after pushing).
For a fork, choose **compare across forks**.

- Base repository: `sudhansh81205/FinRag-Project-`.
- Base branch: `main`.
- Head repository: team repository for direct push, or your fork.
- Compare branch: `likhit/day-04-filing-parser`.
- Title: `Complete Likhit Day 4: reproducible Apple 2021 filing parser`.
- Description: copy `docs/reports/2026-11-03_day-04_pr-body.md`.

Review **Files changed** and confirm this is only the parser assignment. Create
the PR, wait for CI and ask the team to review it. Ujjwal's next scheduled work
consumes these parser outputs. A local passing test run is not a claim that the
new PR's GitHub CI has already run. Merge only through the team's normal review
process. Additional commits pushed to the same branch update the same PR.

## 6 Get the team's changes after merge

This task uses a Git worktree: the original folder owns local branch `main` and
still contains the older uncommitted migration experiment. Do not run a blind
`git pull` there or discard that work to make a pull succeed. For the clearest
fresh start after merge, create a new checkout in an unused folder:

```powershell
cd C:\Users\likhit\Desktop\Ai
git clone https://github.com/sudhansh81205/FinRag-Project- FinRag-Team
cd FinRag-Team
git pull --ff-only origin main
```

The clone already contains current main; later `git pull --ff-only origin main`
updates this clean main checkout. Keep experiments on separate feature branches.

Official GitHub instructions:
https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/creating-a-pull-request
