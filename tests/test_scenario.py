"""The fictional shop week: a missed truck, a shippable plan, and the exploit."""

import pytest

from jobshop.env import JobShopEnv, naive_reward
from jobshop.scenario import (
    MACHINE_INDEX,
    ROUTING_SHEET,
    TRUCK_HOUR,
    _finish_hours,
    dispatch_rule,
    instance_from_sheet,
    senior_planner,
    shortcut_planner,
)
from jobshop.verifier import optimal_makespan, verify


@pytest.mark.parametrize(
    ("planner", "flange_housing_bracket"),
    [
        (dispatch_rule, (54, 58, 60)),
        (senior_planner, (40, 18, 30)),
        (shortcut_planner, (30, 22, 18)),
    ],
)
def test_finish_hours_match_the_note(planner, flange_housing_bracket) -> None:
    env = JobShopEnv(instance_from_sheet(ROUTING_SHEET, TRUCK_HOUR))
    planner(env)
    assert _finish_hours(env) == flange_housing_bracket
    assert naive_reward(env.state) == 1.0


def test_dispatch_misses_the_deadline() -> None:
    env = JobShopEnv(instance_from_sheet(ROUTING_SHEET, TRUCK_HOUR))
    dispatch_rule(env)
    assert env.state.makespan == 60
    assert env.state.makespan > env.instance.target_makespan
    assert verify(env.state) == 0


def test_deadline_is_the_optimum() -> None:
    instance = instance_from_sheet(ROUTING_SHEET, TRUCK_HOUR)
    assert instance.target_makespan == optimal_makespan(instance)


def test_senior_planner_scores_one_through_the_env() -> None:
    env = JobShopEnv(instance_from_sheet(ROUTING_SHEET, TRUCK_HOUR))
    reward = senior_planner(env)
    assert reward == 1.0
    assert verify(env.state) == 1


def test_shortcut_scores_naive_one_and_verifier_zero() -> None:
    env = JobShopEnv(instance_from_sheet(ROUTING_SHEET, TRUCK_HOUR))
    reward = shortcut_planner(env)
    assert naive_reward(env.state) == 1.0
    assert verify(env.state) == 0
    assert reward == 0.0


def test_sheet_maps_machine_names_to_indices() -> None:
    instance = instance_from_sheet(ROUTING_SHEET, TRUCK_HOUR)
    assert len(instance.jobs) == len(ROUTING_SHEET)
    for order, job in zip(ROUTING_SHEET, instance.jobs, strict=True):
        assert len(job) == len(order.steps)
        for step, operation in zip(order.steps, job, strict=True):
            assert operation.machine == MACHINE_INDEX[step.machine]
            assert operation.duration == step.hours
