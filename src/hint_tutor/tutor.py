"""A practice tutor that gives hints and never the answer, with a guard on every reply."""

import asyncio
import re

from strands import Agent
from strands.models import Model

from hint_tutor.guard import Problem, value_match

TUTOR_PROMPT = """You're a patient math tutor. A grade 6 student is practicing this problem:
{problem}
Help them work it out themselves. Ask one guiding question or give one small hint at a time.
Never state the final answer in any form: not as a fraction, a decimal, a percent or in words.
Never tell the student whether their answer is right or wrong. If they give an answer, ask how they got it."""

FALLBACK = "I can't give you the answer, but we can work it out together. What would you try first?"
TIMEOUT = 30.0  # seconds


def call_usage(result) -> dict:
    """Tokens for this call only. accumulated_usage is a running total across every call the agent has made, so
    summing it over a conversation would count the early turns again and again."""
    latest = result.metrics.latest_agent_invocation
    u = latest.usage if latest else {"inputTokens": 0, "outputTokens": 0}
    return {"input_tokens": u["inputTokens"], "output_tokens": u["outputTokens"]}


def without_thinking(text: str) -> str:
    """Drop the <thinking> blocks some models write, as an app would before showing the reply."""
    text = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.S)
    return re.sub(r"<thinking>.*", "", text, flags=re.S).strip()


class Tutor:
    """One conversation about one problem. guard=None turns the guard off."""

    def __init__(self, problem: Problem, model: Model, guard=value_match):
        self.problem, self.guard = problem, guard
        self.agent = Agent(model=model, system_prompt=TUTOR_PROMPT.format(problem=problem.text), callback_handler=None)

    async def reply(self, message: str) -> dict:
        turn = {"student": message, "raw": "", "shown": FALLBACK, "blocked": None, "error": None, "usage": None}
        try:
            result = await asyncio.wait_for(self.agent.invoke_async(message), timeout=TIMEOUT)
            turn["raw"] = without_thinking(str(result))
            turn["usage"] = call_usage(result)
        except Exception as e:  # a failed call shows the fallback, never an error message
            turn["error"] = f"{type(e).__name__}: {e}"[:300]
            return turn
        turn["blocked"] = self.guard(turn["raw"], self.problem, message) if self.guard else None
        if turn["blocked"]:
            # The model should remember what the student saw, not the answer it tried to give.
            self.agent.messages[-1]["content"] = [{"text": FALLBACK}]
        else:
            turn["shown"] = turn["raw"]
        return turn
