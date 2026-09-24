"""Verifier cases from the brief. The verifier reads the log, not cached fields."""

from jobshop import Action, Instance, Operation, State, verify


def tiny() -> Instance:
    # Job 0: m0 for 2, then m1 for 3. Job 1: m1 for 2, then m0 for 2.
    # Lower bound is max(job 5, job 4, m0 load 4, m1 load 5) = 5.
    return Instance(
        jobs=(
            (Operation(0, 2), Operation(1, 3)),
            (Operation(1, 2), Operation(0, 2)),
        ),
        target_makespan=5,
    )


def optimal_log() -> tuple[Action, ...]:
    # m0: job 0 [0, 2), job 1 [2, 4). m1: job 1 [0, 2), job 0 [2, 5).
    return (Action(0, 0), Action(1, 0), Action(1, 2), Action(0, 2))


def test_initial_state_scores_zero() -> None:
    assert verify(State(tiny(), ())) == 0


def test_correct_solution_scores_one() -> None:
    # Cached fields claim failure. The replay of the log is what scores.
    state = State(tiny(), optimal_log(), done=False, makespan=0)
    assert verify(state) == 1


def test_invalid_action_scores_zero() -> None:
    # One extra action schedules a job that has no operation left.
    log = optimal_log() + (Action(0, 2),)
    state = State(tiny(), log, done=True, makespan=5)
    assert verify(state) == 0


def test_written_goal_state_scores_zero() -> None:
    state = State(tiny(), (), done=True, makespan=5)
    assert verify(state) == 0
