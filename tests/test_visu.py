"""Tests for the visualization module."""

import pytest

from pycsp3_scheduling import visu
from pycsp3_scheduling.variables import IntervalVar, SequenceVar, clear_interval_registry


@pytest.fixture(autouse=True)
def reset_visu():
    """Reset visualization state before each test."""
    visu.reset()
    clear_interval_registry()
    yield
    visu.reset()
    clear_interval_registry()


class TestVisuEnabled:
    """Tests for is_visu_enabled."""

    def test_is_visu_enabled_returns_bool(self):
        """is_visu_enabled returns a boolean."""
        result = visu.is_visu_enabled()
        assert isinstance(result, bool)


class TestTimeline:
    """Tests for timeline creation."""

    def test_timeline_creates_timeline(self):
        """timeline() creates a new timeline."""
        visu.timeline("Test Schedule")
        assert visu._current_timeline is not None
        assert visu._current_timeline.title == "Test Schedule"

    def test_timeline_with_origin_horizon(self):
        """timeline() accepts origin and horizon."""
        visu.timeline("Test", origin=10, horizon=100)
        assert visu._current_timeline.origin == 10
        assert visu._current_timeline.horizon == 100

    def test_timeline_resets_panel(self):
        """Creating a new timeline resets the current panel."""
        visu.timeline("First")
        visu.panel("Panel 1")
        assert visu._current_panel is not None
        visu.timeline("Second")
        assert visu._current_panel is None


class TestPanel:
    """Tests for panel creation."""

    def test_panel_creates_panel(self):
        """panel() creates a new panel."""
        visu.timeline("Test")
        visu.panel("Machine 1")
        assert visu._current_panel is not None
        assert visu._current_panel.name == "Machine 1"

    def test_panel_adds_to_timeline(self):
        """panel() adds the panel to the timeline."""
        visu.timeline("Test")
        visu.panel("Panel 1")
        visu.panel("Panel 2")
        assert len(visu._current_timeline.panels) == 2

    def test_panel_auto_creates_timeline(self):
        """panel() creates a timeline if none exists."""
        visu.panel("Panel 1")
        assert visu._current_timeline is not None


class TestInterval:
    """Tests for interval display."""

    def test_interval_adds_to_panel(self):
        """interval() adds interval data to the current panel."""
        from pycsp3_scheduling.interop import IntervalValue

        visu.timeline("Test")
        visu.panel("Machine")
        visu.interval(IntervalValue(start=0, length=10, name="Task A"), color=0)
        assert len(visu._current_panel.intervals) == 1
        intv = visu._current_panel.intervals[0]
        assert intv.start == 0
        assert intv.end == 10
        assert intv.name == "Task A"
        assert intv.color == 0

    def test_interval_auto_creates_panel(self):
        """interval() creates a panel if none exists."""
        from pycsp3_scheduling.interop import IntervalValue

        visu.timeline("Test")
        visu.interval(IntervalValue(start=0, length=10, name="Task"))
        assert visu._current_panel is not None
        assert len(visu._current_panel.intervals) == 1

    def test_multiple_intervals(self):
        """Multiple intervals can be added to a panel."""
        from pycsp3_scheduling.interop import IntervalValue

        visu.panel("Machine")
        visu.interval(IntervalValue(start=0, length=10, name="Task A"), color=0)
        visu.interval(IntervalValue(start=10, length=15, name="Task B"), color=1)
        visu.interval(IntervalValue(start=25, length=5, name="Task C"), color=2)
        assert len(visu._current_panel.intervals) == 3


class TestTransition:
    """Tests for transition display."""

    def test_transition_adds_to_panel(self):
        """transition() adds transition data to the current panel."""
        visu.panel("Machine")
        visu.transition(10, 12, "Setup")
        assert len(visu._current_panel.transitions) == 1
        trans = visu._current_panel.transitions[0]
        assert trans.start == 10
        assert trans.end == 12
        assert trans.name == "Setup"

    def test_transition_sets_panel_type(self):
        """transition() sets panel type to 'sequence'."""
        visu.panel("Machine")
        visu.transition(10, 12)
        assert visu._current_panel.panel_type == "sequence"


class TestPause:
    """Tests for pause display."""

    def test_pause_adds_to_panel(self):
        """pause() adds pause data to the current panel."""
        visu.panel("Machine")
        visu.pause(50, 60, "Maintenance")
        assert len(visu._current_panel.pauses) == 1
        p = visu._current_panel.pauses[0]
        assert p.start == 50
        assert p.end == 60
        assert p.name == "Maintenance"


class TestSegment:
    """Tests for function segment display."""

    def test_segment_adds_to_panel(self):
        """segment() adds segment data to the current panel."""
        visu.panel("Resource")
        visu.segment(0, 10, 2)
        assert len(visu._current_panel.segments) == 1
        seg = visu._current_panel.segments[0]
        assert seg.start == 0
        assert seg.end == 10
        assert seg.value == 2

    def test_segment_sets_panel_type(self):
        """segment() sets panel type to 'function'."""
        visu.panel("Resource")
        visu.segment(0, 10, 2)
        assert visu._current_panel.panel_type == "function"


