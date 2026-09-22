"""One greedy dispatch rule.

The environment allows double-booking. This policy still chooses start
times that keep machines free, so its success rate is a real baseline
rather than the exploit.
"""

from jobshop.env import Action, JobShopEnv


def most_work_remaining(env: JobShopEnv) -> list[Action]:
    """Run one episode: always dispatch the eligible job with the most work left.

    Work left is the sum of durations of that job's unscheduled operations.
    The chosen start is the earliest time at or after the clock that
    respects both job precedence and machine capacity. Returns the action
    log. Does not mutate a caller's copy of the instance.
    """
    raise NotImplementedError
