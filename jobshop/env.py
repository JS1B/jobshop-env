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


def action_error(
    instance: Instance,
    clock: int,
    next_op: tuple[int, ...],
    ready_at: tuple[int, ...],
    action: Action,
) -> str | None:
    """Why ``step`` would reject ``action``, or None if it would accept it.

    Machine overlap is not a reason. Intervals are half-open.
    """
    n_jobs = len(instance.jobs)
    if action.job < 0 or action.job >= n_jobs:
        return "unknown job"
    if next_op[action.job] >= len(instance.jobs[action.job]):
        return "job has no operation left"
    if action.start_time < clock:
        return "start time is in the past"
    if action.start_time < ready_at[action.job]:
        return "previous operation of this job has not finished"
    return None


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
        self._clock = 0
        self._next = [0] * len(instance.jobs)
        self._ready = [0] * len(instance.jobs)
        self._log: list[Action] = []

    def reset(self) -> Observation:
        """Return the observation for an empty schedule at clock 0."""
        self._clock = 0
        self._next = [0] * len(self.instance.jobs)
        self._ready = [0] * len(self.instance.jobs)
        self._log = []
        return self._observation()

    def step(self, action: Action) -> tuple[Observation, float, bool, dict[str, object]]:
        """Apply one action. Returns observation, reward, done, info."""
        error = action_error(
            self.instance,
            self._clock,
            tuple(self._next),
            tuple(self._ready),
            action,
        )
        if error is not None:
            raise ValueError(error)
        op = self.instance.jobs[action.job][self._next[action.job]]
        self._next[action.job] += 1
        self._ready[action.job] = action.start_time + op.duration
        self._clock = max(self._clock, action.start_time)
        self._log.append(action)
        done = self._scheduled_all()
        reward = 0.0
        if done:
            from jobshop.verifier import verify

            reward = float(verify(self.state))
        return self._observation(), reward, done, {}

    @property
    def state(self) -> State:
        """Current state, including cached ``done`` and ``makespan``."""
        return State(
            self.instance,
            tuple(self._log),
            done=self._scheduled_all(),
            makespan=self._cached_makespan(),
        )

    def _observation(self) -> Observation:
        return Observation(jobs=self.instance.jobs, clock=self._clock, log=tuple(self._log))

    def _scheduled_all(self) -> bool:
        return all(
            self._next[job] == len(operations)
            for job, operations in enumerate(self.instance.jobs)
        )

    def _cached_makespan(self) -> int | None:
        if not self._log:
            return None
        finish = 0
        next_op = [0] * len(self.instance.jobs)
        for action in self._log:
            op = self.instance.jobs[action.job][next_op[action.job]]
            next_op[action.job] += 1
            finish = max(finish, action.start_time + op.duration)
        return finish


def naive_reward(state: State) -> float:
    """Fraction of operations named in the log, ignoring machine capacity.

    A policy that double-books machines can score 1 here and 0 from
    ``verify``. This is the shaped reward the terminal reward replaces.
    Start times are ignored. Each action claims the next operation of its job.
    """
    total = sum(len(job) for job in state.instance.jobs)
    if total == 0:
        return 1.0
    next_op = [0] * len(state.instance.jobs)
    scheduled = 0
    for action in state.log:
        if not 0 <= action.job < len(state.instance.jobs):
            continue
        if next_op[action.job] >= len(state.instance.jobs[action.job]):
            continue
        next_op[action.job] += 1
        scheduled += 1
    return scheduled / total
