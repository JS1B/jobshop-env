# Job-shop environment

## One week at Hartwig

I picked machine scheduling because it is easy to explain and hard to solve. Finding a good plan is hard, but checking a finished one takes milliseconds and needs no human judge. That gap is what makes it a good environment.

To make it concrete I made up a small machining shop, Hartwig Zerspanung GmbH: three orders, a 5-axis mill, a lathe, an inspection station, and a truck that leaves at the end of Friday's shift. I tuned the hours so the truck leaves exactly at the best possible finish, hour 40. Then I gave the same week to three planners:

| planner | finish hour | naive reward | verifier | ships |
| --- | --- | --- | --- | --- |
| greedy dispatch rule | 60 | 1.0 | 0 | no, late |
| senior planner (exhaustive search) | 40 | 1.0 | 1 | yes |
| shortcut planner | 30 | 1.0 | 0 | no, mill double-booked |

The naive reward gives all three 1.0, because it only counts whether every operation got scheduled. The shortcut plan even looks like the best one on paper, but it gets to hour 30 by running two orders on the mill at once, so on the floor it misses the truck. Only the verifier catches that. It returns a single bit, so it does not say why the other two failed.

## How it is built

I like building simulators out of separate parts, and here the split between simulator and verifier is the whole point. The simulator keeps each order's operations in sequence and refuses starts in the past, but it lets you double-book a machine. The verifier replays the finished log and decides. Real planning works the same way: an ERP system will book one work center twice until somebody checks the load. If the simulator blocked that, the policy under test could never make the mistake that actually costs a delivery, and I would have nothing to measure. It is the same shape as the multi-agent planning course I took at DTU, where a server refereed every move our planner sent, except here the check runs once on the finished plan.

The policy sends a job and a start time, which schedules that job's next operation. It never sees the target. The environment scores its own copy of the instance, and the verifier rebuilds everything from the log instead of trusting cached fields like `done`. Up to 9 operations the target is the exact optimum, found by brute force. Above that it is 1.5 times a lower bound, the longest job or the busiest machine. `tight` uses 1.05 times the bound, but never less than the optimum when I know it.

## Results

The baseline is a greedy rule: start the job with the most work left, as early as its machine is free. On thirty generated 3×3 weeks, seeds 0 to 9 (`make demo`):

| uniform | bottleneck | tight |
| --- | --- | --- |
| 2/10 | 4/10 | 3/10 |

It misses more often than it hits, which is what I wanted. If a simple rule always won, the task would not be worth training on. My first version of `tight` scored 2/10, and when I checked, six of the ten targets were below the optimum, so nothing could have solved them. Now the target never drops below a known optimum, and tests pin every number in this note.

The exploit is the naive reward itself. A double-booked log scores 1 on it and 0 on the verifier, and played through `step` the episode ends with reward 0. `tests/test_exploit.py` checks both.

## Limits

Above 9 operations I do not know the optimum, so a target can be unreachable. It is one rule on thirty small weeks, with no learned policy. Hartwig's hours are invented, with no setup times, quantities, per-order due dates or breakdowns. Untrusted code should be scored from its saved log in a separate process.

## What I would do next

Build the weeks from real routing sheets and operation confirmations instead of generating them: quantities, setup and run times, per-order due dates and actual hours. Success then becomes "feasible, and every order on time", which does not need a known optimum. I would hold out whole customers for evaluation, so a policy cannot just learn one shop. A Gymnasium adapter and a container come after that.
