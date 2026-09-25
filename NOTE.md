# Job-shop environment

## One week at Hartwig

Hartwig Zerspanung GmbH is a machining shop I made up: three orders, three machines, one truck at the end of Friday's shift. I chose the hours so the truck leaves at the best possible finish, hour 40. Only a plan that is optimal and never double-books a machine ships.

| planner | finish hour | naive reward | verifier | ships |
| --- | --- | --- | --- | --- |
| greedy dispatch rule | 60 | 1.0 | 0 | no, late |
| senior planner (exhaustive search) | 40 | 1.0 | 1 | yes |
| shortcut planner | 30 | 1.0 | 0 | no, mill double-booked |

The naive reward scores all three 1.0. The verifier passes only the plan that ships. It returns one bit, so it does not say why the other two failed. `make scenario` runs the week; the hours are in the README.

## The idea

The simulator accepts almost any plan, and a separate verifier decides what counts. An infinite-capacity plan in an ERP system works the same way: it books one work center twice until someone checks the load. If the environment blocked the overlap, the policy under test could never make the mistake that costs a delivery, and I could not measure it.

Checking a plan is cheap even when finding one is hard. A replay takes milliseconds and needs no human judge, which lets the reward scale. The checker is the contract; what a buyer pays for is the weeks it runs on.

## Decisions

- The policy under test (a rule, a search, or a model) sends a job and a start time, which schedules that job's next operation. Starts come in time order and after the job's previous operation. Double-booking is accepted.
- The observation shows the jobs, the clock and the log, never the target. The environment scores its own copy of the instance, so editing what it hands out changes nothing.
- The verifier replays the log and ignores the cached `done` and `makespan`. It returns 1 only if the log is complete and legal, no machine overlaps, and the finish meets the target. That bit is the episode's reward.
- Targets: the exact optimum up to 9 operations, else `ceil(lower bound × 1.5)`, where the lower bound is the longest job or the busiest machine. `tight` uses `ceil(lower bound × 1.05)`, raised to the optimum when it is known, so every small `tight` week is solvable.
- The baseline dispatches the job with the most work left, at the earliest start at or after the clock that keeps its machine free. Ties go to the lower job index.

## Results

Greedy baseline, thirty generated 3×3 weeks, seeds 0 to 9 (`make demo`). Success means meeting the target, here the optimum or just above the bound:

| uniform | bottleneck | tight |
| --- | --- | --- |
| 2/10 | 4/10 | 3/10 |

The naive reward is the fraction of operations named in the log. It ignores machines and start times, so a double-booked log scores 1 on it and 0 on the verifier, and ends with reward 0 through `step`. `tests/test_exploit.py` checks both. Other tests cover the brief's verifier cases, edited observations, and every number in this note.

## Limits

Exact optima stop at 9 operations; above that a slack target can be unreachable. One rule, thirty small weeks, no learned policy. The hours are invented, with no setups, quantities, per-order due dates, breakdowns, alternative machines or shift calendars. Untrusted code should be scored from the saved log in a separate process.

## Next

Build weeks from licensed routing sheets and operation confirmations: quantities, setup and run times, per-order due dates, actual hours. Success becomes "feasible, every order on time", which needs no known optimum. Hold out whole customers for evaluation. A Gymnasium adapter and a container come after.
