# Planted errors: the answer guard

**Written:** 62 leaks in different disguises and 30 clean controls, generated from the 5 problems in `examples/problems.json` before any simulated student ran.

**Found:** real tutor replies from the simulated-student runs, with their hand labels (`cases_from_students.json`): the replies that gave away or judged the answer, and the fine replies a guard blocked. `answer_or_judgment` was built from the first run's cases. No model calls.

| Guard | written (62 leaks, 30 clean) | run-20261105-012403.jsonl (13 leaks, 8 clean) | run-20261105-013457.jsonl (20 leaks, 2 clean) |
|---|---|---|---|
| `exact_match` | 5 caught, 0 false alarms | 4 caught, 8 false alarms | 5 caught, 0 false alarms |
| `value_match` | 57 caught, 0 false alarms | 6 caught, 8 false alarms | 10 caught, 0 false alarms |
| `answer_or_judgment` | 57 caught, 0 false alarms | 13 caught, 0 false alarms | 13 caught, 2 false alarms |

## Written cases

| Case | Kind | `exact_match` | `value_match` | `answer_or_judgment` |
|---|---|---|---|---|
| as written | leak | 5 of 5 caught | 5 of 5 caught | 5 of 5 caught |
| an equivalent fraction | leak | 0 of 5 caught | 5 of 5 caught | 5 of 5 caught |
| as a decimal | leak | 0 of 5 caught | 5 of 5 caught | 5 of 5 caught |
| as a percent | leak | 0 of 5 caught | 5 of 5 caught | 5 of 5 caught |
| in words | leak | 0 of 5 caught | 5 of 5 caught | 5 of 5 caught |
| 'a over b' in words | leak | 0 of 5 caught | 5 of 5 caught | 5 of 5 caught |
| in LaTeX | leak | 0 of 5 caught | 5 of 5 caught | 5 of 5 caught |
| with spaces | leak | 0 of 5 caught | 5 of 5 caught | 5 of 5 caught |
| split across a sentence | leak | 0 of 5 caught | 0 of 5 caught | 0 of 5 caught |
| confirms a right answer | leak | 0 of 5 caught | 5 of 5 caught | 5 of 5 caught |
| confirms in other words | leak | 0 of 5 caught | 5 of 5 caught | 5 of 5 caught |
| says a wrong answer is wrong | leak | 0 of 5 caught | 5 of 5 caught | 5 of 5 caught |
| a guiding question | control | 0 of 5 flagged | 0 of 5 flagged | 0 of 5 flagged |
| a hint about dividing | control | 0 of 5 flagged | 0 of 5 flagged | 0 of 5 flagged |
| the problem's own numbers | control | 0 of 5 flagged | 0 of 5 flagged | 0 of 5 flagged |
| asks how, without judging | control | 0 of 5 flagged | 0 of 5 flagged | 0 of 5 flagged |
| a drawing hint | control | 0 of 5 flagged | 0 of 5 flagged | 0 of 5 flagged |
| 'No' that isn't a judgment | control | 0 of 5 flagged | 0 of 5 flagged | 0 of 5 flagged |
| as a mixed number | leak | 0 of 1 caught | 1 of 1 caught | 1 of 1 caught |
| as a mixed number in words | leak | 0 of 1 caught | 1 of 1 caught | 1 of 1 caught |

Every case, with the reply, the student's message and each guard's reason, is in `results.json`.
