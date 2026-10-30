# Historical prototypes

Use the repository-root `app.py` for team work. These files preserve earlier work;
they are not supported launch commands or evidence of a finished system.

- `gradio_original.py`: original main-branch UI at `b3bb02f`. Its retrieval and
  evidence-panel design informed the integrated UI. It downloads models at import,
  changes a process-wide credential and assumes an index exists. Do not run it for
  the final demo; port required behavior through the shared application boundary.
- `Dockerfile.experimental`: original backend container file. It claims to launch
  an app but actually runs pytest without copying tests. Container delivery is
  deferred in the PRD; the verified route is native Python.
- The root `Untitled.ipynb` remains the original ingestion reference. Its saved
  outputs and evaluation examples are historical, not new measured results.
- `scripts/run_eval.py` is the legacy three-question experiment, not the planned
  14-question scored evaluation. Its default automatic provider can return mocks.

Both original revisions remain in Git history. No source work was discarded.
