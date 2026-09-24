"""Final-state verifier.

``verify`` rebuilds the schedule from ``state.log`` and ``state.instance``.
It does not read ``state.done`` or ``state.makespan``.
"""

from jobshop.env import Instance, State, action_error


_TINY_OPERATIONS = 9


def lower_bound(instance: Instance) -> int:
    """Max of the longest job and the busiest machine's total load."""
    job_load = [sum(op.duration for op in job) for job in instance.jobs]
    machine_load: dict[int, int] = {}
    for job in instance.jobs:
        for op in job:
            machine_load[op.machine] = machine_load.get(op.machine, 0) + op.duration
    if not job_load or not machine_load:
        return 0
    return max(max(job_load), max(machine_load.values()))


def optimal_makespan(instance: Instance) -> int:
    """Exact optimum by brute force. Used for tiny fixtures only.

    Tries every order that keeps each job's operations in sequence, and
    starts each operation at the earliest time that order allows. Instances
    with more than 9 operations raise ``ValueError``.
    """
    jobs = instance.jobs
    n_ops = sum(len(job) for job in jobs)
    if n_ops > _TINY_OPERATIONS:
        raise ValueError(f"optimal_makespan supports at most {_TINY_OPERATIONS} operations")
    if n_ops == 0:
        return 0
    n_jobs = len(jobs)
    machine_ready = {op.machine: 0 for job in jobs for op in job}
    next_op = [0] * n_jobs
    job_ready = [0] * n_jobs
    best = sum(op.duration for job in jobs for op in job)

    def search(placed: int, horizon: int) -> None:
        nonlocal best
        if horizon >= best:
            return
        if placed == n_ops:
            best = horizon
            return
        for job in range(n_jobs):
            index = next_op[job]
            if index >= len(jobs[job]):
                continue
            op = jobs[job][index]
            end = max(job_ready[job], machine_ready[op.machine]) + op.duration
            if end >= best:
                continue
            next_op[job] = index + 1
            previous_job = job_ready[job]
            previous_machine = machine_ready[op.machine]
            job_ready[job] = end
            machine_ready[op.machine] = end
            search(placed + 1, max(horizon, end))
            next_op[job] = index
            job_ready[job] = previous_job
            machine_ready[op.machine] = previous_machine

    search(0, 0)
    return best


def verify(state: State) -> int:
    """Return 1 if the replayed log is a complete feasible schedule, else 0.

    Feasible means: every action would have passed ``step``, operations of
    a job do not overlap and keep their order, no machine runs two
    operations at once, and the finish time is at most
    ``instance.target_makespan``. An empty log scores 0 even if ``done``
    is true. A log containing an action ``step`` would reject scores 0.
    ``state.done`` and ``state.makespan`` are ignored.
    """
    instance = state.instance
    n_jobs = len(instance.jobs)
    clock = 0
    next_op = [0] * n_jobs
    ready_at = [0] * n_jobs
    spans: dict[int, list[tuple[int, int]]] = {}
    for action in state.log:
        if action_error(instance, clock, tuple(next_op), tuple(ready_at), action):
            return 0
        operation = instance.jobs[action.job][next_op[action.job]]
        end = action.start_time + operation.duration
        spans.setdefault(operation.machine, []).append((action.start_time, end))
        next_op[action.job] += 1
        ready_at[action.job] = end
        clock = max(clock, action.start_time)
    if any(next_op[job] != len(instance.jobs[job]) for job in range(n_jobs)):
        return 0
    finish = 0
    for intervals in spans.values():
        intervals.sort()
        previous_end = None
        for start, end in intervals:
            if previous_end is not None and start < previous_end:
                return 0
            previous_end = end
            finish = max(finish, end)
    if finish > instance.target_makespan:
        return 0
    return 1
