# Initial results

Comparative study: **NOT_RUN**.

Software fixture result, 2026-10-02, clean install of `retrace-0.1.0`, pytest exit 0, 17 tests:

- For ecology, trajectory, and assay, the diagnosed path repair finished and was `REPRODUCED_WITHIN_CONTRACT`.
- For each family's result-changing trap, verification was `CHANGED_RESULT`. On the ecology trap the mean still matched and the record count did not. The browser run view showed both labels: "Reproduced within contract" and "Changed result".
- A contract without a historical reference stayed `BLOCKED_MISSING_EVIDENCE` even when the candidate contained numbers.
- A notebook that wrote its own verification grade was not trusted.

These are results on authored fixtures with injected faults. They do not estimate performance on published notebooks.
