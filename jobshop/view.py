"""Gantt chart for a finished action log.

Reads the instance and the log only. One row per machine, time left to
right, color by job. Overlapping operations on a machine stack inside
that row so a double-booking stays visible.
"""

from pathlib import Path

from jobshop.env import Action, Instance

_COLORS = ("#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2", "#B279A2")
_SCALE = 48
_BAR_H = 22
_LANE_GAP = 4
_ROW_GAP = 10
_LABEL_W = 112
_PAD_X = 16
_TOP = 36
_AXIS_H = 32


def gantt_svg(instance: Instance, log: tuple[Action, ...]) -> str:
    """Return an SVG document for this schedule."""
    bars = _placements(instance, log)
    machines = sorted({op.machine for job in instance.jobs for op in job})
    finish = max((end for _job, _machine, _start, end in bars), default=0)
    axis_end = max(finish, 1)
    show_target = 0 < instance.target_makespan <= finish * 2
    if show_target:
        axis_end = max(axis_end, instance.target_makespan)

    by_machine: dict[int, list[tuple[int, int, int]]] = {machine: [] for machine in machines}
    for job, machine, start, end in bars:
        by_machine.setdefault(machine, []).append((start, end, job))
        if machine not in machines:
            machines.append(machine)
            machines.sort()

    lanes = {machine: _lanes(intervals) for machine, intervals in by_machine.items()}
    row_heights = {
        machine: max(1, len(lane_list)) * _BAR_H + max(0, len(lane_list) - 1) * _LANE_GAP
        for machine, lane_list in lanes.items()
    }
    width = _LABEL_W + _PAD_X + axis_end * _SCALE + _PAD_X
    body = sum(row_heights.get(machine, _BAR_H) + _ROW_GAP for machine in machines)
    height = _TOP + body + _AXIS_H + 28

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        f'<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{_PAD_X}" y="24" font-family="sans-serif" font-size="16" fill="#1f2328">'
        f'Schedule</text>',
    ]
    y = _TOP
    for machine in machines:
        row_h = row_heights.get(machine, _BAR_H)
        parts.append(
            f'<text x="{_LABEL_W - 8}" y="{y + row_h / 2 + 4}" text-anchor="end" '
            f'font-family="sans-serif" font-size="13" fill="#1f2328">machine {machine}</text>'
        )
        parts.append(
            f'<rect x="{_LABEL_W}" y="{y}" width="{axis_end * _SCALE}" height="{row_h}" '
            f'fill="#f6f8fa" stroke="#d0d7de"/>'
        )
        for lane_index, lane in enumerate(lanes.get(machine, ())):
            bar_y = y + lane_index * (_BAR_H + _LANE_GAP)
            for start, end, job in lane:
                color = _COLORS[job % len(_COLORS)]
                x = _LABEL_W + start * _SCALE
                w = max((end - start) * _SCALE, 1)
                parts.append(
                    f'<rect class="op" x="{x}" y="{bar_y}" width="{w}" height="{_BAR_H}" '
                    f'fill="{color}" fill-opacity="0.9"/>'
                )
                if w >= 40:
                    parts.append(
                        f'<text x="{x + 4}" y="{bar_y + 15}" font-family="sans-serif" font-size="12" '
                        f'fill="#ffffff">job {job}</text>'
                    )
        y += row_h + _ROW_GAP

    axis_y = y
    for t in range(axis_end + 1):
        x = _LABEL_W + t * _SCALE
        parts.append(f'<line x1="{x}" y1="{axis_y}" x2="{x}" y2="{axis_y + 6}" stroke="#1f2328"/>')
        parts.append(
            f'<text x="{x}" y="{axis_y + 20}" text-anchor="middle" font-family="sans-serif" '
            f'font-size="11" fill="#1f2328">{t}</text>'
        )
    if show_target:
        x = _LABEL_W + instance.target_makespan * _SCALE
        parts.append(
            f'<line x1="{x}" y1="{_TOP}" x2="{x}" y2="{axis_y}" stroke="#cf222e" '
            f'stroke-dasharray="4 3"/>'
        )
        parts.append(
            f'<text x="{x + 4}" y="{_TOP + 12}" font-family="sans-serif" font-size="11" '
            f'fill="#cf222e">target</text>'
        )
    elif instance.target_makespan > axis_end:
        parts.append(
            f'<text x="{_PAD_X}" y="{height - 10}" font-family="sans-serif" font-size="11" '
            f'fill="#656d76">target {instance.target_makespan} is beyond this chart</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def write_gantt(path: Path, instance: Instance, log: tuple[Action, ...]) -> None:
    """Write ``gantt_svg`` to ``path``, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(gantt_svg(instance, log), encoding="utf-8")


def _placements(instance: Instance, log: tuple[Action, ...]) -> list[tuple[int, int, int, int]]:
    next_op = [0] * len(instance.jobs)
    placed: list[tuple[int, int, int, int]] = []
    for action in log:
        if not 0 <= action.job < len(instance.jobs):
            continue
        if next_op[action.job] >= len(instance.jobs[action.job]):
            continue
        operation = instance.jobs[action.job][next_op[action.job]]
        next_op[action.job] += 1
        placed.append(
            (action.job, operation.machine, action.start_time, action.start_time + operation.duration)
        )
    return placed


def _lanes(
    intervals: list[tuple[int, int, int]],
) -> tuple[tuple[tuple[int, int, int], ...], ...]:
    lanes: list[list[tuple[int, int, int]]] = []
    lane_end: list[int] = []
    for start, end, job in sorted(intervals):
        for index, end_at in enumerate(lane_end):
            if start >= end_at:
                lanes[index].append((start, end, job))
                lane_end[index] = end
                break
        else:
            lanes.append([(start, end, job)])
            lane_end.append(end)
    return tuple(tuple(lane) for lane in lanes)
