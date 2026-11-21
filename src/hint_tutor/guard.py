"""Does a tutor reply give the answer away? Two checks to compare: the one most people write first, and a stricter one.

A guard gets the reply, the problem and the student's last message, and returns a reason, or None when the reply
can be shown.
"""

import json
import re
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path


@dataclass(frozen=True)
class Problem:
    id: str
    text: str
    answer: str  # as a fraction, "5/8"

    @property
    def value(self) -> Fraction:
        return Fraction(self.answer)


def load_problems(path: str | Path) -> list[Problem]:
    return [Problem(**p) for p in json.loads(Path(path).read_text(encoding="utf-8"))]


def exact_match(reply: str, problem: Problem, student: str = "") -> str | None:
    """The check most people write first: the answer, exactly as written, appears in the reply."""
    return f"states the answer as {problem.answer}" if problem.answer in reply else None


_COUNT = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen "
                                     "fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}
_COUNT["a"] = 1
_PARTS = {"half": 2, "halves": 2, "third": 3, "thirds": 3, "quarter": 4, "quarters": 4, "fourth": 4, "fourths": 4,
          "fifth": 5, "fifths": 5, "sixth": 6, "sixths": 6, "seventh": 7, "sevenths": 7, "eighth": 8, "eighths": 8,
          "ninth": 9, "ninths": 9, "tenth": 10, "tenths": 10, "twelfth": 12, "twelfths": 12, "sixteenth": 16,
          "sixteenths": 16}
_N = r"(\d+|" + "|".join(sorted(_COUNT, key=len, reverse=True)) + r")"
_P = "(" + "|".join(sorted(_PARTS, key=len, reverse=True)) + ")"
_PATTERNS = [  # (kind, pattern); earlier patterns claim their text first
    ("latex", re.compile(r"\\d?frac\s*\{\s*(\d+)\s*\}\s*\{\s*(\d+)\s*\}")),
    ("mixed", re.compile(r"(?<![\d./])(\d+)\s+(\d+)\s*/\s*(\d+)(?![\d/])")),
    ("mixed words", re.compile(rf"\b{_N}\s+and\s+{_N}[\s-]+{_P}\b")),
    ("fraction", re.compile(r"(?<![\d.])(\d+)\s*/\s*(\d+)(?![\d/])")),
    ("percent", re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)\s*(?:%|percent\b)")),
    ("decimal", re.compile(r"(?<![\d/])(\d*\.\d+)(?![\d/])")),
    ("over", re.compile(rf"\b{_N}\s+(?:over|out of)\s+{_N}\b")),
    ("words", re.compile(rf"\b{_N}[\s-]+{_P}\b")),
]


def _count(word: str) -> int:
    return int(word) if word.isdigit() else _COUNT[word]


def numbers_in(text: str) -> list[tuple[str, str, Fraction]]:
    """Every number the text writes as a fraction or part of one: (kind, written form, value). The written form is
    canonical, so "\\frac{3}{4}", "3 / 4" and "three quarters" all read as "3/4", unreduced."""
    text, found = text.lower(), []
    for kind, pattern in _PATTERNS:
        for m in pattern.finditer(text):
            g = m.groups()
            try:
                if kind in ("latex", "fraction", "over"):
                    top, bottom = _count(g[0]), _count(g[1])
                    value, written = Fraction(top, bottom), f"{top}/{bottom}"
                elif kind == "mixed":
                    value, written = int(g[0]) + Fraction(int(g[1]), int(g[2])), f"{g[0]} {g[1]}/{g[2]}"
                elif kind == "mixed words":
                    whole, top, bottom = _count(g[0]), _count(g[1]), _PARTS[g[2]]
                    value, written = whole + Fraction(top, bottom), f"{whole} {top}/{bottom}"
                elif kind == "words":
                    top, bottom = _count(g[0]), _PARTS[g[1]]
                    value, written = Fraction(top, bottom), f"{top}/{bottom}"
                elif kind == "percent":
                    value, written = Fraction(g[0]) / 100, f"{g[0]}%"
                else:
                    value, written = Fraction(g[0]), g[0]
            except (ZeroDivisionError, ValueError):
                continue
            found.append((kind, written, value))
        text = pattern.sub(lambda m: " " * len(m.group(0)), text)
    return found


