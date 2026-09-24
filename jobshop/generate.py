"""Seeded instance generators.

``uniform`` and ``bottleneck`` set ``target_makespan`` from an exact
optimum on tiny instances, and from ``ceil(lower_bound * slack)``
otherwise. The default slack is 1.5. ``tight`` always uses
``ceil(lower_bound * 1.05)``.
"""

import math
import random

from jobshop.env import Instance, Operation
from jobshop.verifier import lower_bound, optimal_makespan

_TINY_OPERATIONS = 9


def uniform(
    *,
    seed: int,
    n_jobs: int = 3,
    n_machines: int = 3,
    duration: tuple[int, int] = (1, 5),
    slack: float = 1.5,
) -> Instance:
    """Each job visits every machine once, in a random order.

    Durations are drawn uniformly from ``duration`` (inclusive).
    """
    jobs = _jobs(random.Random(seed), n_jobs, n_machines, duration, factor=1)
    return _with_target(jobs, slack, exact=True)


def bottleneck(
    *,
    seed: int,
    n_jobs: int = 3,
    n_machines: int = 3,
    duration: tuple[int, int] = (1, 5),
    factor: int = 5,
    slack: float = 1.5,
) -> Instance:
    """Like ``uniform``, but every operation on machine 0 lasts ``factor`` times longer."""
    jobs = _jobs(random.Random(seed), n_jobs, n_machines, duration, factor=factor)
    return _with_target(jobs, slack, exact=True)


def tight(
    *,
    seed: int,
    n_jobs: int = 3,
    n_machines: int = 3,
    duration: tuple[int, int] = (1, 5),
    slack: float = 1.05,
) -> Instance:
    """Like ``uniform``, with a target about 1.05 times the lower bound."""
    jobs = _jobs(random.Random(seed), n_jobs, n_machines, duration, factor=1)
    return _with_target(jobs, slack, exact=False)


def _jobs(
    rng: random.Random,
    n_jobs: int,
    n_machines: int,
    duration: tuple[int, int],
    factor: int,
) -> tuple[tuple[Operation, ...], ...]:
    low, high = duration
    jobs: list[tuple[Operation, ...]] = []
    for _ in range(n_jobs):
        order = list(range(n_machines))
        rng.shuffle(order)
        operations: list[Operation] = []
        for machine in order:
            length = rng.randint(low, high)
            if machine == 0:
                length *= factor
            operations.append(Operation(machine, length))
        jobs.append(tuple(operations))
    return tuple(jobs)


def _with_target(
    jobs: tuple[tuple[Operation, ...], ...],
    slack: float,
    exact: bool,
) -> Instance:
    blank = Instance(jobs, target_makespan=0)
    n_ops = sum(len(job) for job in jobs)
    if exact and n_ops <= _TINY_OPERATIONS:
        target = optimal_makespan(blank)
    else:
        target = math.ceil(lower_bound(blank) * slack)
    return Instance(jobs, target_makespan=target)
