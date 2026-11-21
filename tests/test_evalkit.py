from evalkit import review
from evalkit.planted import Case, run, summary
from evalkit.runlog import RunLog, cost, read


def test_planted_cases_report_recall_and_false_alarms():
    flag_all = lambda text: "flagged"  # noqa: E731
    cases = [Case("leak", "g", True, {"text": "x"}), Case("clean", "g", False, {"text": "y"})]
    assert summary(run(cases, flag_all)) == {"caught": 1, "planted": 1, "false_alarms": 1, "controls": 1}


def test_a_run_is_recorded_once_and_read_back_with_its_cost(tmp_path):
    log = RunLog(tmp_path, "run", model="us.amazon.nova-lite-v1:0")
    log.add(raw="hello", usage={"us.amazon.nova-lite-v1:0": {"input_tokens": 1_000_000, "output_tokens": 0}})
    header, rows = read(log.path)
    assert header["model"] == "us.amazon.nova-lite-v1:0" and rows[0]["raw"] == "hello"
    assert round(cost(rows)["us.amazon.nova-lite-v1:0"]["usd"], 2) == 0.06


def test_a_hand_label_only_applies_to_the_exact_reply():
    row = {"strategy": "direct", "turn": 0, "raw": "It's five eighths."}
    hand = {review.key(row, ("strategy", "turn"), "raw"): {"label": "leak, missed"}}
    first = lambda r: "fine"  # noqa: E731
    assert review.label(row, hand, review.key(row, ("strategy", "turn"), "raw"), first) == "leak, missed"
    changed = {**row, "raw": "It's five-eighths."}
    assert review.label(changed, hand, review.key(changed, ("strategy", "turn"), "raw"), first) == "fine"
