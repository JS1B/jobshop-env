"""Seeded instance generators.

``uniform`` and ``bottleneck`` set ``target_makespan`` from an exact
optimum on tiny instances, and from ``ceil(lower_bound * slack)``
otherwise. The default slack is 1.5. ``tight`` always uses
``ceil(lower_bound * 1.05)``.
"""

from jobshop.env import Instance


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
    raise NotImplementedError


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
    raise NotImplementedError


def tight(
    *,
    seed: int,
    n_jobs: int = 3,
    n_machines: int = 3,
    duration: tuple[int, int] = (1, 5),
    slack: float = 1.05,
) -> Instance:
    """Like ``uniform``, with a target about 1.05 times the lower bound."""
    raise NotImplementedError
