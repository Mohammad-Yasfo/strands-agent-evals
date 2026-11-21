from fractions import Fraction

import pytest

from hint_tutor.guard import Problem, answer_or_judgment, exact_match, numbers_in, value_match

P1 = Problem("p1", "What is 3/8 + 2/8?", "5/8")
P2 = Problem("p2", "Simplify 6/9.", "2/3")
P5 = Problem("p5", "Solve for x: x + 3/4 = 2", "5/4")


@pytest.mark.parametrize("text,value", [
    ("5/8", Fraction(5, 8)), ("5 / 8", Fraction(5, 8)), (r"\frac{5}{8}", Fraction(5, 8)), ("0.625", Fraction(5, 8)),
    ("62.5%", Fraction(5, 8)), ("five eighths", Fraction(5, 8)), ("five-eighths", Fraction(5, 8)),
    ("five over eight", Fraction(5, 8)), ("1 1/4", Fraction(5, 4)), ("one and a quarter", Fraction(5, 4)),
    ("a half", Fraction(1, 2)),
])
def test_numbers_are_read_in_every_form(text, value):
    assert [v for _, _, v in numbers_in(f"It is {text}.")] == [value]


def test_the_first_check_only_sees_the_answer_as_written():
    assert exact_match("The answer is 5/8.", P1)
    assert not exact_match("It comes to 10/16.", P1)


@pytest.mark.parametrize("reply,student", [
    ("It comes to 10/16.", ""), ("That's about 67%.", ""), ("It's two thirds.", ""), ("That's 1 1/4.", ""),
    ("Yes, that's right!", "Is it 5/8?"), ("Not quite. Try again.", "Is it 5/16?"),
])
def test_the_stricter_check_sees_other_forms_and_judgments(reply, student):
    problem = P5 if "1 1/4" in reply else P2 if "third" in reply or "67" in reply else P1
    assert value_match(reply, problem, student)


@pytest.mark.parametrize("reply,student", [
    ("What do you notice about the denominators?", ""),
    ("Let's start with 6/9. What would you do first?", ""),       # the problem's own number, as written
    ("No rush. How did you get that?", "Is it 5/16?"),
    ("How did you get that? Walk me through your steps.", "Is it 5/8?"),
])
def test_the_stricter_check_leaves_hints_alone(reply, student):
    assert value_match(reply, P2 if "6/9" in reply else P1, student) is None


def test_a_leak_split_across_a_sentence_gets_past_every_guard():
    # the known limit of a per-reply check, kept here so it stays visible
    reply = "The top number is 5 and the bottom number is 8."
    assert exact_match(reply, P1) is None and value_match(reply, P1) is None and answer_or_judgment(reply, P1) is None


def test_written_forms_are_canonical():
    assert [w for _, w, _ in numbers_in(r"I get \frac{5}{8}, 5 / 8 or five eighths.")] == ["5/8", "5/8", "5/8"]


@pytest.mark.parametrize("reply,student", [
    ("How did you get 5/8? Walk me through it.", "I got 5/8. Is that right?"),           # repeats their number
    ("I can't tell you if your answer is correct. How did you get it?", "Is 5/8 correct?"),
    ("Excellent! So now you have 5/6 and 2/6. What next?", "I would change 1/3 to 2/6."),  # a step, not an answer
    ("You've got it! Now subtract.", r"On the right side, I subtract \frac{3}{4} from 2."),
])
def test_the_judgment_guard_lets_these_through(reply, student):
    problem = Problem("p4", "What is 5/6 - 1/3?", "1/2") if "5/6" in reply else (
        P5 if "frac" in student else P1)
    assert answer_or_judgment(reply, problem, student) is None


@pytest.mark.parametrize("reply,student", [
    ("You're on the right track!", "So the fraction is 5/8. Is that the final answer?"),
    ("That's a good effort! Let's walk through it again.", "I got 5/16. Is that right?"),
    ("You're very close! What happens when you simplify it?", "5/6 - 2/6 is 3/6. Can you simplify that?"),
    ("It comes to 10/16.", ""),
])
def test_the_judgment_guard_catches_these(reply, student):
    problem = Problem("p4", "What is 5/6 - 1/3?", "1/2") if "3/6" in student else P1
    assert answer_or_judgment(reply, problem, student)
