"""
Visualization utilities for scheduling solutions.

This module provides visualization capabilities for constraint programming scheduling solutions

Requires matplotlib for rendering. Install with:
    pip install matplotlib

Basic usage:
    >>> from pycsp3_scheduling import visu, interval_value
    >>> from pycsp3_scheduling.interop import IntervalValue
    >>> if visu.is_visu_enabled():
    ...     visu.timeline("My Schedule")
    ...     visu.panel("Machine 1")
    ...     # Using IntervalValue directly
    ...     visu.interval(IntervalValue(start=0, length=10, name="Task A"), color=0)
    ...     # Or from solved intervals
    ...     val = interval_value(task)
    ...     visu.interval(val, color=1)
    ...     visu.show()

The visualization consists of:
- Timeline: The main figure containing panels
- Panel: A row in the timeline showing intervals, sequences, or functions
- Interval: A time-bounded task displayed as a colored rectangle
- Sequence: An ordered list of intervals with optional transitions
- Function: A step function (e.g., cumulative resource usage)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from pycsp3_scheduling.variables import IntervalVar, SequenceVar
    from pycsp3_scheduling.interop import IntervalValue

# Check if matplotlib is available
_MATPLOTLIB_AVAILABLE = False
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    _MATPLOTLIB_AVAILABLE = True
except ImportError:
    plt = None
    mpatches = None
    Axes = None
    Figure = None


# =============================================================================
# COLOR PALETTE
# =============================================================================

# Default color palette for intervals (similar to docplex)
# These are visually distinct colors suitable for Gantt charts
DEFAULT_COLORS = [
    "#4E79A7",  # Blue
    "#F28E2B",  # Orange
    "#E15759",  # Red
    "#76B7B2",  # Teal
    "#59A14F",  # Green
    "#EDC948",  # Yellow
    "#B07AA1",  # Purple
    "#FF9DA7",  # Pink
    "#9C755F",  # Brown
    "#BAB0AC",  # Gray
]

# Color mapping: integer index -> color string
_color_map: dict[int, str] = {}


def _get_color(color: int | str | None, default_index: int = 0) -> str:
    """
    Get a color string from a color specification.

    Args:
        color: Integer index, color name/hex string, or None for auto.
        default_index: Default index when color is None.

    Returns:
        A color string usable by matplotlib.
    """
    if color is None:
        color = default_index

    if isinstance(color, int):
        # Integer index: use palette with auto-allocation
        if color not in _color_map:
            palette_index = len(_color_map) % len(DEFAULT_COLORS)
            _color_map[color] = DEFAULT_COLORS[palette_index]
        return _color_map[color]

    # String color: use directly
    return str(color)


# =============================================================================
# GLOBAL STATE
# =============================================================================

# Current timeline and panel state
_current_timeline: Timeline | None = None
_current_panel: Panel | None = None
_naming_func: Callable[[str], str] | None = None


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class Segment:
    """
    A segment in a step function.

    Represents a constant value over a time interval [start, end).
    For sloped segments, use value_start and value_end (not yet implemented).

    Attributes:
        start: Start time (inclusive).
        end: End time (exclusive).
        value: The constant value in this segment.
        name: Optional label for the segment.
    """

    start: int | float
    end: int | float
    value: int | float
    name: str | None = None


@dataclass
class IntervalData:
    """
    Data for displaying an interval.

    Attributes:
        start: Start time.
        end: End time.
        name: Label for the interval.
        color: Color specification (index or string).
        height: Height of the bar (0.0 to 1.0).
    """

    start: int | float
    end: int | float
    name: str | None = None
    color: int | str | None = None
    height: float = 0.8


@dataclass
class TransitionData:
    """
    Data for displaying a transition between intervals.

    Attributes:
        start: Start time (end of previous interval).
        end: End time (start of next interval).
        name: Optional label.
        color: Color for the transition marker.
    """

    start: int | float
    end: int | float
    name: str | None = None
    color: int | str | None = None


@dataclass
class PauseData:
    """
    Data for displaying a pause/inactive period.

    Attributes:
        start: Start time.
        end: End time.
        name: Optional label.
    """

    start: int | float
    end: int | float
    name: str | None = None


@dataclass
class Panel:
    """
    A panel in the timeline displaying intervals, sequences, or functions.

    Attributes:
        name: Label for the panel (shown on y-axis).
        intervals: List of intervals to display.
        transitions: List of transitions between intervals.
        pauses: List of pause periods.
        segments: List of function segments.
        panel_type: Type of panel ('interval', 'sequence', 'function').
    """

    name: str | None = None
    intervals: list[IntervalData] = field(default_factory=list)
    transitions: list[TransitionData] = field(default_factory=list)
    pauses: list[PauseData] = field(default_factory=list)
    segments: list[Segment] = field(default_factory=list)
    panel_type: str = "interval"


@dataclass
class AnnotationData:
    """
    Data for annotations (vertical lines, horizontal lines, text).

    Attributes:
        kind: Type of annotation ('vline', 'hline', 'text').
        x: X coordinate (time).
        y: Y coordinate (for text and hline).
        value: Value for hline or text content.
        color: Color for the annotation.
        label: Optional label (for legend).
        style: Line style ('solid', 'dashed', 'dotted').
    """

    kind: str
    x: int | float | None = None
    y: int | float | None = None
    value: str | int | float | None = None
    color: str | None = None
    label: str | None = None
    style: str = "dashed"


@dataclass
class LegendItem:
    """
    Data for a legend entry.

    Attributes:
        label: Text label for the legend entry.
        color: Color for the legend marker.
    """

    label: str
    color: int | str


@dataclass
class Timeline:
    """
    The main visualization figure.

    Attributes:
        title: Title for the figure.
        origin: Start of the time axis.
        horizon: End of the time axis (auto-computed if None).
        panels: List of panels to display.
        legend_items: List of legend entries.
        annotations: List of global annotations.
    """

    title: str | None = None
    origin: int | float = 0
    horizon: int | float | None = None
    panels: list[Panel] = field(default_factory=list)
    legend_items: list[LegendItem] = field(default_factory=list)
    annotations: list[AnnotationData] = field(default_factory=list)


# =============================================================================
# PUBLIC API
# =============================================================================


def is_visu_enabled() -> bool:
    """
    Check if visualization is available.

    Returns True if matplotlib is installed and can be used.

    Returns:
        True if visualization is enabled, False otherwise.

    Example:
        >>> if visu.is_visu_enabled():
        ...     visu.timeline("Schedule")
        ...     visu.show()
    """
    return _MATPLOTLIB_AVAILABLE


def timeline(
    title: str | None = None,
    origin: int | float = 0,
    horizon: int | float | None = None,
) -> None:
    """
    Create a new timeline for visualization.

    This creates a new figure and sets it as the current timeline.
    Subsequent calls to panel(), interval(), etc. will add to this timeline.

    Args:
        title: Title for the figure.
        origin: Start of the time axis (default 0).
        horizon: End of the time axis (auto-computed from content if None).

    Example:
        >>> visu.timeline("Job Shop Schedule", origin=0, horizon=100)
        >>> visu.panel("Machine 1")
        >>> visu.interval(IntervalValue(start=0, length=10, name="Task A"))
    """
    global _current_timeline, _current_panel
    _current_timeline = Timeline(title=title, origin=origin, horizon=horizon)
    _current_panel = None


def panel(name: str | None = None) -> None:
    """
    Add a new panel to the current timeline.

    A panel is a row in the visualization that can contain intervals,
    sequences, or function segments. The panel type is automatically
    determined by the content added to it.

    Args:
        name: Label for the panel (displayed on the y-axis).

    Example:
        >>> visu.timeline("Schedule")
        >>> visu.panel("Machine 1")
        >>> visu.interval(IntervalValue(start=0, length=10, name="Task A"))
        >>> visu.panel("Machine 2")
        >>> visu.interval(IntervalValue(start=5, length=10, name="Task B"))
    """
    global _current_panel
    if _current_timeline is None:
        timeline()
    p = Panel(name=name)
    _current_timeline.panels.append(p)
    _current_panel = p


def interval(
    value: IntervalValue,
    color: int | str | None = None,
    height: float = 0.8,
) -> None:
    """
    Add an interval to the current panel.

    Displays a colored rectangle representing a task or activity.

    Args:
        value: An IntervalValue containing start, end, and optionally name.
        color: Color as integer index or color string.
               Integer indices are automatically mapped to palette colors.
        height: Height of the bar (0.0 to 1.0, default 0.8).

    Example:
        >>> visu.panel("Machine 1")
        >>> value = IntervalValue(start=0, length=10, name="Task A")
        >>> visu.interval(value, color=0)
        >>> # Or from a solved interval:
        >>> val = interval_value(task)
        >>> visu.interval(val, color=1)
    """
    if _current_panel is None:
        panel()

    # Apply naming function if set
    display_name = value.name
    if _naming_func is not None and value.name is not None:
        display_name = _naming_func(value.name)

    _current_panel.intervals.append(
        IntervalData(
            start=value.start,
            end=value.end,
            name=display_name,
            color=color,
            height=height,
        )
    )
    _current_panel.panel_type = "interval"


def transition(
    start: int | float,
    end: int | float,
    name: str | None = None,
    color: int | str | None = None,
) -> None:
    """
    Add a transition marker between intervals.

    Transitions represent setup times or changeover periods between tasks.

    Args:
        start: Start time (typically end of previous interval).
        end: End time (typically start of next interval).
        name: Optional label.
        color: Color for the transition marker.

    Example:
        >>> visu.panel("Machine")
        >>> visu.interval(IntervalValue(start=0, length=10, name="Task A"), color=0)
        >>> visu.transition(10, 12)  # Setup time
        >>> visu.interval(IntervalValue(start=12, length=13, name="Task B"), color=1)
    """
    if _current_panel is None:
        panel()

    _current_panel.transitions.append(
        TransitionData(start=start, end=end, name=name, color=color)
    )
    _current_panel.panel_type = "sequence"


def pause(
    start: int | float,
    end: int | float,
    name: str | None = None,
) -> None:
    """
    Add a pause/inactive period to the current panel.

    Pauses are displayed as hatched regions indicating unavailable time.

    Args:
        start: Start time of the pause.
        end: End time of the pause.
        name: Optional label.

    Example:
        >>> visu.panel("Machine")
        >>> visu.pause(50, 60, "Maintenance")
    """
    if _current_panel is None:
        panel()

    _current_panel.pauses.append(PauseData(start=start, end=end, name=name))


def segment(
    start: int | float,
    end: int | float,
    value: int | float,
    name: str | None = None,
) -> None:
    """
    Add a segment to the current panel's function.

    Segments define step functions for displaying cumulative resource usage
    or other time-varying quantities.

    Args:
        start: Start time of the segment.
        end: End time of the segment.
        value: Value during this segment.
        name: Optional label.

    Example:
        >>> visu.panel("Resource Usage")
        >>> visu.segment(0, 10, 2)   # Usage is 2 from t=0 to t=10
        >>> visu.segment(10, 15, 4)  # Usage is 4 from t=10 to t=15
        >>> visu.segment(15, 30, 1)  # Usage is 1 from t=15 to t=30
    """
    if _current_panel is None:
        panel()

    _current_panel.segments.append(
        Segment(start=start, end=end, value=value, name=name)
    )
    _current_panel.panel_type = "function"


def function(
    segments: Sequence[Segment | tuple[int | float, int | float, int | float]],
    name: str | None = None,
    color: int | str | None = None,
    style: str = "area",
) -> None:
    """
    Add a complete function to the current panel.

    This is a convenience method for adding multiple segments at once.

    Args:
        segments: List of Segment objects or (start, end, value) tuples.
        name: Optional name for the function.
        color: Color for the function area/line.
        style: Display style - 'area' (filled), 'line', or 'step'.

    Example:
        >>> visu.panel("Cumulative")
        >>> visu.function([
        ...     (0, 10, 2),
        ...     (10, 15, 4),
        ...     (15, 30, 1),
        ... ], name="Usage", style="area")
    """
    if _current_panel is None:
        panel()

    for seg in segments:
        if isinstance(seg, Segment):
            _current_panel.segments.append(seg)
        else:
            start, end, value = seg
            _current_panel.segments.append(Segment(start=start, end=end, value=value))

    _current_panel.panel_type = "function"


def sequence(
    intervals: Sequence[IntervalData | tuple],
    name: str | None = None,
    transitions: Sequence[TransitionData | tuple] | None = None,
) -> None:
    """
    Add a sequence of intervals to the current panel.

    This is a convenience method for displaying ordered intervals
    (e.g., tasks on a machine in execution order).

    Args:
        intervals: List of IntervalData or (start, end, name, color) tuples.
        name: Name for the sequence (used as panel name if not set).
        transitions: Optional list of transitions between intervals.

    Example:
        >>> visu.panel("Machine")
        >>> visu.sequence([
        ...     (0, 10, "Task A", 0),
        ...     (12, 25, "Task B", 1),
        ...     (25, 35, "Task C", 2),
        ... ])
    """
    if _current_panel is None:
        panel(name)
    elif name is not None and _current_panel.name is None:
        _current_panel.name = name

    for intv in intervals:
        if isinstance(intv, IntervalData):
            _current_panel.intervals.append(intv)
        else:
            # Assume tuple: (start, end, name?, color?)
            start, end = intv[0], intv[1]
            intv_name = intv[2] if len(intv) > 2 else None
            intv_color = intv[3] if len(intv) > 3 else None
            _current_panel.intervals.append(
                IntervalData(start=start, end=end, name=intv_name, color=intv_color)
            )

    if transitions:
        for trans in transitions:
            if isinstance(trans, TransitionData):
                _current_panel.transitions.append(trans)
            else:
                start, end = trans[0], trans[1]
                trans_name = trans[2] if len(trans) > 2 else None
                _current_panel.transitions.append(
                    TransitionData(start=start, end=end, name=trans_name)
                )

    _current_panel.panel_type = "sequence"


def naming(func: Callable[[str], str] | None) -> None:
    """
    Set a naming function for interval labels.

    The function is applied to all interval names before display.
    Pass None to disable custom naming.

    Args:
        func: A function that takes a name string and returns a formatted string,
              or None to disable.

    Example:
        >>> # Show only task numbers
        >>> visu.naming(lambda n: n.split("_")[-1])
        >>> visu.interval(IntervalValue(start=0, length=10, name="task_1"))  # Displays as "1"
    """
    global _naming_func
    _naming_func = func


def show(block: bool = True) -> None:
    """
    Render and display the current timeline.

    This creates the matplotlib figure and displays it.

    Args:
        block: If True, block execution until the figure is closed.

    Example:
        >>> visu.timeline("Schedule")
        >>> visu.panel("Machine 1")
        >>> visu.interval(IntervalValue(start=0, length=10, name="Task A"))
        >>> visu.show()
    """
    if not _MATPLOTLIB_AVAILABLE:
        print("Visualization not available: matplotlib is not installed.")
        print("Install with: pip install matplotlib")
        return

    if _current_timeline is None:
        print("No timeline to display. Call timeline() first.")
        return

    _render_timeline(_current_timeline)
    plt.show(block=block)


def savefig(
    filename: str,
    dpi: int = 150,
    bbox_inches: str = "tight",
    transparent: bool = False,
) -> None:
    """
    Save the current timeline to a file.

    Renders the timeline and saves it to the specified file.
    The format is determined by the file extension (png, pdf, svg, etc.).

    Args:
        filename: Output filename with extension (e.g., "schedule.png").
        dpi: Resolution in dots per inch (default 150).
        bbox_inches: Bounding box setting, "tight" removes extra whitespace.
        transparent: If True, save with transparent background.

    Example:
        >>> visu.timeline("Schedule")
        >>> visu.panel("Machine 1")
        >>> visu.interval(IntervalValue(start=0, length=10, name="Task A"))
        >>> visu.savefig("schedule.png")
        >>> visu.savefig("schedule.pdf", dpi=300)
    """
    if not _MATPLOTLIB_AVAILABLE:
        print("Visualization not available: matplotlib is not installed.")
        print("Install with: pip install matplotlib")
        return

    if _current_timeline is None:
        print("No timeline to save. Call timeline() first.")
        return

    fig = _render_timeline(_current_timeline)
    fig.savefig(filename, dpi=dpi, bbox_inches=bbox_inches, transparent=transparent)
    print(f"Saved visualization to: {filename}")


def close() -> None:
    """
    Close the current figure and reset state.

    Example:
        >>> visu.show(block=False)
        >>> # ... do other things ...
        >>> visu.close()
    """
    global _current_timeline, _current_panel
    if _MATPLOTLIB_AVAILABLE:
        plt.close()
    _current_timeline = None
    _current_panel = None


def legend(label: str, color: int | str) -> None:
    """
    Add an entry to the legend.

    The legend is displayed when show() or savefig() is called.

    Args:
        label: Text label for the legend entry.
        color: Color as integer index or color string.

    Example:
        >>> visu.timeline("Schedule")
        >>> visu.legend("Task Type A", 0)
        >>> visu.legend("Task Type B", 1)
        >>> visu.legend("Maintenance", "gray")
        >>> visu.show()
    """
    if _current_timeline is None:
        timeline()

    _current_timeline.legend_items.append(LegendItem(label=label, color=color))


def vline(
    x: int | float,
    color: str = "red",
    style: str = "dashed",
    label: str | None = None,
) -> None:
    """
    Add a vertical line annotation at a specific time.

    The line spans all panels from top to bottom.

    Args:
        x: Time position for the vertical line.
        color: Color for the line (default "red").
        style: Line style - 'solid', 'dashed', or 'dotted' (default "dashed").
        label: Optional label to display above the line.

    Example:
        >>> visu.timeline("Schedule", horizon=100)
        >>> visu.vline(50, color="red", label="Deadline")
        >>> visu.vline(25, color="green", style="dotted", label="Milestone")
    """
    if _current_timeline is None:
        timeline()

    _current_timeline.annotations.append(
        AnnotationData(kind="vline", x=x, color=color, style=style, label=label)
    )


def hline(
    y: int | float,
    color: str = "red",
    style: str = "dashed",
    label: str | None = None,
    panel_name: str | None = None,
) -> None:
    """
    Add a horizontal line annotation at a specific value.

    Useful for showing capacity limits on function panels.

    Args:
        y: Y-axis value for the horizontal line.
        color: Color for the line (default "red").
        style: Line style - 'solid', 'dashed', or 'dotted' (default "dashed").
        label: Optional label to display at the line.
        panel_name: Panel to add the line to (current panel if None).

    Example:
        >>> visu.panel("Resource Usage")
        >>> visu.segment(0, 10, 3)
        >>> visu.hline(5, color="red", label="Capacity")
    """
    if _current_panel is None:
        panel()

    # Store in current panel's annotations (we'll add this to Panel)
    _current_timeline.annotations.append(
        AnnotationData(
            kind="hline",
            y=y,
            color=color,
            style=style,
            label=label,
            value=panel_name or _current_panel.name,
        )
    )


def annotate(
    x: int | float,
    text: str,
    y: float = 0.95,
    color: str = "black",
    fontsize: int = 9,
) -> None:
    """
    Add a text annotation at a specific time position.

    Args:
        x: Time position for the annotation.
        text: Text content to display.
        y: Vertical position (0.0 to 1.0, default 0.95 = near top).
        color: Text color (default "black").
        fontsize: Font size (default 9).

    Example:
        >>> visu.timeline("Schedule")
        >>> visu.annotate(50, "Important event", color="red")
    """
    if _current_timeline is None:
        timeline()

    _current_timeline.annotations.append(
        AnnotationData(kind="text", x=x, y=y, value=text, color=color)
    )


# =============================================================================
# HIGH-LEVEL CONVENIENCE FUNCTIONS
# =============================================================================


def show_interval(
    iv: IntervalVar,
    value: IntervalValue | None = None,
    panel_name: str | None = None,
    color: int | str | None = None,
) -> None:
    """
    Display a single interval variable.

    If value is provided, uses the solved values. Otherwise, displays the bounds.

    Args:
        iv: The IntervalVar to display.
        value: Solved IntervalValue from interval_value().
        panel_name: Name for the panel (defaults to interval name).
        color: Color for the interval.

    Example:
        >>> task = IntervalVar(size=10, name="task")
        >>> # After solving:
        >>> vals = interval_value(task)
        >>> visu.show_interval(task, vals)
    """
    from pycsp3_scheduling.interop import IntervalValue as IV

    if panel_name is None:
        panel_name = iv.name or "Interval"

    if _current_panel is None or _current_panel.name != panel_name:
        panel(panel_name)

    if value is not None:
        # Use solved values
        interval(value, color=color)
    else:
        # Use bounds - create IntervalValue from bounds
        iv_bounds = IV(
            start=iv.start_min,
            length=iv.length_min,
            name=iv.name,
        )
        interval(iv_bounds, color=color)


def show_sequence(
    seq: SequenceVar,
    values: Sequence[IntervalValue] | None = None,
    panel_name: str | None = None,
) -> None:
    """
    Display a sequence variable with its intervals.

    Args:
        seq: The SequenceVar to display.
        values: List of solved IntervalValue for each interval.
        panel_name: Name for the panel (defaults to sequence name).

    Example:
        >>> machine = SequenceVar(intervals=tasks, name="machine")
        >>> # After solving:
        >>> vals = [interval_value(t) for t in tasks]
        >>> visu.show_sequence(machine, vals)
    """
    from pycsp3_scheduling.interop import IntervalValue as IV

    if panel_name is None:
        panel_name = seq.name or "Sequence"

    panel(panel_name)

    intervals_data: list[tuple[IntervalValue, int | str]] = []
    for i, intv in enumerate(seq.intervals):
        if values is not None and i < len(values):
            val = values[i]
            if val is None:
                continue  # Absent interval
            iv = val
        else:
            # Use bounds
            iv = IV(start=intv.start_min, length=intv.length_min, name=intv.name)

        color = seq.types[i] if seq.types else i
        intervals_data.append((iv, color))

    # Sort by start time
    intervals_data.sort(key=lambda x: x[0].start)

    for iv, color in intervals_data:
        interval(iv, color=color)


# =============================================================================
# RENDERING
# =============================================================================


def _render_timeline(tl: Timeline) -> Figure:
    """Render a timeline to a matplotlib figure."""
    if not _MATPLOTLIB_AVAILABLE:
        raise RuntimeError("matplotlib is required for visualization")

    # Compute horizon if not set
    horizon = tl.horizon
    if horizon is None:
        horizon = tl.origin
        for p in tl.panels:
            for intv in p.intervals:
                horizon = max(horizon, intv.end)
            for seg in p.segments:
                horizon = max(horizon, seg.end)
            for pause_data in p.pauses:
                horizon = max(horizon, pause_data.end)
        horizon = max(horizon, tl.origin + 10)  # Minimum width

    num_panels = len(tl.panels)
    if num_panels == 0:
        num_panels = 1

    # Create figure with subplots for each panel
    fig_height = max(2, 1.5 * num_panels)
    fig, axes = plt.subplots(
        num_panels, 1, figsize=(12, fig_height), squeeze=False, sharex=True
    )
    axes = axes.flatten()

    # Add title
    if tl.title:
        fig.suptitle(tl.title, fontsize=14, fontweight="bold")

    # Build panel name to axes mapping
    panel_axes = {}
    for i, p in enumerate(tl.panels):
        if p.name:
            panel_axes[p.name] = axes[i]

    # Render each panel
    for i, p in enumerate(tl.panels):
        ax = axes[i]
        _render_panel(ax, p, tl.origin, horizon, i)

    # Render global annotations
    linestyle_map = {"solid": "-", "dashed": "--", "dotted": ":"}
    for ann in tl.annotations:
        if ann.kind == "vline":
            # Draw vertical line on all panels
            ls = linestyle_map.get(ann.style, "--")
            for ax in axes:
                ax.axvline(ann.x, color=ann.color, linestyle=ls, linewidth=1.5, alpha=0.8)
            # Add label on top panel
            if ann.label:
                axes[0].text(
                    ann.x, 1.02, ann.label,
                    transform=axes[0].get_xaxis_transform(),
                    ha="center", va="bottom", fontsize=8, color=ann.color
                )
        elif ann.kind == "hline":
            # Draw horizontal line on specified panel
            target_ax = panel_axes.get(ann.value, axes[-1])
            ls = linestyle_map.get(ann.style, "--")
            target_ax.axhline(ann.y, color=ann.color, linestyle=ls, linewidth=1.5, alpha=0.8)
            if ann.label:
                target_ax.text(
                    horizon, ann.y, f" {ann.label}",
                    ha="left", va="center", fontsize=8, color=ann.color
                )
        elif ann.kind == "text":
            # Draw text annotation on top panel
            axes[0].text(
                ann.x, ann.y, str(ann.value),
                transform=axes[0].get_xaxis_transform(),
                ha="center", va="top", fontsize=9, color=ann.color
            )

    # Set x-axis limits
    for ax in axes:
        ax.set_xlim(tl.origin, horizon)

    # Add x-axis label to bottom panel
    axes[-1].set_xlabel("Time")

    # Add legend if items exist
    if tl.legend_items:
        handles = []
        for item in tl.legend_items:
            color = _get_color(item.color, 0)
            patch = mpatches.Patch(color=color, label=item.label)
            handles.append(patch)
        fig.legend(
            handles=handles,
            loc="upper right",
            bbox_to_anchor=(0.99, 0.99),
            fontsize=9,
            framealpha=0.9,
        )

    plt.tight_layout()
    return fig


def _render_panel(
    ax: Axes,
    panel: Panel,
    origin: int | float,
    horizon: int | float,
    panel_index: int,
) -> None:
    """Render a single panel."""
    if panel.panel_type == "function":
        _render_function_panel(ax, panel, origin, horizon)
    else:
        _render_interval_panel(ax, panel, panel_index)

    # Set panel name as y-label
    if panel.name:
        ax.set_ylabel(panel.name, fontsize=10)

    # Remove y-ticks for interval panels
    if panel.panel_type != "function":
        ax.set_yticks([])

    # Add grid
    ax.grid(axis="x", linestyle="--", alpha=0.3)


def _render_interval_panel(ax: Axes, panel: Panel, panel_index: int) -> None:
    """Render an interval/sequence panel."""
    ax.set_ylim(0, 1)

    # Render pauses first (background)
    for pause_data in panel.pauses:
        ax.axvspan(
            pause_data.start,
            pause_data.end,
            facecolor="gray",
            alpha=0.2,
            hatch="//",
            edgecolor="gray",
        )
        if pause_data.name:
            mid = (pause_data.start + pause_data.end) / 2
            ax.text(mid, 0.9, pause_data.name, ha="center", va="top", fontsize=8, alpha=0.7)

    # Render transitions
    for trans in panel.transitions:
        color = _get_color(trans.color, panel_index)
        ax.axvspan(
            trans.start,
            trans.end,
            facecolor=color,
            alpha=0.3,
            hatch="\\\\",
        )

    # Render intervals
    for i, intv in enumerate(panel.intervals):
        color = _get_color(intv.color, i)
        y_center = 0.5
        y_bottom = y_center - intv.height / 2

        # Draw rectangle
        rect = mpatches.FancyBboxPatch(
            (intv.start, y_bottom),
            intv.end - intv.start,
            intv.height,
            boxstyle="round,pad=0.02,rounding_size=0.1",
            facecolor=color,
            edgecolor="black",
            linewidth=1,
        )
        ax.add_patch(rect)

        # Add label with overflow handling
        if intv.name:
            mid_x = (intv.start + intv.end) / 2
            interval_width = intv.end - intv.start
            # Determine text color based on background brightness
            text_color = "white" if _is_dark_color(color) else "black"

            # Estimate if text fits (rough heuristic: ~0.7 units per character at fontsize 9)
            # This uses data coordinates, so we need to check relative to interval width
            display_name = _fit_text_to_width(intv.name, interval_width)

            if display_name:
                ax.text(
                    mid_x,
                    y_center,
                    display_name,
                    ha="center",
                    va="center",
                    fontsize=9,
                    color=text_color,
                    fontweight="bold",
                    clip_on=True,
                )


def _render_function_panel(
    ax: Axes,
    panel: Panel,
    origin: int | float,
    horizon: int | float,
) -> None:
    """Render a function panel with step function."""
    if not panel.segments:
        ax.set_ylim(0, 1)
        return

    # Sort segments by start time
    segments = sorted(panel.segments, key=lambda s: s.start)

    # Build step function data
    times = [origin]
    values = [0]

    for seg in segments:
        # Add step up at start
        times.extend([seg.start, seg.start])
        values.extend([values[-1], seg.value])
        # Add step down at end
        times.extend([seg.end, seg.end])
        values.extend([seg.value, 0])

    times.append(horizon)
    values.append(0)

    # Draw filled area
    ax.fill_between(times, values, alpha=0.4, color=DEFAULT_COLORS[0], step="post")
    ax.step(times, values, where="post", color=DEFAULT_COLORS[0], linewidth=2)

    # Set y-axis limits with some padding
    max_value = max(seg.value for seg in segments) if segments else 1
    ax.set_ylim(0, max_value * 1.1)


def _fit_text_to_width(text: str, width: float, char_width: float = 0.8) -> str | None:
    """
    Fit text to a given width, truncating with ellipsis if needed.

    Args:
        text: The text to fit.
        width: Available width in data units.
        char_width: Estimated width per character in data units.

    Returns:
        The fitted text, possibly truncated with "...", or None if too small.
    """
    # Estimate how many characters fit
    max_chars = int(width / char_width)

    if max_chars < 1:
        # Too small to show anything
        return None
    elif max_chars < 3:
        # Very small: show first character only
        return text[0] if len(text) >= 1 else text
    elif len(text) <= max_chars:
        # Text fits completely
        return text
    else:
        # Truncate with ellipsis
        return text[: max_chars - 2] + ".."


def _is_dark_color(color: str) -> bool:
    """
    Determine if a color is dark (for choosing text color).

    Uses a simple luminance calculation.
    """
    import matplotlib.colors as mcolors

    try:
        rgb = mcolors.to_rgb(color)
        # Calculate relative luminance
        luminance = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
        return luminance < 0.5
    except (ValueError, KeyError):
        return False


# =============================================================================
# SUBPROCESS-SAFE VISUALIZATION
# =============================================================================


def savefig_safe(
    filename: str,
    visu_data: dict,
    title: str = "Schedule",
    horizon: int | float | None = None,
    legends: list[tuple[str, int | str]] | None = None,
    vlines: list[tuple[int | float, str, str, str | None]] | None = None,
) -> None:
    """
    Save visualization in a subprocess to avoid pycsp3 operator conflicts.

    This function runs matplotlib in a separate Python process, which
    avoids conflicts with pycsp3's operator monkey-patching.

    Args:
        filename: Output filename with extension (e.g., "schedule.png").
        visu_data: Dictionary with visualization data containing:
            - "panels": List of panel dicts with "name" and "intervals"
              where intervals are lists of (start, end, label, color)
        title: Title for the figure.
        horizon: End of the time axis (auto-computed if None).
        legends: Optional list of (label, color) tuples for the legend.
        vlines: Optional list of (x, color, style, label) tuples for vertical lines.

    Example:
        >>> # Extract data from solved model
        >>> visu_data = {
        ...     "panels": [
        ...         {"name": "Machine 1", "intervals": [(0, 10, "Task A", 0), (15, 25, "Task B", 1)]},
        ...         {"name": "Machine 2", "intervals": [(5, 20, "Task C", 2)]},
        ...     ]
        ... }
        >>> visu.savefig_safe("schedule.png", visu_data, title="Job Shop Schedule")
    """
    import subprocess
    import json

    # Build the visualization script
    visu_script = f'''
import json
import matplotlib
matplotlib.use('Agg')
from pycsp3_scheduling import visu

visu_data = {json.dumps(visu_data)}
title = {json.dumps(title)}
horizon = {json.dumps(horizon)}
legends = {json.dumps(legends)}
vlines = {json.dumps(vlines)}
filename = {json.dumps(filename)}

# Compute horizon if not provided
if horizon is None:
    horizon = 0
    for panel_data in visu_data.get("panels", []):
        for intv in panel_data.get("intervals", []):
            horizon = max(horizon, intv[1])
    horizon = max(horizon, 10) + 10

visu.reset()
visu.timeline(title, origin=0, horizon=horizon)

# Add legends
if legends:
    for label, color in legends:
        visu.legend(label, color)

# Add vertical lines
if vlines:
    for x, color, style, label in vlines:
        visu.vline(x, color=color, style=style, label=label)

# Add panels
from pycsp3_scheduling.interop import IntervalValue
for panel_data in visu_data.get("panels", []):
    visu.panel(panel_data.get("name"))
    for intv in panel_data.get("intervals", []):
        start, end = intv[0], intv[1]
        name = intv[2] if len(intv) > 2 else None
        color = intv[3] if len(intv) > 3 else None
        visu.interval(IntervalValue(start=start, length=end-start, name=name), color=color)

visu.savefig(filename)
'''
    result = subprocess.run(["python", "-c", visu_script], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Visualization error: {result.stderr}")
    else:
        if result.stdout:
            print(result.stdout, end="")


# =============================================================================
# CLEANUP
# =============================================================================


def reset() -> None:
    """
    Reset all visualization state.

    Clears the current timeline, panel, and color mappings.
    """
    global _current_timeline, _current_panel, _naming_func, _color_map
    _current_timeline = None
    _current_panel = None
    _naming_func = None
    _color_map = {}
