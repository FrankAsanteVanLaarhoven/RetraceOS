from __future__ import annotations

import json
from dataclasses import dataclass

import nbformat

from retrace.hashing import snapshot_content_hash


def _notebook(title: str, fault: str, code: str) -> bytes:
    notebook = nbformat.v4.new_notebook()
    markdown = nbformat.v4.new_markdown_cell(
        f"# {title}\n\n"
        "Teaching fixture. The fault below is injected and labelled. "
        "It is not a defect found in anyone's published software.\n\n"
        f"**Injected fault:** {fault}\n"
    )
    markdown["id"] = "fixture-context"
    code_cell = nbformat.v4.new_code_cell(code)
    code_cell["id"] = "fixture-analysis"
    notebook.cells.append(markdown)
    notebook.cells.append(code_cell)
    notebook.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    return nbformat.writes(notebook).encode("utf-8")


ECOLOGY_CODE = """from pathlib import Path
import json
import pandas as pd

source = Path("/Users/former/lab/measurements.csv")  # INJECTED FAULT: absolute path from another computer
df = pd.read_csv(source)
# Intended exclusion: keep rows even when mass_g is missing; drop only if flipper_mm is missing.
clean = df.dropna(subset=["flipper_mm"])
result = {
    "mean_mass_g": float(clean["mass_g"].mean()),
    "n_records": int(len(clean)),
}
Path("outputs").mkdir(exist_ok=True)
Path("outputs/results.json").write_text(json.dumps(result))
result
"""

TRAJECTORY_CODE = """from pathlib import Path
import json
import math
import pandas as pd

df = pd.read_csv(Path("data/trajectory.csv"))  # INJECTED FAULT: packaged file is data/track.csv
total_cm = 0.0
for i in range(1, len(df)):
    dx = float(df.iloc[i].x_cm - df.iloc[i - 1].x_cm)
    dy = float(df.iloc[i].y_cm - df.iloc[i - 1].y_cm)
    total_cm += math.hypot(dx, dy)
metres = total_cm / 100.0
result = {"path_length_m": metres, "n_records": int(len(df))}
Path("outputs").mkdir(exist_ok=True)
Path("outputs/results.json").write_text(json.dumps(result))
result
"""

ASSAY_CODE = """from pathlib import Path
import json
import pandas as pd

df = pd.read_csv(Path("data/assay.csv"))  # INJECTED FAULT: file is semicolon-separated
# Teaching analysis: mean response across every admitted sample. No exclusion threshold.
result = {
    "mean_response": float(df["response"].mean()),
    "n_records": int(len(df)),
}
Path("outputs").mkdir(exist_ok=True)
Path("outputs/results.json").write_text(json.dumps(result))
result
"""


@dataclass(frozen=True)
class Trap:
    slug: str
    title: str
    rationale: str
    find: str
    replace: str


@dataclass(frozen=True)
class DemoCase:
    slug: str
    title: str
    discipline: str
    question: str
    notebook_path: str
    files: dict[str, bytes]
    contract: dict
    missing_contract: dict
    traps: tuple[Trap, ...]
    diagnosis_find: str
    diagnosis_replace: str
    diagnosis_title: str
    diagnosis_rationale: str


def _contract(title: str, population: str, exclusions: str, units: dict[str, str], limitations: str, outputs: list[dict], reference: str) -> dict:
    return {
        "title": title,
        "reference_established": reference,
        "reference_note": (
            "Researcher-authored fixture contract. Expected values were fixed before any repair. "
            "They are not taken from the candidate run."
            if reference == "historical"
            else "No historical reference was supplied. The candidate output must not be promoted into one."
        ),
        "population": population,
        "exclusions": exclusions,
        "units": units,
        "seed": None,
        "limitations": limitations,
        "outputs": outputs,
    }


def _missing_from(contract: dict) -> dict:
    body = json.loads(json.dumps(contract))
    body["reference_established"] = "missing"
    body["reference_note"] = "No historical reference was supplied. The candidate output must not be promoted into one."
    body["title"] = contract["title"] + " — reference withheld"
    for item in body["outputs"]:
        item["expected"] = None
    return body


