# Test report

Date: 2026-10-02.

## Installed package

Command, from `/tmp`, with `PYTHONPATH` unset:

```text
/tmp/retrace-clean/bin/python -m pytest /Users/favl/workspace/retrace/tests --import-mode=importlib -q -ra
```

The interpreter imported `retrace` from `/private/tmp/retrace-clean/lib/python3.11/site-packages/retrace/__init__.py`.

- Collected tests: 17 (`pytest --collect-only -q` reported `tests/test_retrace.py: 17`).
- Run: 17 dots, exit 0. Captured in `docs/quality/pytest-installed.txt`. The quiet mode's final "N passed" sentence was not present in that capture; the dot count, the collect count, and the exit code agree.
- Wheel: `retrace-0.1.0-py3-none-any.whl`, SHA-256 `c1ca1a02346811af15bc81e098bf69d06eb1b4cddea3342c88b85dcf89536ec6`.
- Kernel used by the clean environment: `retrace`, installed with `ipykernel install --sys-prefix --name retrace`.

`test_demonstration_journey` is parametrized over ecology/`drop-records`, trajectory/`centimetres-as-metres`, and assay/`exclude-low-response`. Each case asserts a reproduced path repair, a `CHANGED_RESULT` trap, and a `BLOCKED_MISSING_EVIDENCE` reference.

Also covered by name: hidden contract overrides, mislabelled method changes, notebook-authored grades, cross-account reads, untrusted notebooks, pickle uploads, ambiguous local times, cancel-after-finish, replay, approval invalidation, and UIPlan rejection.

## Browser

Chrome headless via playwright-core, 2026-10-02, against `http://127.0.0.1:3011` and the API on `127.0.0.1:8765`.

- 390×844: document overflow 0. Tabs Snapshot, Contract, Review, Run, Evidence, and Lineage were fully inside the viewport and not text-clipped. Keyboard login reached the display-name field and Continue. ArrowRight moved focus to Contract. End moved focus to Lineage.
- 768×1024: overflow 0, same six tabs inside the viewport.
- 1440×900, left-to-right: the ecology Run tab showed "Reproduced within contract" (mean_mass_g and n_records) and "Changed result".
- Right-to-left Urdu catalogue: `dir=rtl`, rail on the right, English paragraphs computed as `ltr`. Screenshot `docs/quality/desktop-settings-urdu.png` and `docs/quality/desktop-ecology-rtl.png`.
- `/not-a-page` returned HTTP 404 and the heading "That page is not on this desk." The recovery link returned to the desk.
- Connectors rendered `NEEDS_CONFIGURATION`. The page did not claim Connected.
- Sign out returned to "Sign in · RETRACE".

## Not run

PostgreSQL, row-level security, a sandbox escape test, a production load test, a second-person browser import, and the human-participant study.
