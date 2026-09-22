# Job-shop environment

A small job-shop scheduling environment with a separate verifier that scores only the final state.

The agent schedules one operation at a time by choosing a job and a start time. The environment keeps each job in order and rejects a start in the past. It does not keep machines from being double-booked. The terminal reward is the verifier score, 0 or 1. The observation does not include a target schedule or the target finish time.

## Run

From this directory, with Python 3.11+ and pytest:

```bash
pip install -e ".[dev]"
make test
```

`make test` collects four verifier tests. They are skipped until the verifier is implemented.

`make demo` will print the greedy baseline's success rate on three seeded variants. It is not implemented yet.
