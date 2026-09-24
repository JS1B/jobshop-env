# Job-shop environment

A small job-shop scheduling environment with a separate verifier that scores only the final state.

The agent schedules one operation at a time by choosing a job and a start time. The environment keeps each job in order and rejects a start in the past. It does not keep machines from being double-booked. The terminal reward is the verifier score, 0 or 1. The observation does not include a target schedule or the target finish time.

## Run

From this directory, with Python 3.11+ and pytest:

```bash
pip install -e ".[dev]"
make test
```

`make test` runs the verifier, the environment, the generators, and the exploit test.

`make demo` prints the greedy baseline's success rate on three seeded variants, ten episodes each. It also writes `out/greedy-uniform.svg` and `out/double-booked.svg`. Open either file in a browser. The second chart stacks two jobs on machine 0 at the same time.

One episode:

```bash
python -m jobshop.demo --variant uniform --seed 0
```

That prints the verifier score, 0 or 1, and writes `out/uniform-seed0.svg`. `--variant` is `uniform`, `bottleneck`, or `tight`.

Decisions, results, limits, and the next step are in `NOTE.md`.
