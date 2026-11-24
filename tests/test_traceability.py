"""Every requirement in the spec has a test."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_every_requirement_is_referenced_by_a_test():
    spec = (ROOT / "specs/001-seat-change-proration/spec.md").read_text()
    required = set(re.findall(r"REQ-\d{3}", spec))
    tests = " ".join(p.read_text() for p in (ROOT / "tests").glob("test_*.py")
                     if p.name != "test_traceability.py")
    covered = {f"REQ-{n}" for n in re.findall(r"req[_-](\d{3})", tests, flags=re.I)}
    assert required, "no requirements found"
    assert required - covered == set(), f"untested: {sorted(required - covered)}"
