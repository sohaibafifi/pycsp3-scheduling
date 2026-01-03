"""
Visualization utilities for scheduling solutions.

This module provides visualization capabilities for constraint programming scheduling solutions

Requires matplotlib for rendering. Install with:
    pip install matplotlib

Basic usage:
    >>> from pycsp3_scheduling import visu
    >>> if visu.is_visu_enabled():
    ...     visu.timeline("My Schedule")
    ...     visu.panel("Machine 1")
    ...     visu.interval(0, 10, "Task A", color=0)
    ...     visu.interval(10, 25, "Task B", color=1)
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
class Timeline:
    """
    The main visualization figure.

    Attributes:
        title: Title for the figure.
        origin: Start of the time axis.
        horizon: End of the time axis (auto-computed if None).
        panels: List of panels to display.
    """

    title: str | None = None
    origin: int | float = 0
    horizon: int | float | None = None
    panels: list[Panel] = field(default_factory=list)


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
        >>> visu.interval(0, 10, "Task A")
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
        >>> visu.interval(0, 10, "Task A")
        >>> visu.panel("Machine 2")
        >>> visu.interval(5, 15, "Task B")
    """
    global _current_panel
    if _current_timeline is None:
        timeline()
    p = Panel(name=name)
    _current_timeline.panels.append(p)
    _current_panel = p


def interval(
    start: int | float,
    end: int | float,
    name: str | None = None,
    color: int | str | None = None,
    height: float = 0.8,
) -> None:
    """
    Add an interval to the current panel.

    Displays a colored rectangle representing a task or activity.

    Args:
        start: Start time of the interval.
        end: End time of the interval.
        name: Label to display on the interval.
        color: Color as integer index or color string.
               Integer indices are automatically mapped to palette colors.
        height: Height of the bar (0.0 to 1.0, default 0.8).

    Example:
        >>> visu.panel("Machine 1")
        >>> visu.interval(0, 10, "Task A", color=0)
        >>> visu.interval(10, 25, "Task B", color=1)
        >>> visu.interval(25, 30, "Task C", color="red")
    """
    if _current_panel is None:
        panel()

    # Apply naming function if set
    display_name = name
    if _naming_func is not None and name is not None:
        display_name = _naming_func(name)

    _current_panel.intervals.append(
        IntervalData(
            start=start,
            end=end,
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
        >>> visu.interval(0, 10, "Task A", color=0)
        >>> visu.transition(10, 12)  # Setup time
        >>> visu.interval(12, 25, "Task B", color=1)
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
        >>> visu.interval(0, 10, "task_1")  # Displays as "1"
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
        >>> visu.interval(0, 10, "Task A")
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


# =============================================================================
# HIGH-LEVEL CONVENIENCE FUNCTIONS
# =============================================================================


def show_interval(
    interval: IntervalVar,
    value: IntervalValue | dict | None = None,
    panel_name: str | None = None,
    color: int | str | None = None,
) -> None:
    """
    Display a single interval variable.

    If value is provided, uses the solved values. Otherwise, displays the bounds.

    Args:
        interval: The IntervalVar to display.
        value: Solved IntervalValue or dict with start/end keys.
        panel_name: Name for the panel (defaults to interval name).
        color: Color for the interval.

    Example:
        >>> task = IntervalVar(size=10, name="task")
        >>> # After solving:
        >>> vals = interval_value(task)
        >>> visu.show_interval(task, vals)
    """
    if panel_name is None:
        panel_name = interval.name or "Interval"

    if _current_panel is None or _current_panel.name != panel_name:
        panel(panel_name)

    if value is not None:
        # Use solved values
        if hasattr(value, "start"):
            start, end = value.start, value.end
        else:
            start, end = value["start"], value["end"]
    else:
        # Use bounds
        start = interval.start_min
        end = interval.start_min + interval.length_min

    interval_func = globals()["interval"]
    interval_func(start, end, interval.name, color=color)


def show_sequence(
    seq: SequenceVar,
    values: Sequence[IntervalValue | dict] | None = None,
    panel_name: str | None = None,
) -> None:
    """
    Display a sequence variable with its intervals.

    Args:
        seq: The SequenceVar to display.
        values: List of solved IntervalValue or dicts for each interval.
        panel_name: Name for the panel (defaults to sequence name).

    Example:
        >>> machine = SequenceVar(intervals=tasks, name="machine")
        >>> # After solving:
        >>> vals = [interval_value(t) for t in tasks]
        >>> visu.show_sequence(machine, vals)
    """
    if panel_name is None:
        panel_name = seq.name or "Sequence"

    panel(panel_name)

    intervals_data = []
    for i, intv in enumerate(seq.intervals):
        if values is not None and i < len(values):
            val = values[i]
            if val is None:
                continue  # Absent interval
            if hasattr(val, "start"):
                start, end = val.start, val.end
            else:
                start, end = val["start"], val["end"]
        else:
            start = intv.start_min
            end = intv.start_min + intv.length_min

        color = seq.types[i] if seq.types else i
        intervals_data.append((start, end, intv.name, color))

    # Sort by start time
    intervals_data.sort(key=lambda x: x[0])

    for start, end, name, color in intervals_data:
        interval(start, end, name, color=color)


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

    # Render each panel
    for i, p in enumerate(tl.panels):
        ax = axes[i]
        _render_panel(ax, p, tl.origin, horizon, i)

    # Set x-axis limits
    for ax in axes:
        ax.set_xlim(tl.origin, horizon)

    # Add x-axis label to bottom panel
    axes[-1].set_xlabel("Time")

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

        # Add label
        if intv.name:
            mid_x = (intv.start + intv.end) / 2
            # Determine text color based on background brightness
            text_color = "white" if _is_dark_color(color) else "black"
            ax.text(
                mid_x,
                y_center,
                intv.name,
                ha="center",
                va="center",
                fontsize=9,
                color=text_color,
                fontweight="bold",
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
