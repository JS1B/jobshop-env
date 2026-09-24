"""The Gantt chart is a pure function of the instance and the log."""

from jobshop import Action, Instance, Operation
from jobshop.view import gantt_svg
from tests.test_verifier import optimal_log, tiny


def test_optimal_chart_has_one_bar_per_operation() -> None:
    svg = gantt_svg(tiny(), optimal_log())
    assert svg.count('class="op"') == 4
    assert "target" in svg


def test_double_booking_stacks_on_one_machine() -> None:
    instance = Instance(
        jobs=(
            (Operation(0, 3), Operation(1, 1)),
            (Operation(0, 3), Operation(1, 1)),
        ),
        target_makespan=100,
    )
    log = (Action(0, 0), Action(1, 0), Action(0, 3), Action(1, 4))
    svg = gantt_svg(instance, log)
    assert svg.count('class="op"') == 4
    assert "target 100 is beyond this chart" in svg
