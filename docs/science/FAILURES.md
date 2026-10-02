# Failures

No failed assertion remained in the clean-install pytest run on 2026-10-02 (exit 0).

Recorded limits, which are not hidden failures of that run:

- Notebooks outside the three demonstration hashes do not run. The status is a refusal, not a successful execution.
- `grams-to-kilograms` is present as a proposal and was not the trap executed by `test_demonstration_journey`.
- The human effort hypothesis H4 has no measurement.
- No second-person browser import was clicked in this session. The API test covers export, a tampered bundle rejected on import, and a clean import that does not copy runs.

Warnings that did not fail the run: Starlette deprecates using `httpx` with `starlette.testclient`. nbformat warns that the hand-built untrusted notebook in `test_untrusted_notebook_is_not_executed` has a cell without an id.