class TestFunction:
    """Tests for function display."""

    def test_function_adds_segments(self):
        """function() adds multiple segments."""
        visu.panel("Resource")
        visu.function([
            (0, 10, 2),
            (10, 15, 4),
            (15, 30, 1),
        ])
        assert len(visu._current_panel.segments) == 3

    def test_function_accepts_segment_objects(self):
        """function() accepts Segment objects."""
        visu.panel("Resource")
        visu.function([
            visu.Segment(0, 10, 2),
            visu.Segment(10, 20, 3),
        ])
        assert len(visu._current_panel.segments) == 2


class TestSequence:
    """Tests for sequence display."""

    def test_sequence_adds_intervals(self):
        """sequence() adds multiple intervals."""
        visu.panel("Machine")
        visu.sequence([
            (0, 10, "Task A", 0),
            (12, 25, "Task B", 1),
        ])
        assert len(visu._current_panel.intervals) == 2

    def test_sequence_sets_panel_type(self):
        """sequence() sets panel type to 'sequence'."""
        visu.panel("Machine")
        visu.sequence([(0, 10, "Task", 0)])
        assert visu._current_panel.panel_type == "sequence"


class TestNaming:
    """Tests for naming function."""

    def test_naming_applies_to_intervals(self):
        """naming() applies transformation to interval names."""
        from pycsp3_scheduling.interop import IntervalValue

        visu.naming(lambda n: n.upper())
        visu.panel("Machine")
        visu.interval(IntervalValue(start=0, length=10, name="task"))
        assert visu._current_panel.intervals[0].name == "TASK"

    def test_naming_none_disables(self):
        """naming(None) disables transformation."""
        from pycsp3_scheduling.interop import IntervalValue

        visu.naming(lambda n: n.upper())
        visu.naming(None)
        visu.panel("Machine")
        visu.interval(IntervalValue(start=0, length=10, name="task"))
        assert visu._current_panel.intervals[0].name == "task"


class TestColors:
    """Tests for color handling."""

    def test_get_color_with_string(self):
        """_get_color returns string colors unchanged."""
        assert visu._get_color("red") == "red"
        assert visu._get_color("#FF0000") == "#FF0000"

    def test_get_color_with_int(self):
        """_get_color maps integer indices to palette colors."""
        color0 = visu._get_color(0)
        color1 = visu._get_color(1)
        assert color0 in visu.DEFAULT_COLORS
        assert color1 in visu.DEFAULT_COLORS
        assert color0 != color1

    def test_get_color_consistent(self):
        """_get_color returns consistent colors for same index."""
        visu.reset()  # Clear color map
        color_a = visu._get_color(5)
        color_b = visu._get_color(5)
        assert color_a == color_b


class TestShowInterval:
    """Tests for show_interval helper."""

    def test_show_interval_with_value(self):
        """show_interval displays interval with solved values."""
        from pycsp3_scheduling.interop import IntervalValue

        task = IntervalVar(size=10, name="task")
        value = IntervalValue(start=5, length=10, name="task")

        visu.timeline("Test")
        visu.show_interval(task, value)

        assert len(visu._current_panel.intervals) == 1
        intv = visu._current_panel.intervals[0]
        assert intv.start == 5
        assert intv.end == 15

    def test_show_interval_without_value(self):
        """show_interval displays interval with bounds when no value."""
        task = IntervalVar(start=(0, 10), size=5, name="task")

        visu.timeline("Test")
        visu.show_interval(task)

        assert len(visu._current_panel.intervals) == 1
        intv = visu._current_panel.intervals[0]
        assert intv.start == 0  # start_min
        assert intv.end == 5  # start_min + length_min


class TestShowSequence:
    """Tests for show_sequence helper."""

    def test_show_sequence_with_values(self):
        """show_sequence displays sequence with solved values."""
        from pycsp3_scheduling.interop import IntervalValue

        tasks = [
            IntervalVar(size=5, name="t1"),
            IntervalVar(size=5, name="t2"),
        ]
        seq = SequenceVar(intervals=tasks, name="machine")
        values = [
            IntervalValue(start=0, length=5, name="t1"),
            IntervalValue(start=10, length=5, name="t2"),
        ]

        visu.timeline("Test")
        visu.show_sequence(seq, values)

        # Intervals should be sorted by start time
        assert len(visu._current_panel.intervals) == 2


class TestReset:
    """Tests for reset functionality."""

    def test_reset_clears_state(self):
        """reset() clears all visualization state."""
        from pycsp3_scheduling.interop import IntervalValue

        visu.timeline("Test")
        visu.panel("Panel")
        visu.interval(IntervalValue(start=0, length=10, name="Task"))
        visu._get_color(0)  # Add to color map

        visu.reset()

        assert visu._current_timeline is None
        assert visu._current_panel is None
        assert visu._naming_func is None
        assert len(visu._color_map) == 0


