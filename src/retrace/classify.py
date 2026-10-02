from __future__ import annotations

import re

from retrace.errors import RetraceError

_STRING = re.compile(r"""("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')""")
_FORBIDDEN = (
    "subprocess",
    "socket",
    "pickle",
    "shutil",
    "os.system",
    "Popen",
    "__import__",
    "eval(",
    "exec(",
    "requests",
    "urllib",
    "builtins",
)


def _mask(source: str) -> str:
    return _STRING.sub("STR", source)


def _inner(literal: str) -> str:
    return literal[1:-1]


def _looks_like_path(inner: str) -> bool:
    if any(part == ".." for part in inner.split("/")):
        return False
    if not re.fullmatch(r"[A-Za-z0-9_./ -]+", inner):
        return False
    return "/" in inner or inner.endswith((".csv", ".tsv", ".txt", ".json", ".ipynb"))


def _only_path_literals(before: str, after: str) -> bool:
    if _mask(before) != _mask(after):
        return False
    before_strings = set(_STRING.findall(before))
    after_strings = set(_STRING.findall(after))
    changed = before_strings.symmetric_difference(after_strings)
    if not changed:
        return False
    return all(_looks_like_path(_inner(item)) for item in changed)


def _only_delimiter(before: str, after: str) -> bool:
    def strip_sep(source: str) -> str:
        return source.replace(', sep=";"', "").replace(", sep=';'", "")

    if strip_sep(before) != strip_sep(after):
        return False
    before_count = before.count(', sep=";"') + before.count(", sep=';'")
    after_count = after.count(', sep=";"') + after.count(", sep=';'")
    return after_count == before_count + 1


def classify_edit(before: str, after: str) -> str:
    if before == after:
        raise RetraceError(
            "empty_repair",
            "The proposal does not change the notebook.",
            "Submit a repair that changes the admitted notebook in one place.",
        )
    if _only_path_literals(before, after) or _only_delimiter(before, after):
        return "execution_repair"
    return "methodological_reanalysis"


def assert_label_allowed(before: str, after: str, claimed: str) -> str:
    actual = classify_edit(before, after)
    if claimed not in {"execution_repair", "methodological_reanalysis"}:
        raise RetraceError(
            "bad_classification",
            "A repair is either an execution repair or a methodological reanalysis.",
            "Choose one of those two labels.",
        )
    if claimed == "execution_repair" and actual != "execution_repair":
        raise RetraceError(
            "mislabelled_repair",
            "This change alters the analysis. It cannot be labelled as an execution repair.",
            "Label it as a methodological reanalysis. It will not be accepted as a reproduction.",
            status=422,
        )
    for token in _FORBIDDEN:
        if token in after and token not in before:
            raise RetraceError(
                "refused_repair",
                f"The repair introduces “{token}”, which this workstation profile will not run.",
                "Keep the repair to the analysis notebook. A sandbox for untrusted code is not available.",
                status=422,
            )
    if ".." in after and ".." not in before:
        raise RetraceError(
            "refused_repair",
            "The repair introduces a parent-directory path.",
            "Keep paths inside the admitted package.",
            status=422,
        )
    return actual
