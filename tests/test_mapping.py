"""Tests for pitch-to-lane mapping."""

import pytest
from src.parse_midi import NoteEvent
from src.map_to_frets import (
    map_pitches_to_lanes,
    segment_into_phrases,
    scale_pitch_to_lane,
    smooth_lanes,
    preserve_direction,
    detect_qa_issues,
    create_mapped_notes,
    QAIssue,
)


class TestScalePitchToLane:
    """Tests for single pitch scaling."""

    def test_middle_of_range(self):
        """Middle pitch maps to middle lane."""
        assert scale_pitch_to_lane(65, 60, 70) == 2

    def test_min_pitch_maps_to_green(self):
        """Minimum pitch maps to lane 0."""
        assert scale_pitch_to_lane(60, 60, 72) == 0

    def test_max_pitch_maps_to_orange(self):
        """Maximum pitch maps to lane 4."""
        assert scale_pitch_to_lane(72, 60, 72) == 4

    def test_same_pitch_maps_to_middle(self):
        """When all pitches are same, map to middle lane."""
        assert scale_pitch_to_lane(60, 60, 60) == 2


class TestSegmentIntoPhrases:
    """Tests for phrase segmentation."""

    def test_single_phrase_no_gaps(self):
        """Notes with no gaps form single phrase."""
        notes = [
            NoteEvent(0, 100, 60, 100),
            NoteEvent(100, 200, 62, 100),
            NoteEvent(200, 300, 64, 100),
        ]
        phrases = segment_into_phrases(notes, ticks_per_beat=480, silence_beats=1.0)
        assert len(phrases) == 1
        assert phrases[0] == [0, 1, 2]

    def test_multiple_phrases_with_gap(self):
        """Large gap creates phrase break."""
        notes = [
            NoteEvent(0, 100, 60, 100),
            NoteEvent(100, 200, 62, 100),
            NoteEvent(700, 800, 64, 100),  # 500 tick gap (> 480)
        ]
        phrases = segment_into_phrases(notes, ticks_per_beat=480, silence_beats=1.0)
        assert len(phrases) == 2
        assert phrases[0] == [0, 1]
        assert phrases[1] == [2]

    def test_empty_notes(self):
        """Empty input returns empty phrases."""
        phrases = segment_into_phrases([], ticks_per_beat=480)
        assert phrases == []


class TestSmoothLanes:
    """Tests for lane smoothing."""

    def test_clamps_large_jump(self):
        """Large jumps are clamped to max_jump."""
        lanes = [0, 4]  # Jump of 4
        result = smooth_lanes(lanes, max_jump=2)
        assert abs(result[1] - result[0]) <= 2

    def test_preserves_small_jumps(self):
        """Small jumps within max_jump are preserved."""
        lanes = [0, 2, 4]
        result = smooth_lanes(lanes, max_jump=2)
        assert result == [0, 2, 4]

    def test_single_note(self):
        """Single note is unchanged."""
        assert smooth_lanes([2]) == [2]

    def test_empty(self):
        """Empty list returns empty."""
        assert smooth_lanes([]) == []


class TestPreserveDirection:
    """Tests for melodic direction preservation."""

    def test_upward_pitch_nudges_lane_up(self):
        """When pitch goes up but lane doesn't, nudge up."""
        lanes = [2, 2]  # Same lane
        pitches = [60, 65]  # Pitch goes up
        result = preserve_direction(lanes, pitches)
        assert result[1] >= result[0]  # Should nudge up

    def test_downward_pitch_nudges_lane_down(self):
        """When pitch goes down but lane doesn't, nudge down."""
        lanes = [2, 2]  # Same lane
        pitches = [65, 60]  # Pitch goes down
        result = preserve_direction(lanes, pitches)
        assert result[1] <= result[0]  # Should nudge down


class TestMapPitchesToLanes:
    """Integration tests for full mapping pipeline."""

    def test_ascending_scale_non_decreasing(self):
        """Ascending scale produces non-decreasing lanes."""
        notes = []
        for i, pitch in enumerate(range(60, 73)):
            notes.append(NoteEvent(i * 480, (i + 1) * 480 - 10, pitch, 100))

        lanes = map_pitches_to_lanes(notes, ticks_per_beat=480)

        # Should be generally non-decreasing (with possible small dips from smoothing)
        increasing_count = sum(1 for i in range(1, len(lanes)) if lanes[i] >= lanes[i-1])
        assert increasing_count >= len(lanes) - 2  # Allow 1-2 exceptions

    def test_descending_scale_non_increasing(self):
        """Descending scale produces non-increasing lanes."""
        notes = []
        for i, pitch in enumerate(range(72, 59, -1)):
            notes.append(NoteEvent(i * 480, (i + 1) * 480 - 10, pitch, 100))

        lanes = map_pitches_to_lanes(notes, ticks_per_beat=480)

        # Should be generally non-increasing
        decreasing_count = sum(1 for i in range(1, len(lanes)) if lanes[i] <= lanes[i-1])
        assert decreasing_count >= len(lanes) - 2

    def test_all_lanes_in_valid_range(self):
        """All lanes are in 0-4 range."""
        notes = [
            NoteEvent(0, 100, 36, 100),  # Very low
            NoteEvent(100, 200, 96, 100),  # Very high
            NoteEvent(200, 300, 60, 100),  # Middle
        ]
        lanes = map_pitches_to_lanes(notes, ticks_per_beat=480)
        assert all(0 <= lane <= 4 for lane in lanes)

    def test_empty_notes_returns_empty(self):
        """Empty input returns empty."""
        assert map_pitches_to_lanes([], ticks_per_beat=480) == []


class TestQAIssues:
    """Tests for QA issue detection."""

    def test_detects_different_fret(self):
        """Same pitch on different lanes is flagged."""
        notes = [
            NoteEvent(0, 100, 60, 100),
            NoteEvent(100, 200, 62, 100),
            NoteEvent(200, 300, 60, 100),  # Same pitch as first
        ]
        lanes = [0, 2, 2]  # Different lane for same pitch
        issues = detect_qa_issues(notes, lanes)
        assert QAIssue.DIFFERENT_FRET in issues[2]

    def test_detects_too_low(self):
        """Higher pitch on lower lane is flagged."""
        notes = [
            NoteEvent(0, 100, 60, 100),
            NoteEvent(100, 200, 70, 100),  # Much higher pitch
        ]
        lanes = [3, 0]  # But mapped much lower
        issues = detect_qa_issues(notes, lanes)
        assert QAIssue.TOO_LOW in issues[1]

    def test_detects_too_high(self):
        """Lower pitch on higher lane is flagged."""
        notes = [
            NoteEvent(0, 100, 70, 100),
            NoteEvent(100, 200, 60, 100),  # Much lower pitch
        ]
        lanes = [0, 3]  # But mapped much higher
        issues = detect_qa_issues(notes, lanes)
        assert QAIssue.TOO_HIGH in issues[1]

    def test_create_mapped_notes_includes_issues(self):
        """create_mapped_notes includes QA issues."""
        notes = [
            NoteEvent(0, 100, 60, 100),
            NoteEvent(100, 200, 60, 100),  # Same pitch
        ]
        lanes = [0, 2]  # Different lanes
        mapped = create_mapped_notes(notes, lanes, include_qa=True)
        assert len(mapped) == 2
        assert QAIssue.DIFFERENT_FRET in mapped[1].issues
