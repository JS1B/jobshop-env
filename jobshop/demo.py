"""Print the greedy baseline's success rate, or run one episode."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from jobshop.baseline import most_work_remaining
from jobshop.env import Action, Instance, JobShopEnv, Operation
from jobshop.generate import bottleneck, tight, uniform
from jobshop.verifier import verify
from jobshop.view import write_gantt

_GENERATORS = (uniform, bottleneck, tight)
_BY_NAME = {generate.__name__: generate for generate in _GENERATORS}


def success_table(seeds: Sequence[int] = range(10)) -> list[tuple[str, int, int]]:
    """Return ``(variant, successes, episodes)`` for the greedy baseline."""
    rows: list[tuple[str, int, int]] = []
    for generate in _GENERATORS:
        successes = 0
        for seed in seeds:
            env = JobShopEnv(generate(seed=seed))
            most_work_remaining(env)
            if verify(env.state) == 1:
                successes += 1
        rows.append((generate.__name__, successes, len(seeds)))
    return rows


def write_charts(directory: Path = Path("out")) -> tuple[Path, Path]:
    """Write a greedy uniform chart and the double-booked chart."""
    env = JobShopEnv(uniform(seed=0))
    greedy = most_work_remaining(env)
    greedy_path = directory / "greedy-uniform.svg"
    write_gantt(greedy_path, env.state.instance, tuple(greedy))

    clash = Instance(
        jobs=(
            (Operation(0, 3), Operation(1, 1)),
            (Operation(0, 3), Operation(1, 1)),
        ),
        target_makespan=100,
    )
    clash_log = (Action(0, 0), Action(1, 0), Action(0, 3), Action(1, 4))
    clash_path = directory / "double-booked.svg"
    write_gantt(clash_path, clash, clash_log)
    return greedy_path, clash_path


def run_episode(variant: str, seed: int, directory: Path = Path("out")) -> tuple[int, Path]:
    """Run the greedy rule on one instance and write its chart."""
    env = JobShopEnv(_BY_NAME[variant](seed=seed))
    log = most_work_remaining(env)
    score = verify(env.state)
    path = directory / f"{variant}-seed{seed}.svg"
    write_gantt(path, env.state.instance, tuple(log))
    return score, path


def main(argv: Sequence[str] | None = None) -> None:
    """Report the success table, or run one variant and seed."""
    parser = argparse.ArgumentParser(description="Run the job-shop greedy baseline.")
    parser.add_argument("--variant", choices=tuple(_BY_NAME))
    parser.add_argument("--seed", type=int)
    parser.add_argument("--out", type=Path, default=Path("out"))
    args = parser.parse_args(argv)
    if (args.variant is None) != (args.seed is None):
        parser.error("pass both --variant and --seed, or neither")
    if args.variant is None:
        print(f"{'variant':<12} {'success':>8}")
        for name, successes, episodes in success_table():
            print(f"{name:<12} {successes}/{episodes}")
        for path in write_charts(args.out):
            print(path)
        return
    score, path = run_episode(args.variant, args.seed, args.out)
    print(f"{args.variant} seed {args.seed}: {score}")
    print(path)


if __name__ == "__main__":
    main()
