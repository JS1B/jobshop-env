"""Seeded variants and the greedy baseline."""

import math
from pathlib import Path

import pytest

from jobshop import (
    JobShopEnv,
    bottleneck,
    lower_bound,
    most_work_remaining,
    optimal_makespan,
    tight,
    uniform,
    verify,
)
from jobshop.demo import main, success_table
from tests.test_verifier import tiny


def test_uniform_is_deterministic_and_uses_the_optimum() -> None:
    first = uniform(seed=1)
    assert first == uniform(seed=1)
    for job in first.jobs:
        assert sorted(op.machine for op in job) == [0, 1, 2]
    assert first.target_makespan == optimal_makespan(first)


def test_bottleneck_scales_machine_zero() -> None:
    plain = uniform(seed=2)
    slow = bottleneck(seed=2)
    for plain_job, slow_job in zip(plain.jobs, slow.jobs, strict=True):
        for plain_op, slow_op in zip(plain_job, slow_job, strict=True):
            assert plain_op.machine == slow_op.machine
            if plain_op.machine == 0:
                assert slow_op.duration == plain_op.duration * 5
            else:
                assert slow_op.duration == plain_op.duration
    assert slow.target_makespan == optimal_makespan(slow)


def test_tight_target_is_slack_times_the_bound() -> None:
    instance = tight(seed=0)
    assert instance.target_makespan == math.ceil(lower_bound(instance) * 1.05)


def test_lower_bound_and_optimum_on_the_fixture() -> None:
    instance = tiny()
    assert lower_bound(instance) == 5
    assert optimal_makespan(instance) == 5


def test_baseline_solves_the_fixture() -> None:
    env = JobShopEnv(tiny())
    most_work_remaining(env)
    assert verify(env.state) == 1


def test_cli_writes_one_chart(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    main(["--variant", "uniform", "--seed", "0", "--out", str(tmp_path)])
    assert (tmp_path / "uniform-seed0.svg").is_file()
    assert "uniform seed 0:" in capsys.readouterr().out


def test_cli_rejects_a_variant_without_a_seed() -> None:
    with pytest.raises(SystemExit):
        main(["--variant", "tight"])


def test_success_table_covers_three_variants() -> None:
    rows = success_table(seeds=(0,))
    assert [name for name, _successes, _episodes in rows] == ["uniform", "bottleneck", "tight"]
    for _name, successes, episodes in rows:
        assert episodes == 1
        assert 0 <= successes <= episodes
