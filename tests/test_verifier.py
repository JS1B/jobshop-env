"""The four verifier cases. Skipped until the verifier is implemented."""

import pytest

from jobshop import Action, Instance, Operation, State, verify


def _tiny() -> Instance:
    # Job 0: m0 for 2, then m1 for 3. Job 1: m1 for 2, then m0 for 2.
    # Lower bound is max(job 5, job 4, m0 load 4, m1 load 5) = 5.
    return Instance(
        jobs=(
            (Operation(0, 2), Operation(1, 3)),
            (Operation(1, 2), Operation(0, 2)),
        ),
        target_makespan=5,
    )


def _optimal_log() -> tuple[Action, ...]:
    # m0: job 0 [0, 2), job 1 [2, 4). m1: job 1 [0, 2), job 0 [2, 5).
    return (Action(0, 0), Action(1, 0), Action(1, 2), Action(0, 2))


@pytest.mark.skip(reason="verifier is implemented in the next step")
def test_correct_solution_scores_one() -> None:
    state = State(_tiny(), _optimal_log(), done=True, makespan=5)
    assert verify(state) == 1


@pytest.mark.skip(reason="verifier is implemented in the next step")
def test_cached_done_with_empty_log_scores_zero() -> None:
    state = State(_tiny(), (), done=True, makespan=5)
    assert verify(state) == 0


@pytest.mark.skip(reason="verifier is implemented in the next step")
def test_forged_invalid_action_scores_zero() -> None:
    # The optimal log is feasible. One extra action schedules a job that has
    # no operation left, which step would reject. Cached fields still claim success.
    log = _optimal_log() + (Action(0, 2),)
    state = State(_tiny(), log, done=True, makespan=5)
    assert verify(state) == 0


@pytest.mark.skip(reason="verifier is implemented in the next step")
def test_double_booking_scores_zero() -> None:
    # Both jobs start on machine 0 at t=0. Target is loose, so only the
    # overlap can fail the verifier. Later ops do not overlap.
    instance = Instance(
        jobs=(
            (Operation(0, 3), Operation(1, 1)),
            (Operation(0, 3), Operation(1, 1)),
        ),
        target_makespan=100,
    )
    log = (Action(0, 0), Action(1, 0), Action(0, 3), Action(1, 4))
    state = State(instance, log, done=True, makespan=5)
    assert verify(state) == 0
