# Refinements

No refinement of a scientific hypothesis has been made, because the comparative study is **NOT_RUN**.

Implementation refinements that happened while making the fixture suite honest:

- Cell ids on the demonstration notebooks are pinned, so the execution allowlist does not change when nbformat would otherwise assign random ids.
- Each result-changing trap also applies the mechanical repair that lets the notebook finish. The verifier can then see a completed run whose method changed, instead of stopping at an exception.
- Naive timestamps are stored as UTC rather than converted through the workstation zone.

These are corrections to the instrument. They are not experimental findings.
