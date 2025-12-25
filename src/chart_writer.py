"""
Clone Hero .chart File Writer.

Generates valid Clone Hero .chart files from mapped note data.

.chart Format Reference:
- [Song]: Metadata (Name, Artist, Charter, Resolution)
- [SyncTrack]: Tempo and time signature events
- [Events]: Sections, lyrics, etc.
- [ExpertSingle]: Expert difficulty guitar notes

Note format in [ExpertSingle]:
  <tick> = N <lane> <sustain_length>

Where:
- tick: Position in chart ticks (resolution-based, typically 192 per quarter note)
- lane: 0-4 for Green-Orange, 5 for forcing strum, 6 for tap, 7 for open
- sustain_length: 0 for no sustain, or length in chart ticks
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.parse_midi import NoteEvent
from src.map_to_frets import MappedNote, QAIssue


CHART_RESOLUTION = 192  # Standard Clone Hero resolution (ticks per quarter note)


@dataclass
class ChartMetadata:
    """Metadata for the .chart file."""
    name: str = "Unknown"
    artist: str = "Unknown"
    charter: str = "Auto-Generated"
    album: str = ""
    year: str = ""
    offset: int = 0  # Audio offset in milliseconds
    resolution: int = CHART_RESOLUTION
    difficulty: int = 0  # Unused in .chart but sometimes present


def midi_ticks_to_chart_ticks(
    midi_ticks: int,
    midi_ppq: int,
    chart_resolution: int = CHART_RESOLUTION
) -> int:
    """
    Convert MIDI ticks to .chart ticks.

    Both MIDI and .chart use ticks per quarter note, so this is a simple
    scaling operation.

    Args:
        midi_ticks: Tick position in MIDI file.
        midi_ppq: MIDI ticks per quarter note (PPQ).
        chart_resolution: Chart ticks per quarter note (typically 192).

    Returns:
        Equivalent tick position in chart format.
    """
    # Scale: chart_tick = midi_tick * (chart_res / midi_ppq)
    return int(midi_ticks * chart_resolution / midi_ppq)


def format_song_section(metadata: ChartMetadata) -> str:
    """Generate the [Song] section of the .chart file."""
    lines = [
        "[Song]",
        "{",
        f'  Name = "{metadata.name}"',
        f'  Artist = "{metadata.artist}"',
        f'  Charter = "{metadata.charter}"',
    ]

    if metadata.album:
        lines.append(f'  Album = "{metadata.album}"')
    if metadata.year:
        lines.append(f'  Year = ", {metadata.year}"')

    lines.extend([
        f"  Offset = {metadata.offset}",
        f"  Resolution = {metadata.resolution}",
        '  Player2 = bass',
        "  Difficulty = 0",
        '  PreviewStart = 0',
        '  PreviewEnd = 0',
        '  Genre = "rock"',
        '  MediaType = "cd"',
        "}",
    ])

    return "\n".join(lines)


def format_sync_track(
    bpm: float,
    time_sig_numerator: int = 4,
    time_sig_denominator: int = 4
) -> str:
    """
    Generate the [SyncTrack] section.

    Args:
        bpm: Tempo in beats per minute.
        time_sig_numerator: Time signature numerator (beats per measure).
        time_sig_denominator: Time signature denominator (beat unit).

    Returns:
        Formatted [SyncTrack] section.
    """
    # BPM is stored as microseconds per beat * 1000 in some formats,
    # but .chart uses BPM * 1000 directly
    bpm_value = int(bpm * 1000)

    # Time signature: TS <numerator> <log2(denominator)>
    # e.g., 4/4 = TS 4 2 (since log2(4) = 2)
    import math
    ts_denom_exp = int(math.log2(time_sig_denominator)) if time_sig_denominator > 0 else 2

    lines = [
        "[SyncTrack]",
        "{",
        f"  0 = TS {time_sig_numerator} {ts_denom_exp}",
        f"  0 = B {bpm_value}",
        "}",
    ]

    return "\n".join(lines)


def format_events_section(
    mapped_notes: Optional[list[MappedNote]] = None,
    midi_ppq: int = 480,
    chart_resolution: int = CHART_RESOLUTION,
    include_qa_events: bool = True
) -> str:
    """
    Generate the [Events] section with optional QA markers.

    Args:
        mapped_notes: Optional list of mapped notes with QA issues.
        midi_ppq: MIDI ticks per quarter note.
        chart_resolution: Chart resolution.
        include_qa_events: Whether to add QA issue events.

    Returns:
        Formatted [Events] section.
    """
    lines = [
        "[Events]",
        "{",
        '  0 = E "section intro"',
    ]

    # Add QA events if mapped notes with issues are provided
    if include_qa_events and mapped_notes:
        for mn in mapped_notes:
            if mn.issues:
                chart_tick = midi_ticks_to_chart_ticks(
                    mn.note.start_tick, midi_ppq, chart_resolution
                )
                for issue in mn.issues:
                    lines.append(f'  {chart_tick} = E "{issue.value}"')

    lines.append("}")
    return "\n".join(lines)


def format_note_line(
    chart_tick: int,
    lane: int,
    sustain_length: int = 0
) -> str:
    """
    Format a single note line for the .chart file.

    Args:
        chart_tick: Position in chart ticks.
        lane: Lane 0-4 (Green to Orange).
        sustain_length: Sustain length in chart ticks (0 for no sustain).

    Returns:
        Formatted note line.
    """
    return f"  {chart_tick} = N {lane} {sustain_length}"


def format_notes_section(
    notes: list[NoteEvent],
    lanes: list[int],
    midi_ppq: int,
    chart_resolution: int = CHART_RESOLUTION,
    min_sustain_beats: float = 0.5,
    difficulty: str = "Expert"
) -> str:
    """
    Generate a difficulty notes section.

    Args:
        notes: List of NoteEvent objects.
        lanes: Corresponding lane assignments (0-4).
        midi_ppq: MIDI ticks per quarter note.
        chart_resolution: Chart resolution (typically 192).
        min_sustain_beats: Minimum note length (in beats) to create a sustain.
        difficulty: Difficulty name (Expert, Hard, Medium, Easy).

    Returns:
        Formatted notes section.
    """
    section_name = f"[{difficulty}Single]"
    min_sustain_ticks = int(min_sustain_beats * chart_resolution)

    lines = [section_name, "{"]

    for note, lane in zip(notes, lanes):
        chart_start = midi_ticks_to_chart_ticks(
            note.start_tick, midi_ppq, chart_resolution
        )
        chart_end = midi_ticks_to_chart_ticks(
            note.end_tick, midi_ppq, chart_resolution
        )

        duration = chart_end - chart_start

        # Only create sustain if note is long enough
        sustain = duration if duration >= min_sustain_ticks else 0

        lines.append(format_note_line(chart_start, lane, sustain))

    lines.append("}")

    return "\n".join(lines)


def write_chart(
    output_path: str,
    notes: list[NoteEvent],
    lanes: list[int],
    midi_ppq: int,
    bpm: float,
    metadata: Optional[ChartMetadata] = None,
    difficulties: Optional[list[str]] = None,
    mapped_notes: Optional[list[MappedNote]] = None,
    include_qa_events: bool = True
) -> None:
    """
    Write a complete .chart file.

    Args:
        output_path: Path to write the .chart file.
        notes: List of NoteEvent objects.
        lanes: Corresponding lane assignments (0-4).
        midi_ppq: MIDI ticks per quarter note.
        bpm: Song tempo in BPM.
        metadata: Chart metadata (optional, uses defaults if None).
        difficulties: List of difficulties to generate (default: Expert only).
        mapped_notes: Optional MappedNote list for QA events.
        include_qa_events: Whether to include QA issue markers.
    """
    if metadata is None:
        metadata = ChartMetadata()

    if difficulties is None:
        difficulties = ["Expert"]

    sections = [
        format_song_section(metadata),
        format_sync_track(bpm),
        format_events_section(
            mapped_notes, midi_ppq, metadata.resolution, include_qa_events
        ),
    ]

    # Generate each difficulty
    for difficulty in difficulties:
        sections.append(format_notes_section(
            notes, lanes, midi_ppq, metadata.resolution,
            difficulty=difficulty
        ))

    content = "\n".join(sections)

    # Ensure output directory exists
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Write with UTF-8 encoding
    output.write_text(content, encoding="utf-8")


def generate_chart_string(
    notes: list[NoteEvent],
    lanes: list[int],
    midi_ppq: int,
    bpm: float,
    metadata: Optional[ChartMetadata] = None,
    difficulties: Optional[list[str]] = None
) -> str:
    """
    Generate .chart content as a string (for testing/preview).

    Same parameters as write_chart but returns string instead of writing file.
    """
    if metadata is None:
        metadata = ChartMetadata()

    if difficulties is None:
        difficulties = ["Expert"]

    sections = [
        format_song_section(metadata),
        format_sync_track(bpm),
        format_events_section(),
    ]

    for difficulty in difficulties:
        sections.append(format_notes_section(
            notes, lanes, midi_ppq, metadata.resolution,
            difficulty=difficulty
        ))

    return "\n".join(sections)


if __name__ == "__main__":
    # Demo with synthetic data
    from src.parse_midi import NoteEvent

    print("Generating sample .chart file...")

    # Create some test notes
    test_notes = [
        NoteEvent(start_tick=0, end_tick=480, pitch=60, velocity=100),
        NoteEvent(start_tick=480, end_tick=960, pitch=62, velocity=100),
        NoteEvent(start_tick=960, end_tick=1440, pitch=64, velocity=100),
        NoteEvent(start_tick=1440, end_tick=1920, pitch=65, velocity=100),
        NoteEvent(start_tick=1920, end_tick=2400, pitch=67, velocity=100),
    ]

    test_lanes = [0, 1, 2, 2, 3]  # G, R, Y, Y, B

    metadata = ChartMetadata(
        name="Test Song",
        artist="Test Artist",
        charter="Clone Hero Converter"
    )

    content = generate_chart_string(
        notes=test_notes,
        lanes=test_lanes,
        midi_ppq=480,
        bpm=120.0,
        metadata=metadata
    )

    print("\nGenerated .chart content:")
    print("=" * 60)
    print(content)
    print("=" * 60)
