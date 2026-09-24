"""Simulator seam: legal transitions, rejected actions, and the capacity hole."""

import pytest

from jobshop import Action, Instance, JobShopEnv, Observation, Operation
from tests.test_verifier import optimal_log, tiny


def test_reset_hides_the_target() -> None:
    obs = JobShopEnv(tiny()).reset()
    assert isinstance(obs, Observation)
    assert obs.clock == 0
    assert obs.log == ()
    assert obs.jobs == tiny().jobs
    assert not hasattr(obs, "target_makespan")


def test_invalid_actions_do_not_mutate() -> None:
    env = JobShopEnv(tiny())
    env.reset()
    with pytest.raises(ValueError):
        env.step(Action(9, 0))
    assert env.state.log == ()

    env.step(Action(0, 0))
    with pytest.raises(ValueError):
        env.step(Action(1, -1))
    assert env.state.log == (Action(0, 0),)

    # Clock is still 0, so t=1 is not in the past, but job 0's first op ends at 2.
    with pytest.raises(ValueError):
        env.step(Action(0, 1))
    assert env.state.log == (Action(0, 0),)


def test_optimal_episode_reward_is_one() -> None:
    env = JobShopEnv(tiny())
    env.reset()
    reward = 0.0
    done = False
    for action in optimal_log():
        _obs, reward, done, _info = env.step(action)
    assert done is True
    assert reward == 1.0


def test_step_accepts_double_booking() -> None:
    instance = Instance(
        jobs=(
            (Operation(0, 3), Operation(1, 1)),
            (Operation(0, 3), Operation(1, 1)),
        ),
        target_makespan=100,
    )
    env = JobShopEnv(instance)
    env.reset()
    env.step(Action(0, 0))
    _obs, reward, done, _info = env.step(Action(1, 0))
    assert done is False
    assert reward == 0.0
    assert env.state.log == (Action(0, 0), Action(1, 0))
