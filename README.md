# Job-shop environment

A small job-shop scheduling environment with a separate verifier that scores only the final state.

A policy (rule, search, or model) schedules one operation at a time by picking a job and a start time. The environment enforces job order and rejects starts in the past, but does **not** prevent double-booked machines. The terminal reward is the verifier score (0 or 1). Observations exclude the target schedule and target finish time.

## Quick start

Requires Python 3.11+.

```bash
make test       # verifier, environment, generator, scenario, and exploit tests
make demo       # greedy baseline on three seeded variants, 10 episodes each
make scenario   # three planners on the Hartwig week
```

The first run creates `.venv/` and installs the package with pytest. Charts are written to `out/` as SVG; open them in a browser. `out/double-booked.svg` shows two jobs stacked on machine 0 at the same time.

Single episode (`--variant` is `uniform`, `bottleneck`, or `tight`):

```bash
.venv/bin/python -m jobshop.demo --variant uniform --seed 0
```

This prints the verifier score and writes `out/uniform-seed0.svg`.

## Scenario: the Hartwig week

Hartwig Zerspanung GmbH is fictional. It has three machines: a 5-axis mill, a CNC lathe, and a deburr-and-inspection station. Time is in working hours: one 8-hour shift per day from Monday 06:00. The truck leaves at hour 40 (end of Friday's shift), which is also the optimal makespan.

| Order | Customer | Routing (hours) |
| --- | --- | --- |
| Pump flange | Rhein Hydraulik | lathe 8 → mill 16 → inspect 2 |
| Gearbox housing | Alb Getriebe | mill 12 → lathe 4 → inspect 2 |
| Sensor bracket | Neckar Sensorik | mill 10 → lathe 6 → inspect 2 |

Finish hour per order:

| Planner | Flange | Housing | Bracket |
| --- | --- | --- | --- |
| Greedy dispatch rule | 54 | 58 | 60 |
| Senior planner | 40 | 18 | 30 |
| Shortcut planner (mill double-booked) | 30 | 22 | 18 |

These values are pinned by `tests/test_scenario.py`.

## Further reading

Decisions, results, limits, and next steps: [`NOTE.md`](NOTE.md).