def _same(kind: str, value: Fraction, answer: Fraction) -> bool:
    if kind in ("decimal", "percent"):  # "about 0.67" or "67%" for 2/3
        return abs(value - answer) <= Fraction(1, 200)
    return value == answer


CONFIRM = re.compile(r"^\W*(?:yes|yep|yeah|correct|right|exactly|that'?s (?:it|right|correct)|you(?:'ve| have)? got it|"
                     r"well done|great job|nice work|perfect)\b", re.I)
REJECT = re.compile(r"^\W*(?:no\b(?!\s+(?:problem|rush|worries|need))|nope|not quite|incorrect|"
                    r"that'?s (?:not|wrong|incorrect)|close,? but)", re.I)


def value_match(reply: str, problem: Problem, student: str = "") -> str | None:
    """Stricter: any number equal in value to the answer, in any form, unless it's written exactly as in the
    problem; or a reply that opens by confirming or rejecting a number the student offered."""
    given = {written for _, written, _ in numbers_in(problem.text)}
    for kind, written, value in numbers_in(reply):
        if written not in given and _same(kind, value, problem.value):
            return f"states the answer as {written} ({kind})"
    offered = [(k, v) for k, w, v in numbers_in(student) if w not in given]
    if CONFIRM.search(reply) and any(_same(k, v, problem.value) for k, v in offered):
        return "confirms the student's answer"
    if REJECT.search(reply) and offered:
        return "tells the student their answer is wrong"
    return None


_JUDGE = re.compile(r"\b(?:correct(?:ly)?|(?:right|wrong) track|on track|(?:great|good|nice) (?:job|work)|well done|"
                    r"excellent|you did it|you(?:'ve| have) got it|you got it|exactly|perfect|(?:very|so) close|"
                    r"good effort|not quite|almost there|that'?s right|you(?:'re| are) right|successfully)\b", re.I)
_GREAT = re.compile(r"^\W*great\b(?!\s+question)", re.I)
_NEGATED = re.compile(r"\b(?:can'?t|cannot|won'?t|will not|not|never|if|whether)\b", re.I)
ASKS = re.compile(r"\b(?:answer|correct|wrong)\b|\b(?:right|ok|okay)\s*\?|\b(?:is (?:that|it|this)|am i)\b", re.I)


def judgment(reply: str) -> str | None:
    """A sentence that judges the student's work ("You're on the right track!", "That's a good effort!"), unless
    the judging word is negated earlier in its sentence ("I can't tell you if it's correct")."""
    for sentence in re.split(r"(?<=[.!?])\s+", reply):
        m = _JUDGE.search(sentence) or _GREAT.search(sentence)
        if m and not _NEGATED.search(sentence[:m.start()]):
            return m.group(0).strip(" ,")
    return None


def answer_or_judgment(reply: str, problem: Problem, student: str = "") -> str | None:
    """Built from what simulated students found with value_match. Numbers the student wrote don't count as the
    tutor stating them: repeating "5/8" while asking how they got it isn't giving it away. A judgment does count
    when the student offered the right answer, asked or not, or offered any answer and asked whether it's right."""
    given = {written for _, written, _ in numbers_in(problem.text)}
    theirs = numbers_in(student)
    for kind, written, value in numbers_in(reply):
        if written not in given | {w for _, w, _ in theirs} and _same(kind, value, problem.value):
            return f"states the answer as {written} ({kind})"
    offered = [(k, v) for k, w, v in theirs if w not in given]
    right = any(_same(k, v, problem.value) for k, v in offered)
    if offered and (right or ASKS.search(student)) and (j := judgment(reply)):
        return f"judges the student's answer ('{j}')"
    return None


GUARDS = {"exact_match": exact_match, "value_match": value_match, "answer_or_judgment": answer_or_judgment}
