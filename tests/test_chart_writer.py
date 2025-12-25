"""Tests for .chart file writer."""

import pytest
from src.parse_midi import NoteEvent
from src.chart_writer import (
    midi_ticks_to_chart_ticks,
    format_song_section,
    format_sync_track,
    format_notes_section,
    generate_chart_string,
    ChartMetadata,
    CHART_RESOLUTION,
)


class TestTickConversion:
    """Tests for MIDI to chart tick conversion."""

    def test_same_resolution(self):
        """Same PPQ and resolution returns same value."""
        assert midi_ticks_to_chart_ticks(192, 192, 192) == 192

    def test_doubles_when_ppq_half(self):
        """When MIDI PPQ is half chart resolution, ticks double."""
        assert midi_ticks_to_chart_ticks(100, 96, 192) == 200

    def test_halves_when_ppq_double(self):
        """When MIDI PPQ is double chart resolution, ticks halve."""
        assert midi_ticks_to_chart_ticks(200, 384, 192) == 100

    def test_common_hookpad_ppq(self):
        """Test with common Hookpad PPQ (480)."""
        # 480 MIDI ticks (1 beat) -> 192 chart ticks
        assert midi_ticks_to_chart_ticks(480, 480, 192) == 192
        # 960 MIDI ticks (2 beats) -> 384 chart ticks
        assert midi_ticks_to_chart_ticks(960, 480, 192) == 384


class TestSongSection:
    """Tests for [Song] section formatting."""

    def test_contains_required_fields(self):
        """Song section has all required fields."""
        metadata = ChartMetadata(
            name="Test Song",
            artist="Test Artist",
            charter="Tester",
        )
        output = format_song_section(metadata)

        assert "[Song]" in output
        assert 'Name = "Test Song"' in output
        assert 'Artist = "Test Artist"' in output
        assert 'Charter = "Tester"' in output
        assert "Resolution = 192" in output

    def test_escapes_properly(self):
        """Names with special chars are handled."""
        metadata = ChartMetadata(name='Song "With" Quotes')
        output = format_song_section(metadata)
        # Should contain the name (quotes in value are ok for basic .chart)
        assert 'Song "With" Quotes' in output


class TestSyncTrack:
    """Tests for [SyncTrack] section formatting."""

    def test_bpm_conversion(self):
        """BPM is correctly converted to .chart format."""
        output = format_sync_track(120.0)

        assert "[SyncTrack]" in output
        assert "0 = B 120000" in output  # 120 * 1000

    def test_time_signature(self):
        """Time signature is correctly formatted."""
        output = format_sync_track(120.0, time_sig_numerator=4, time_sig_denominator=4)
        assert "0 = TS 4 2" in output  # 4/4, log2(4) = 2

    def test_different_time_sig(self):
        """6/8 time signature is formatted correctly."""
        output = format_sync_track(120.0, time_sig_numerator=6, time_sig_denominator=8)
        assert "0 = TS 6 3" in output  # 6/8, log2(8) = 3


class TestNotesSection:
    """Tests for notes section formatting."""

    def test_basic_notes(self):
        """Basic notes are formatted correctly."""
        notes = [
            NoteEvent(0, 100, 60, 100),
            NoteEvent(480, 580, 62, 100),
        ]
        lanes = [0, 2]

        output = format_notes_section(notes, lanes, midi_ppq=480)

        assert "[ExpertSingle]" in output
        assert "0 = N 0" in output  # First note at tick 0, green
        assert "192 = N 2" in output  # Second note at tick 192 (480 * 192/480)

    def test_sustain_notes(self):
        """Long notes get sustain values."""
        notes = [
            NoteEvent(0, 960, 60, 100),  # 2 beats long
        ]
        lanes = [0]

        output = format_notes_section(notes, lanes, midi_ppq=480, min_sustain_beats=0.5)

        # Should have sustain (384 chart ticks for 2 beats)
        assert "0 = N 0 384" in output

    def test_different_difficulties(self):
        """Can generate different difficulty sections."""
        notes = [NoteEvent(0, 100, 60, 100)]
        lanes = [0]

        for diff in ["Expert", "Hard", "Medium", "Easy"]:
            output = format_notes_section(notes, lanes, midi_ppq=480, difficulty=diff)
            assert f"[{diff}Single]" in output


class TestGenerateChartString:
    """Integration tests for full chart generation."""

    def test_complete_chart_structure(self):
        """Generated chart has all required sections."""
        notes = [
            NoteEvent(0, 480, 60, 100),
            NoteEvent(480, 960, 62, 100),
            NoteEvent(960, 1440, 64, 100),
        ]
        lanes = [0, 1, 2]

        content = generate_chart_string(
            notes, lanes, midi_ppq=480, bpm=120.0
        )

        assert "[Song]" in content
        assert "[SyncTrack]" in content
        assert "[Events]" in content
        assert "[ExpertSingle]" in content

    def test_correct_number_of_notes(self):
        """Chart contains correct number of note lines."""
        notes = [
            NoteEvent(i * 480, (i + 1) * 480, 60 + i, 100)
            for i in range(5)
        ]
        lanes = [0, 1, 2, 3, 4]

        content = generate_chart_string(notes, lanes, midi_ppq=480, bpm=120.0)

        # Count "= N" occurrences (one per note)
        note_count = content.count("= N ")
        assert note_count == 5

    def test_metadata_in_output(self):
        """Custom metadata appears in output."""
        notes = [NoteEvent(0, 100, 60, 100)]
        lanes = [0]
        metadata = ChartMetadata(
            name="Custom Name",
            artist="Custom Artist",
            charter="Custom Charter",
        )

        content = generate_chart_string(
            notes, lanes, midi_ppq=480, bpm=140.0, metadata=metadata
        )

        assert 'Name = "Custom Name"' in content
        assert 'Artist = "Custom Artist"' in content
        assert 'Charter = "Custom Charter"' in content
        assert "0 = B 140000" in content  # BPM

    def test_empty_notes_generates_valid_chart(self):
        """Empty notes still generate valid chart structure."""
        content = generate_chart_string([], [], midi_ppq=480, bpm=120.0)

        assert "[Song]" in content
        assert "[SyncTrack]" in content
        assert "[ExpertSingle]" in content
        # But no note lines
        assert "= N " not in content