class TestDataClasses:
    """Tests for data classes."""

    def test_segment_creation(self):
        """Segment can be created with required fields."""
        seg = visu.Segment(0, 10, 5)
        assert seg.start == 0
        assert seg.end == 10
        assert seg.value == 5
        assert seg.name is None

    def test_interval_data_creation(self):
        """IntervalData can be created with required fields."""
        intv = visu.IntervalData(0, 10, "Task", color=1)
        assert intv.start == 0
        assert intv.end == 10
        assert intv.name == "Task"
        assert intv.color == 1
        assert intv.height == 0.8  # default

    def test_panel_creation(self):
        """Panel can be created with defaults."""
        p = visu.Panel(name="Test")
        assert p.name == "Test"
        assert p.intervals == []
        assert p.panel_type == "interval"

    def test_timeline_creation(self):
        """Timeline can be created with defaults."""
        tl = visu.Timeline(title="Schedule")
        assert tl.title == "Schedule"
        assert tl.origin == 0
        assert tl.horizon is None
        assert tl.panels == []

    def test_annotation_data_creation(self):
        """AnnotationData can be created."""
        ann = visu.AnnotationData(kind="vline", x=50, color="red", label="Deadline")
        assert ann.kind == "vline"
        assert ann.x == 50
        assert ann.color == "red"
        assert ann.label == "Deadline"
        assert ann.style == "dashed"

    def test_legend_item_creation(self):
        """LegendItem can be created."""
        item = visu.LegendItem(label="Task A", color=0)
        assert item.label == "Task A"
        assert item.color == 0


class TestLegend:
    """Tests for legend functionality."""

    def test_legend_adds_item(self):
        """legend() adds item to timeline."""
        visu.reset()
        visu.timeline("Test")
        visu.legend("Task Type A", 0)
        visu.legend("Task Type B", 1)

        assert len(visu._current_timeline.legend_items) == 2
        assert visu._current_timeline.legend_items[0].label == "Task Type A"
        assert visu._current_timeline.legend_items[1].color == 1
        visu.reset()

    def test_legend_auto_creates_timeline(self):
        """legend() creates timeline if needed."""
        visu.reset()
        visu.legend("Test", "red")

        assert visu._current_timeline is not None
        assert len(visu._current_timeline.legend_items) == 1
        visu.reset()


class TestAnnotations:
    """Tests for annotation functionality."""

    def test_vline_adds_annotation(self):
        """vline() adds vertical line annotation."""
        visu.reset()
        visu.timeline("Test")
        visu.vline(50, color="red", label="Deadline")

        assert len(visu._current_timeline.annotations) == 1
        ann = visu._current_timeline.annotations[0]
        assert ann.kind == "vline"
        assert ann.x == 50
        assert ann.color == "red"
        assert ann.label == "Deadline"
        visu.reset()

    def test_hline_adds_annotation(self):
        """hline() adds horizontal line annotation."""
        visu.reset()
        visu.timeline("Test")
        visu.panel("Resource")
        visu.hline(5, color="blue", label="Capacity")

        assert len(visu._current_timeline.annotations) == 1
        ann = visu._current_timeline.annotations[0]
        assert ann.kind == "hline"
        assert ann.y == 5
        assert ann.color == "blue"
        visu.reset()

    def test_annotate_adds_text(self):
        """annotate() adds text annotation."""
        visu.reset()
        visu.timeline("Test")
        visu.annotate(25, "Important", color="green")

        assert len(visu._current_timeline.annotations) == 1
        ann = visu._current_timeline.annotations[0]
        assert ann.kind == "text"
        assert ann.x == 25
        assert ann.value == "Important"
        visu.reset()


class TestTextOverflow:
    """Tests for text overflow handling."""

    def test_fit_text_to_width_fits(self):
        """Text that fits is returned unchanged."""
        result = visu._fit_text_to_width("Task", 10.0)
        assert result == "Task"

    def test_fit_text_to_width_truncates(self):
        """Long text is truncated with ellipsis."""
        result = visu._fit_text_to_width("Very Long Task Name", 5.0, char_width=0.8)
        assert result is not None
        assert len(result) <= 6
        assert result.endswith("..")

    def test_fit_text_to_width_very_small(self):
        """Very small width shows first char or None."""
        result = visu._fit_text_to_width("Task", 1.5, char_width=0.8)
        assert result in ("T", "Ta", None) or (result and len(result) <= 2)

    def test_fit_text_to_width_too_small(self):
        """Width too small returns None."""
        result = visu._fit_text_to_width("Task", 0.5, char_width=0.8)
        assert result is None


class TestSaveFig:
    """Tests for savefig functionality."""

    def test_savefig_creates_file(self, tmp_path):
        """savefig() creates an image file."""
        from pycsp3_scheduling.interop import IntervalValue

        visu.reset()
        visu.timeline("Test")
        visu.panel("Machine")
        visu.interval(IntervalValue(start=0, length=10, name="Task"))

        output_file = tmp_path / "test.png"
        visu.savefig(str(output_file))

        assert output_file.exists()
        assert output_file.stat().st_size > 0
        visu.close()
        visu.reset()

    def test_savefig_without_timeline(self, capsys):
        """savefig() without timeline prints message."""
        visu.reset()
        visu.savefig("/tmp/test.png")

        captured = capsys.readouterr()
        assert "No timeline to save" in captured.out
        visu.reset()
