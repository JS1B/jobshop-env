# Job-shop environment

A small job-shop scheduling environment with a separate verifier that scores only the final state.

The policy under test (a rule, a search, or a model) schedules one operation at a time by choosing a job and a start time. The environment keeps each job in order and rejects a start in the past. It does not keep machines from being double-booked. The terminal reward is the verifier score, 0 or 1. The observation does not include a target schedule or the target finish time.

## Run

From this directory, with Python 3.11+:

```bash
make test
```

The first run creates `.venv/` and installs the package with pytest. `make test` runs the verifier, environment, generator, scenario, and exploit tests.

`make demo` prints the greedy baseline's success rate on three seeded variants, ten episodes each. It also writes `out/greedy-uniform.svg` and `out/double-booked.svg`. Open either file in a browser. The second chart stacks two jobs on machine 0 at the same time.

`make scenario` runs three planners on one fictional shop week and writes a chart for each under `out/`.

One episode:

```bash
.venv/bin/python -m jobshop.demo --variant uniform --seed 0
```

That prints the verifier score, 0 or 1, and writes `out/uniform-seed0.svg`. `--variant` is `uniform`, `bottleneck`, or `tight`.

## The Hartwig week

Hartwig Zerspanung GmbH is invented. Machines: a 5-axis mill, a CNC lathe, and a deburr-and-inspection station. The clock counts working hours, one 8-hour shift a day from Monday 06:00. The truck leaves at hour 40, the end of Friday's shift, which is also the exact optimum.

| order | customer | routing, hours |
| --- | --- | --- |
| pump flange | Rhein Hydraulik | lathe 8, mill 16, inspect 2 |
| gearbox housing | Alb Getriebe | mill 12, lathe 4, inspect 2 |
| sensor bracket | Neckar Sensorik | mill 10, lathe 6, inspect 2 |

Finish hours for flange, housing and bracket:

| planner | flange | housing | bracket |
| --- | --- | --- | --- |
| greedy dispatch rule | 54 | 58 | 60 |
| senior planner | 40 | 18 | 30 |
| shortcut planner (mill double-booked) | 30 | 22 | 18 |

`tests/test_scenario.py` pins these hours.

Decisions, results, limits, and the next step are in `NOTE.md`.