def cases() -> dict[str, DemoCase]:
    ecology_contract = _contract(
        "Ecology measurement mean",
        "All four admitted rows. A missing mass does not remove the record.",
        "Drop a row only when flipper_mm is missing.",
        {"mean_mass_g": "g", "n_records": "count"},
        "Teaching measurements, not a study of real animals. Agreement is not a biological finding.",
        [
            {
                "name": "mean_mass_g",
                "unit": "g",
                "comparison": "absolute_tolerance",
                "expected": 3716.6666666666665,
                "tolerance": 0.001,
                "required": True,
            },
            {
                "name": "n_records",
                "unit": "count",
                "comparison": "exact_int",
                "expected": 4,
                "tolerance": None,
                "required": True,
            },
        ],
        "historical",
    )
    trajectory_contract = _contract(
        "Trajectory length in metres",
        "Every admitted position sample, in order.",
        "No samples are dropped.",
        {"path_length_m": "m", "n_records": "count"},
        "Synthetic positions. Not a physical robot trial. Source coordinates are centimetres and the contracted length is metres.",
        [
            {
                "name": "path_length_m",
                "unit": "m",
                "comparison": "absolute_tolerance",
                "expected": 2.0,
                "tolerance": 1e-6,
                "required": True,
            },
            {
                "name": "n_records",
                "unit": "count",
                "comparison": "exact_int",
                "expected": 3,
                "tolerance": None,
                "required": True,
            },
        ],
        "historical",
    )
    assay_contract = _contract(
        "Assay mean response",
        "Every sample in the admitted assay table.",
        "No response threshold. Samples are not removed.",
        {"mean_response": "response units", "n_records": "count"},
        "Synthetic assay table, not the UCI Wine Quality dataset and not a laboratory result.",
        [
            {
                "name": "mean_response",
                "unit": "response units",
                "comparison": "absolute_tolerance",
                "expected": 5.5,
                "tolerance": 1e-9,
                "required": True,
            },
            {
                "name": "n_records",
                "unit": "count",
                "comparison": "exact_int",
                "expected": 4,
                "tolerance": None,
                "required": True,
            },
        ],
        "historical",
    )

    ecology = DemoCase(
        slug="ecology",
        title="Ecology measurements",
        discipline="Ecology",
        question="Can a colleague recover the mean mass without dropping records or changing the unit?",
        notebook_path="analysis.ipynb",
        files={
            "analysis.ipynb": _notebook(
                "Ecology measurements",
                "The loader points at an absolute path on another computer.",
                ECOLOGY_CODE,
            ),
            "data/measurements.csv": (
                "id,mass_g,flipper_mm\n1,3750,181\n2,3800,186\n3,,190\n4,3600,180\n"
            ).encode(),
        },
        contract=ecology_contract,
        missing_contract=_missing_from(ecology_contract),
        traps=(
            Trap(
                slug="drop-records",
                title="Drop rows with any missing value",
                rationale="Injected trap. The path is repaired, and dropping every incomplete row removes a record the contract keeps. The mean of the remaining masses can stay the same.",
                find=(
                    'source = Path("/Users/former/lab/measurements.csv")  # INJECTED FAULT: absolute path from another computer\n'
                    "df = pd.read_csv(source)\n"
                    "# Intended exclusion: keep rows even when mass_g is missing; drop only if flipper_mm is missing.\n"
                    'clean = df.dropna(subset=["flipper_mm"])'
                ),
                replace=(
                    'source = Path("data/measurements.csv")\n'
                    "df = pd.read_csv(source)\n"
                    "# INJECTED TRAP: drops records with a missing mass\n"
                    "clean = df.dropna()"
                ),
            ),
            Trap(
                slug="grams-to-kilograms",
                title="Report kilograms in the grams field",
                rationale="Injected trap. The path is repaired, and dividing by 1000 changes the unit while leaving the field name unchanged.",
                find=(
                    'source = Path("/Users/former/lab/measurements.csv")  # INJECTED FAULT: absolute path from another computer\n'
                    "df = pd.read_csv(source)\n"
                    "# Intended exclusion: keep rows even when mass_g is missing; drop only if flipper_mm is missing.\n"
                    'clean = df.dropna(subset=["flipper_mm"])\n'
                    "result = {\n"
                    '    "mean_mass_g": float(clean["mass_g"].mean()),'
                ),
                replace=(
                    'source = Path("data/measurements.csv")\n'
                    "df = pd.read_csv(source)\n"
                    "# Intended exclusion: keep rows even when mass_g is missing; drop only if flipper_mm is missing.\n"
                    'clean = df.dropna(subset=["flipper_mm"])\n'
                    "result = {\n"
                    '    "mean_mass_g": float((clean["mass_g"] / 1000).mean()),  # INJECTED TRAP: kilograms written into a grams field'
                ),
            ),
        ),
        diagnosis_find='Path("/Users/former/lab/measurements.csv")',
        diagnosis_replace='Path("data/measurements.csv")',
        diagnosis_title="Point the loader at the packaged measurements file",
        diagnosis_rationale="The notebook refers to an absolute path on another computer. A file with the expected name is in this package. No original checksum is available to prove it is the same dataset. This fixture declares the packaged file as the admitted input.",
    )
    trajectory = DemoCase(
        slug="trajectory",
        title="Trajectory length",
        discipline="Robotics",
        question="Can a colleague recover the path length in metres, not centimetres?",
        notebook_path="analysis.ipynb",
        files={
            "analysis.ipynb": _notebook(
                "Trajectory length",
                "The loader names a file that is not in the package. The packaged track is data/track.csv.",
                TRAJECTORY_CODE,
            ),
            "data/track.csv": "t,x_cm,y_cm\n0,0,0\n1,100,0\n2,100,100\n".encode(),
        },
        contract=trajectory_contract,
        missing_contract=_missing_from(trajectory_contract),
        traps=(
            Trap(
                slug="centimetres-as-metres",
                title="Leave the length in centimetres",
                rationale="Injected trap. Removing the conversion reports centimetres through a field defined in metres.",
                find=(
                    'df = pd.read_csv(Path("data/trajectory.csv"))  # INJECTED FAULT: packaged file is data/track.csv\n'
                    "total_cm = 0.0\n"
                    "for i in range(1, len(df)):\n"
                    "    dx = float(df.iloc[i].x_cm - df.iloc[i - 1].x_cm)\n"
                    "    dy = float(df.iloc[i].y_cm - df.iloc[i - 1].y_cm)\n"
                    "    total_cm += math.hypot(dx, dy)\n"
                    "metres = total_cm / 100.0"
                ),
                replace=(
                    'df = pd.read_csv(Path("data/track.csv"))\n'
                    "total_cm = 0.0\n"
                    "for i in range(1, len(df)):\n"
                    "    dx = float(df.iloc[i].x_cm - df.iloc[i - 1].x_cm)\n"
                    "    dy = float(df.iloc[i].y_cm - df.iloc[i - 1].y_cm)\n"
                    "    total_cm += math.hypot(dx, dy)\n"
                    "metres = total_cm  # INJECTED TRAP: centimetres left in a metres field"
                ),
            ),
        ),
        diagnosis_find='Path("data/trajectory.csv")',
        diagnosis_replace='Path("data/track.csv")',
        diagnosis_title="Read the packaged track file",
        diagnosis_rationale="The notebook asks for data/trajectory.csv. The admitted file is data/track.csv. The repair changes that path and does not change the conversion from centimetres to metres.",
    )
    assay = DemoCase(
        slug="assay",
        title="Assay table",
        discipline="Analytical chemistry",
        question="Can a colleague recover the mean of every sample, without an unapproved exclusion?",
        notebook_path="analysis.ipynb",
        files={
            "analysis.ipynb": _notebook(
                "Assay table",
                "The table is semicolon-separated and the loader uses the comma default.",
                ASSAY_CODE,
            ),
            "data/assay.csv": "sample_id;response\nA;5.0\nB;6.0\nC;7.0\nD;4.0\n".encode(),
        },
        contract=assay_contract,
        missing_contract=_missing_from(assay_contract),
        traps=(
            Trap(
                slug="exclude-low-response",
                title="Drop samples below 5",
                rationale="Injected trap. The contract admits every sample. A threshold changes the population.",
                find=(
                    'df = pd.read_csv(Path("data/assay.csv"))  # INJECTED FAULT: file is semicolon-separated\n'
                    "# Teaching analysis: mean response across every admitted sample. No exclusion threshold.\n"
                ),
                replace=(
                    'df = pd.read_csv(Path("data/assay.csv"), sep=";")\n'
                    "# INJECTED TRAP: excludes samples below an unapproved threshold.\n"
                    'df = df[df["response"] >= 5]\n'
                ),
            ),
        ),
        diagnosis_find='pd.read_csv(Path("data/assay.csv"))',
        diagnosis_replace='pd.read_csv(Path("data/assay.csv"), sep=";")',
        diagnosis_title="Read the semicolon-separated assay table",
        diagnosis_rationale="The admitted file uses semicolons. The notebook uses the comma default, so the response column is never read. The repair sets the delimiter and does not drop samples.",
    )
    return {"ecology": ecology, "trajectory": trajectory, "assay": assay}


def allowlist() -> set[str]:
    return {snapshot_content_hash(case.files) for case in cases().values()}
