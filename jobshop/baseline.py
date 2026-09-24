"""One greedy dispatch rule.

The environment allows double-booking. This policy still chooses start
times that keep machines free, so its success rate is a real baseline
rather than the exploit.
"""

from jobshop.env import Action, JobShopEnv, Observation, Operation


def most_work_remaining(env: JobShopEnv) -> list[Action]:
    """Run one episode: always dispatch the eligible job with the most work left.

    Work left is the sum of durations of that job's unscheduled operations.
    The chosen start is the earliest time at or after the clock that
    respects both job precedence and machine capacity. Returns the action
    log. Does not mutate a caller's copy of the instance.
    """
    observation = env.reset()
    actions: list[Action] = []
    while not env.state.done:
        action = _next_action(observation)
        actions.append(action)
        observation, _reward, done, _info = env.step(action)
        if done:
            break
    return actions


def _next_action(observation: Observation) -> Action:
    next_op, ready_at, spans = _replay(observation)
    chosen: tuple[int, int] | None = None
    for job, operations in enumerate(observation.jobs):
        if next_op[job] >= len(operations):
            continue
        work = sum(op.duration for op in operations[next_op[job] :])
        if chosen is None or work > chosen[0] or (work == chosen[0] and job < chosen[1]):
            chosen = (work, job)
    if chosen is None:
        raise RuntimeError("no operation left to dispatch")
    job = chosen[1]
    operation = observation.jobs[job][next_op[job]]
    start = _earliest_start(
        observation.clock,
        ready_at[job],
        operation.duration,
        spans.get(operation.machine, ()),
    )
    return Action(job, start)


def _replay(
    observation: Observation,
) -> tuple[list[int], list[int], dict[int, tuple[tuple[int, int], ...]]]:
    next_op = [0] * len(observation.jobs)
    ready_at = [0] * len(observation.jobs)
    spans: dict[int, list[tuple[int, int]]] = {}
    for action in observation.log:
        operation: Operation = observation.jobs[action.job][next_op[action.job]]
        end = action.start_time + operation.duration
        next_op[action.job] += 1
        ready_at[action.job] = end
        spans.setdefault(operation.machine, []).append((action.start_time, end))
    frozen = {machine: tuple(sorted(intervals)) for machine, intervals in spans.items()}
    return next_op, ready_at, frozen


def _earliest_start(
    clock: int,
    ready: int,
    duration: int,
    intervals: tuple[tuple[int, int], ...],
) -> int:
    start = max(clock, ready)
    for begin, end in intervals:
        if start >= end:
            continue
        if start + duration <= begin:
            return start
        start = end
    return start
