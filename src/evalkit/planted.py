"""Planted errors: does a check catch the defects it exists for, and leave clean inputs alone?

Each case is one input with a known answer: a planted defect the check must flag, or a clean control it must pass.
Recall comes from the planted cases; false alarms come from the controls. A suite without controls can be passed
by a check that flags everything.
"""

from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class Case:
    name: str           # what was planted, or what the control is
    group: str          # e.g. the problem or component it belongs to
    should_flag: bool   # True for a planted defect, False for a control
    input: dict = field(default_factory=dict)


def run(cases: list[Case], check: Callable[..., str | None]) -> list[dict]:
    out = []
    for case in cases:
        reason = check(**case.input)
        out.append({"name": case.name, "group": case.group, "should_flag": case.should_flag, "flagged": bool(reason),
                    "reason": reason, "ok": bool(reason) == case.should_flag})
    return out


def summary(results: list[dict]) -> dict:
    planted = [r for r in results if r["should_flag"]]
    controls = [r for r in results if not r["should_flag"]]
    return {"caught": sum(r["flagged"] for r in planted), "planted": len(planted),
            "false_alarms": sum(r["flagged"] for r in controls), "controls": len(controls)}
