"""Job-shop environment.

The agent acts with ``(job, start_time)`` and always schedules that job's
next operation. The environment enforces precedence and rejects a start in
the past. It does not enforce machine capacity: two operations may occupy
the same machine at the same time. That gap is the reward exploit.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Operation:
    """One step of a job."""

    machine: int
    duration: int


@dataclass(frozen=True)
class Instance:
    """Full problem spec, including the finish-time ceiling.

    ``target_makespan`` is for the verifier. Observations must not carry it
    or a target schedule.
    """

    jobs: tuple[tuple[Operation, ...], ...]
    target_makespan: int


@dataclass(frozen=True)
class Action:
    """Schedule ``job``'s next operation to start at ``start_time``."""

    job: int
    start_time: int


@dataclass(frozen=True)
class State:
    """Final state. The verifier may read ``instance`` and ``log`` only.

    ``done`` and ``makespan`` are cached conveniences. A replay ignores them,
    so writing ``done=True`` on an empty log does not pass.
    """

    instance: Instance
    log: tuple[Action, ...]
    done: bool = False
    makespan: int | None = None


@dataclass(frozen=True)
class Observation:
    """Agent view. Same jobs as the instance, without the target makespan."""

    jobs: tuple[tuple[Operation, ...], ...]
    clock: int
    log: tuple[Action, ...]


class JobShopEnv:
    """Episode over one instance.

    The clock starts at 0 and becomes the latest accepted start time.
    ``step`` raises ``ValueError`` without mutating state when the action
    names an unknown job, would schedule anything other than that job's
    next operation, or uses a ``start_time`` earlier than the clock.
    Overlapping machine intervals are accepted.

    Intermediate rewards are 0. When every operation has been scheduled,
    the episode ends and the reward is ``verify(state)`` (0 or 1).
    """

    def __init__(self, instance: Instance) -> None:
        self.instance = instance

    def reset(self) -> Observation:
        """Return the observation for an empty schedule at clock 0."""
        raise NotImplementedError

    def step(self, action: Action) -> tuple[Observation, float, bool, dict[str, object]]:
        """Apply one action. Returns observation, reward, done, info."""
        raise NotImplementedError

    @property
    def state(self) -> State:
        """Current state, including cached ``done`` and ``makespan``."""
        raise NotImplementedError


def naive_reward(state: State) -> float:
    """Fraction of operations named in the log, ignoring machine capacity.

    A policy that double-books machines can score 1 here and 0 from
    ``verify``. This is the shaped reward the terminal reward replaces.
    """
    raise NotImplementedError
