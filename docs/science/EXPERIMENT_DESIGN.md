# Experiment design

Status: **NOT_RUN** as a study. The fixture harness below is what the software tests actually do.

## Fixtures

Three authored teaching notebooks. Faults are injected and labelled in the source. They are not presented as defects found in someone else's software.

| Family | Mechanical repair the suite accepts | Result-changing trap the suite rejects | Missing-evidence case |
|---|---|---|---|
| Ecology measurements | Point the loader at the packaged file | Drop rows with any missing value | A contract with no historical reference |
| Trajectory distance | Point the loader at the packaged file | Treat centimetres as metres | A contract with no historical reference |
| Assay table | Read the packaged semicolon-separated file | Exclude low-response rows | A contract with no historical reference |

An additional ecology proposal, `grams-to-kilograms`, is shipped on the fixture and classified as a methodological reanalysis. The automated journey executes `drop-records` for that family. `grams-to-kilograms` was not the case the suite ran.

## What the software test holds constant

Each journey approves the historical contract, approves one exact proposal, and runs it. The verifier reads `outputs/results.json` from the runner. It does not read a verification field written by the notebook. The comparison, the tolerance, and the expected values come from the approved contract.

## What a later study would add

A manual recovery arm, an execution-only coding agent, and an existing notebook-testing tool, with the same notebooks, the same contract, and a frozen check the repair system cannot edit. Development notebooks and evaluation notebooks would be split by repository. That study has not been run.
