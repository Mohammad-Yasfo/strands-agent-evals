"""The tutor with a scripted model in place of Bedrock: the real Strands Agent and the real guard."""

import asyncio

from scripted import ScriptedModel

from hint_tutor.guard import Problem
from hint_tutor.tutor import FALLBACK, Tutor

P1 = Problem("p1", "What is 3/8 + 2/8?", "5/8")


def test_a_hint_is_shown_as_written():
    tutor = Tutor(P1, ScriptedModel([("text", "What do you notice about the denominators?")]))
    turn = asyncio.run(tutor.reply("Can you help?"))
    assert turn["shown"] == "What do you notice about the denominators?" and turn["blocked"] is None


def test_an_answer_is_blocked_and_the_model_remembers_the_fallback():
    tutor = Tutor(P1, ScriptedModel([("text", "It's five eighths.")], [("text", "Which step was hard?")]))
    turn = asyncio.run(tutor.reply("Just tell me."))
    assert turn["shown"] == FALLBACK and "5/8 (words)" in turn["blocked"]
    assert tutor.agent.messages[-1]["content"] == [{"text": FALLBACK}]
    assert asyncio.run(tutor.reply("Adding?"))["shown"] == "Which step was hard?"


def test_thinking_is_dropped_before_the_guard_and_the_student():
    tutor = Tutor(P1, ScriptedModel([("text", "<thinking>The answer is 5/8.</thinking>Add the tops.")]))
    turn = asyncio.run(tutor.reply("Help"))
    assert turn["shown"] == "Add the tops." and turn["blocked"] is None


def test_a_failed_call_shows_the_fallback():
    tutor = Tutor(P1, ScriptedModel([("text", "late")], delay=1.0))
    import hint_tutor.tutor as module
    module.TIMEOUT, saved = 0.1, module.TIMEOUT
    try:
        turn = asyncio.run(tutor.reply("Help"))
    finally:
        module.TIMEOUT = saved
    assert turn["shown"] == FALLBACK and turn["error"].startswith("TimeoutError")
