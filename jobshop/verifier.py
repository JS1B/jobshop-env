"""Final-state verifier.

``verify`` rebuilds the schedule from ``state.log`` and ``state.instance``.
It does not read ``state.done`` or ``state.makespan``.
"""

from jobshop.env import Instance, State


def lower_bound(instance: Instance) -> int:
    """Max of the longest job and the busiest machine's total load."""
    raise NotImplementedError


def optimal_makespan(instance: Instance) -> int:
    """Exact optimum by brute force. Used for tiny fixtures only."""
    raise NotImplementedError


def verify(state: State) -> int:
    """Return 1 if the replayed log is a complete feasible schedule, else 0.

    Feasible means: every action would have passed ``step``, operations of
    a job do not overlap and keep their order, no machine runs two
    operations at once, and the finish time is at most
    ``instance.target_makespan``. An empty log scores 0 even if ``done``
    is true. A log containing an action ``step`` would reject scores 0.
    """
    raise NotImplementedError
