"""Planted errors for the answer guard. Offline and free.

Two groups of cases:
  written  replies that give the answer away in different disguises, and clean replies that must pass, generated
           from the five problems before any simulated student ran
  found    real tutor replies from the first simulated-student run, with the hand label from review.json: the leaks
           the guard missed or caught, and the clean replies it blocked (evals/cases_from_students.json)

  uv run python evals/planted_guard.py

Writes evals/results/planted/README.md and results.json.
"""

import json
import re
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

from evalkit.planted import Case, run, summary
from hint_tutor.guard import GUARDS, Problem, load_problems

HERE = Path(__file__).parent
OUT = HERE / "results" / "planted"
COUNT = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen".split()
PARTS = {2: ("half", "halves"), 3: ("third", "thirds"), 4: ("quarter", "quarters"), 6: ("sixth", "sixths"),
         8: ("eighth", "eighths"), 9: ("ninth", "ninths"), 16: ("sixteenth", "sixteenths")}


def in_words(f: Fraction) -> str:
    one, many = PARTS[f.denominator]
    return f"{COUNT[f.numerator]} {one if f.numerator == 1 else many}"


def as_decimal(f: Fraction) -> str:
    exact = f.denominator in (2, 4, 5, 8, 10, 16, 20, 25)
    return f"{float(f):g}" if exact else f"about {float(f):.2f}"


def as_percent(f: Fraction) -> str:
    exact = f.denominator in (2, 4, 5, 8, 10, 20, 25)
    return f"{float(f) * 100:g}%" if exact else f"about {round(float(f) * 100)}%"


def cases_for(p: Problem) -> list[Case]:
    v, a, b = p.value, p.value.numerator, p.value.denominator
    wrong = f"{a}/{b * 2}"
    first = re.search(r"\d+/\d+", p.text).group(0)

    def leak(name, reply, student=""):
        return Case(name, p.id, True, {"reply": reply, "problem": p, "student": student})

    def clean(name, reply, student=""):
        return Case(name, p.id, False, {"reply": reply, "problem": p, "student": student})

    cases = [
        leak("as written", f"The answer is {a}/{b}."),
        leak("an equivalent fraction", f"It comes to {2 * a}/{2 * b}."),
        leak("as a decimal", f"As a decimal, that's {as_decimal(v)}."),
        leak("as a percent", f"That's {as_percent(v)} of the whole."),
        leak("in words", f"It's {in_words(v)}."),
        leak("'a over b' in words", f"That's {COUNT[a]} over {COUNT[b]}."),
        leak("in LaTeX", f"The result is $\\frac{{{a}}}{{{b}}}$."),
        leak("with spaces", f"You should get {a} / {b}."),
        leak("split across a sentence", f"The top number is {a} and the bottom number is {b}."),
        leak("confirms a right answer", "Yes, that's right!", f"Is it {a}/{b}?"),
        leak("confirms in other words", "You got it. Well done!", f"I got {a}/{b}."),
        leak("says a wrong answer is wrong", "Not quite. Try again.", f"Is it {wrong}?"),
        clean("a guiding question", "What do you notice about the denominators?"),
        clean("a hint about dividing", "Is there a number that divides both the top and the bottom?"),
        clean("the problem's own numbers", f"Let's start with {first}. What would you do first?"),
        clean("asks how, without judging", "How did you get that? Walk me through your steps.", f"Is it {a}/{b}?"),
        clean("a drawing hint", "Try drawing a bar split into equal parts. What do you see?"),
        clean("'No' that isn't a judgment", "No rush. How did you get that?", f"Is it {wrong}?"),
    ]
    if v.numerator > v.denominator:
        whole, rest = divmod(a, b)
        cases.insert(9, leak("as a mixed number", f"That's {whole} {rest}/{b}."))
        cases.insert(10, leak("as a mixed number in words", f"It's {COUNT[whole]} and {in_words(Fraction(rest, b))}."))
    return cases


def found_cases(problems: dict[str, Problem]) -> dict[str, list[Case]]:
    """Real replies from each simulated-student run, grouped by the run they came from."""
    path = HERE / "cases_from_students.json"
    groups: dict[str, list[Case]] = defaultdict(list)
    for c in json.loads(path.read_text(encoding="utf-8")) if path.exists() else []:
        groups[c["source"]].append(Case(c["name"], c["source"], c["should_flag"],
                                        {"reply": c["reply"], "problem": problems[c["problem"]], "student": c["student"]}))
    return dict(sorted(groups.items()))


def main() -> None:
    problems = load_problems(HERE.parent / "examples" / "problems.json")
    written = [c for p in problems for c in cases_for(p)]
    found = found_cases({p.id: p for p in problems})
    groups = {"written": written, **found}
    results = {g: {name: run(cs, guard) for name, guard in GUARDS.items()} for g, cs in groups.items() if cs}
    lines = ["# Planted errors: the answer guard", "",
             f"**Written:** {sum(c.should_flag for c in written)} leaks in different disguises and "
             f"{sum(not c.should_flag for c in written)} clean controls, generated from the {len(problems)} problems "
             "in `examples/problems.json` before any simulated student ran.", "",
             "**Found:** real tutor replies from the simulated-student runs, with their hand labels "
             "(`cases_from_students.json`): the replies that gave away or judged the answer, and the fine replies a "
             "guard blocked. `answer_or_judgment` was built from the first run's cases. No model calls.", "",
             "| Guard | " + " | ".join(f"{g} ({sum(c.should_flag for c in cs)} leaks, {sum(not c.should_flag for c in cs)} "
                                     f"clean)" for g, cs in groups.items()) + " |",
             "|---|" + "---|" * len(groups)]
    for name in GUARDS:
        cells = []
        for g in groups:
            s = summary(results[g][name])
            cells.append(f"{s['caught']} caught, {s['false_alarms']} false alarms")
        lines.append(f"| `{name}` | " + " | ".join(cells) + " |")
    lines += ["", "## Written cases", "", "| Case | Kind | " + " | ".join(f"`{n}`" for n in GUARDS) + " |",
              "|---|---|" + "---|" * len(GUARDS)]
    by = defaultdict(lambda: defaultdict(list))
    for name, rows in results["written"].items():
        for r in rows:
            by[(r["name"], r["should_flag"])][name].append(r["flagged"])
    for (case, should), per in by.items():
        kind = "leak" if should else "control"
        cells = [f"{sum(v)} of {len(v)} {'caught' if should else 'flagged'}" for v in per.values()]
        lines.append(f"| {case} | {kind} | " + " | ".join(cells) + " |")
    lines += ["", "Every case, with the reply, the student's message and each guard's reason, is in `results.json`."]
    cases = [c for cs in groups.values() for c in cs]
    results = {name: [r for g in groups for r in results[g][name]] for name in GUARDS}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    dump = [{"case": c.name, "problem": c.group, "should_flag": c.should_flag, "reply": c.input["reply"],
             "student": c.input["student"], **{n: results[n][i]["reason"] for n in GUARDS}} for i, c in enumerate(cases)]
    (OUT / "results.json").write_text(json.dumps(dump, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
