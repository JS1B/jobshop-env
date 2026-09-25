"""One planning week at a fictional contract shop.

Hartwig Zerspanung GmbH is not a real company. The orders, the standard
hours, and the Friday truck are invented. A routing sheet becomes an
``Instance``, three planners act through ``JobShopEnv.step``, and the
verifier decides whether the plan can ship.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from jobshop.baseline import most_work_remaining
from jobshop.env import Action, Instance, JobShopEnv, Operation, naive_reward
from jobshop.verifier import verify
from jobshop.view import write_gantt

# Index is the machine id the environment stores. Names are the sheet's words.
MACHINE_INDEX = {
    "5-axis mill": 0,
    "CNC lathe": 1,
    "deburr and inspection": 2,
}

# One 8-hour shift a day, Monday through Friday, counted from Monday 06:00.
# Hour 40 is the end of Friday's shift, when the truck leaves. The hours
# below were chosen so that 40 is also the exact optimum: only an optimal
# plan with no overlap makes the truck.
TRUCK_HOUR = 40


@dataclass(frozen=True)
class RouteStep:
    """One line of a routing sheet: a machine name and standard hours."""

    machine: str
    hours: int


@dataclass(frozen=True)
class Order:
    """One customer order: a name, a customer, and a fixed routing."""

    name: str
    customer: str
    steps: tuple[RouteStep, ...]


# Nine operations, so ``optimal_makespan`` applies. Mill hours are the longest.
# The flange is a turned part; the housing and the bracket are milled first.
ROUTING_SHEET: tuple[Order, ...] = (
    Order(
        "pump flange",
        "Rhein Hydraulik",
        (
            RouteStep("CNC lathe", 8),
            RouteStep("5-axis mill", 16),
            RouteStep("deburr and inspection", 2),
        ),
    ),
    Order(
        "gearbox housing",
        "Alb Getriebe",
        (
            RouteStep("5-axis mill", 12),
            RouteStep("CNC lathe", 4),
            RouteStep("deburr and inspection", 2),
        ),
    ),
    Order(
        "sensor bracket",
        "Neckar Sensorik",
        (
            RouteStep("5-axis mill", 10),
            RouteStep("CNC lathe", 6),
            RouteStep("deburr and inspection", 2),
        ),
    ),
)

# Housing and bracket both take the 5-axis mill at hour 0. The lathe and
# inspection are single-booked, and the schedule finishes at hour 30.
# ``step`` accepts the mill overlap. The verifier does not.
_SHORTCUT: tuple[Action, ...] = (
    Action(0, 0),
    Action(1, 0),
    Action(2, 0),
    Action(2, 10),
    Action(0, 12),
    Action(2, 16),
    Action(1, 16),
    Action(1, 20),
    Action(0, 28),
)


def instance_from_sheet(orders: Sequence[Order], deadline_hour: int) -> Instance:
    """Turn routing-sheet names and hours into an ``Instance``.

    Machine names map through ``MACHINE_INDEX``. ``deadline_hour`` becomes
    ``target_makespan``.
    """
    jobs: list[tuple[Operation, ...]] = []
    for order in orders:
        steps: list[Operation] = []
        for step in order.steps:
            try:
                machine = MACHINE_INDEX[step.machine]
            except KeyError:
                raise ValueError(f"unknown machine {step.machine!r}") from None
            steps.append(Operation(machine, step.hours))
        jobs.append(tuple(steps))
    return Instance(tuple(jobs), deadline_hour)


def dispatch_rule(env: JobShopEnv) -> float:
    """Run ``most_work_remaining`` through ``step``. Returns the terminal reward."""
    most_work_remaining(env)
    return float(verify(env.state))


def senior_planner(env: JobShopEnv) -> float:
    """Play one earliest-start optimum through ``step``. Returns the terminal reward."""
    return _play(env, _optimal_actions(env.instance))


def shortcut_planner(env: JobShopEnv) -> float:
    """Play a complete log that double-books the 5-axis mill.

    Returns the terminal reward. The log is for ``ROUTING_SHEET`` only.
    """
    return _play(env, _SHORTCUT)


def main() -> None:
    """Print the three planners and write one Gantt chart each."""
    instance = instance_from_sheet(ROUTING_SHEET, TRUCK_HOUR)
    planners = (
        ("dispatch rule", "scenario-dispatch.svg", dispatch_rule),
        ("senior planner", "scenario-planner.svg", senior_planner),
        ("shortcut planner", "scenario-shortcut.svg", shortcut_planner),
    )
    print("Hartwig Zerspanung GmbH")
    print(f"Friday truck leaves at hour {TRUCK_HOUR}")
    print()
    paths: list[Path] = []
    for name, filename, planner in planners:
        env = JobShopEnv(instance)
        reward = planner(env)
        _print_planner(name, env, reward)
        print()
        path = Path("out") / filename
        write_gantt(path, env.state.instance, env.state.log)
        paths.append(path)
    for path in paths:
        print(path)


def _play(env: JobShopEnv, actions: Sequence[Action]) -> float:
    env.reset()
    reward = 0.0
    done = False
    for action in actions:
        _observation, reward, done, _info = env.step(action)
    if not done:
        raise RuntimeError("planner stopped before every operation was scheduled")
    return reward


def _optimal_actions(instance: Instance) -> tuple[Action, ...]:
    """One optimal log: earliest starts, first schedule that hits the best horizon.

    Same active-schedule enumeration as ``optimal_makespan``. Actions are
    emitted in start-time order so ``step`` accepts them. Ties at one start
    go to the lower job index.
    """
    jobs = instance.jobs
    n_ops = sum(len(job) for job in jobs)
    n_jobs = len(jobs)
    machine_ready = {op.machine: 0 for job in jobs for op in job}
    next_op = [0] * n_jobs
    job_ready = [0] * n_jobs
    best = sum(op.duration for job in jobs for op in job) + 1
    best_placed: list[tuple[int, int]] | None = None
    stack: list[tuple[int, int]] = []

    def search(placed: int, horizon: int) -> None:
        nonlocal best, best_placed
        if horizon >= best:
            return
        if placed == n_ops:
            best = horizon
            best_placed = list(stack)
            return
        for job in range(n_jobs):
            index = next_op[job]
            if index >= len(jobs[job]):
                continue
            operation = jobs[job][index]
            start = max(job_ready[job], machine_ready[operation.machine])
            end = start + operation.duration
            if end >= best:
                continue
            next_op[job] = index + 1
            previous_job = job_ready[job]
            previous_machine = machine_ready[operation.machine]
            job_ready[job] = end
            machine_ready[operation.machine] = end
            stack.append((start, job))
            search(placed + 1, max(horizon, end))
            stack.pop()
            next_op[job] = index
            job_ready[job] = previous_job
            machine_ready[operation.machine] = previous_machine

    search(0, 0)
    if best_placed is None:
        raise RuntimeError("no schedule")
    ordered = sorted(best_placed, key=lambda item: (item[0], item[1]))
    return tuple(Action(job, start) for start, job in ordered)


def _finish_hours(env: JobShopEnv) -> tuple[int, ...]:
    instance = env.state.instance
    next_op = [0] * len(instance.jobs)
    finish = [0] * len(instance.jobs)
    for action in env.state.log:
        operation = instance.jobs[action.job][next_op[action.job]]
        next_op[action.job] += 1
        finish[action.job] = action.start_time + operation.duration
    return tuple(finish)


def _print_planner(name: str, env: JobShopEnv, terminal_reward: float) -> None:
    finish_hours = _finish_hours(env)
    finish = max(finish_hours) if finish_hours else 0
    deadline = env.instance.target_makespan
    score = verify(env.state)
    ships = "yes" if score == 1 else "no"
    print(name)
    print(f"  finish hour: {finish}")
    print(f"  deadline hour: {deadline}")
    print(f"  ships: {ships}")
    print(f"  naive reward: {naive_reward(env.state):.1f}")
    print(f"  verifier score: {score}")
    print(f"  terminal reward: {terminal_reward:.1f}")
    for order, hour in zip(ROUTING_SHEET, finish_hours, strict=True):
        print(f"  {order.name}: hour {hour}")


if __name__ == "__main__":
    main()
