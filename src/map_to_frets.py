"""
Pitch-to-Fret Mapping for Clone Hero.

Maps MIDI pitches to 5 guitar lanes (0-4 = Green, Red, Yellow, Blue, Orange)
using phrase-based scaling with smoothing to create playable charts.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.parse_midi import NoteEvent


class QAIssue(Enum):
    """QA issue types for charting problems (inspired by midi-ch)."""
    TOO_LOW = "Bad_Too_Low"      # Higher pitch charted as lower fret
    TOO_HIGH = "Bad_Too_High"    # Lower pitch charted as higher fret
    DIFFERENT_FRET = "Bad_Different_Fret"  # Same pitch on different frets


@dataclass
class MappedNote:
    """A note with its assigned lane and optional QA issues."""
    note: NoteEvent
    lane: int  # 0-4 (Green to Orange)
    issues: list[QAIssue] = field(default_factory=list)


def segment_into_phrases(
    notes: list[NoteEvent],
    ticks_per_beat: int,
    silence_beats: float = 1.0
) -> list[list[int]]:
    """
    Segment notes into phrases based on gaps between notes.

    A phrase break occurs when the gap between the end of one note
    and the start of the next exceeds the silence threshold.

    Args:
        notes: List of NoteEvents (must be sorted by start_tick).
        ticks_per_beat: MIDI ticks per beat (PPQ).
        silence_beats: Silence threshold in beats to split phrases.

    Returns:
        List of phrases, where each phrase is a list of note indices.
    """
    if not notes:
        return []

    silence_ticks = int(silence_beats * ticks_per_beat)
    phrases: list[list[int]] = []
    current_phrase: list[int] = [0]

    for i in range(1, len(notes)):
        prev_end = notes[i - 1].end_tick
        curr_start = notes[i].start_tick
        gap = curr_start - prev_end

        if gap >= silence_ticks:
            # Start new phrase
            phrases.append(current_phrase)
            current_phrase = [i]
        else:
            current_phrase.append(i)

    # Don't forget the last phrase
    if current_phrase:
        phrases.append(current_phrase)

    return phrases


def scale_pitch_to_lane(pitch: int, min_pitch: int, max_pitch: int) -> int:
    """
    Scale a single pitch to a lane (0-4).

    Uses linear interpolation across the pitch range.

    Args:
        pitch: MIDI pitch to map.
        min_pitch: Minimum pitch in the phrase.
        max_pitch: Maximum pitch in the phrase.

    Returns:
        Lane index 0-4.
    """
    if max_pitch == min_pitch:
        # All same pitch, map to middle lane
        return 2

    # Linear scale to 0-4 range
    ratio = (pitch - min_pitch) / (max_pitch - min_pitch)
    lane = round(ratio * 4)
    return max(0, min(4, lane))


def smooth_lanes(
    lanes: list[int],
    max_jump: int = 2,
    passes: int = 1
) -> list[int]:
    """
    Smooth lane assignments to avoid jarring jumps.

    Two-pass smoothing:
    1. Clamp jumps: Limit consecutive lane changes to max_jump.
    2. Preserve direction: If pitch goes up but lane goes down, nudge up.

    Args:
        lanes: List of lane assignments (0-4).
        max_jump: Maximum allowed lane change between consecutive notes.
        passes: Number of smoothing passes.

    Returns:
        Smoothed lane assignments.
    """
    if len(lanes) <= 1:
        return lanes.copy()

    result = lanes.copy()

    for _ in range(passes):
        # Pass 1: Clamp jumps
        for i in range(1, len(result)):
            diff = result[i] - result[i - 1]
            if abs(diff) > max_jump:
                # Clamp to max_jump in the same direction
                if diff > 0:
                    result[i] = result[i - 1] + max_jump
                else:
                    result[i] = result[i - 1] - max_jump
                # Ensure still in valid range
                result[i] = max(0, min(4, result[i]))

    return result


def preserve_direction(
    lanes: list[int],
    pitches: list[int]
) -> list[int]:
    """
    Adjust lanes to better preserve melodic direction.

    If pitch goes up but lane stays same or goes down (or vice versa),
    nudge the lane to match the direction when possible.

    Args:
        lanes: Current lane assignments.
        pitches: Original MIDI pitches.

    Returns:
        Direction-adjusted lane assignments.
    """
    if len(lanes) <= 1:
        return lanes.copy()

    result = lanes.copy()

    for i in range(1, len(result)):
        pitch_diff = pitches[i] - pitches[i - 1]
        lane_diff = result[i] - result[i - 1]

        # Pitch goes up but lane doesn't
        if pitch_diff > 0 and lane_diff <= 0:
            if result[i] < 4:
                result[i] = min(4, result[i - 1] + 1)

        # Pitch goes down but lane doesn't
        elif pitch_diff < 0 and lane_diff >= 0:
            if result[i] > 0:
                result[i] = max(0, result[i - 1] - 1)

    return result


def map_pitches_to_lanes(
    notes: list[NoteEvent],
    ticks_per_beat: int,
    phrase_silence_beats: float = 1.0,
    max_lane_jump: int = 2,
    smoothing_passes: int = 1
) -> list[int]:
    """
    Map MIDI pitches to Clone Hero lanes (0-4).

    Algorithm:
    1. Segment notes into phrases based on silence gaps.
    2. For each phrase, find pitch range and scale linearly to 0-4.
    3. Apply smoothing to reduce jarring lane jumps.
    4. Preserve melodic direction where possible.

    Args:
        notes: List of NoteEvents to map.
        ticks_per_beat: MIDI ticks per beat (PPQ).
        phrase_silence_beats: Silence threshold for phrase detection.
        max_lane_jump: Maximum lane jump between consecutive notes.
        smoothing_passes: Number of smoothing iterations.

    Returns:
        List of lane assignments (0-4), same length as notes.
    """
    if not notes:
        return []

    # Segment into phrases
    phrases = segment_into_phrases(notes, ticks_per_beat, phrase_silence_beats)

    # Map each phrase independently
    lanes = [0] * len(notes)

    for phrase_indices in phrases:
        phrase_pitches = [notes[i].pitch for i in phrase_indices]
        min_pitch = min(phrase_pitches)
        max_pitch = max(phrase_pitches)

        # Scale each note in the phrase
        for idx in phrase_indices:
            lanes[idx] = scale_pitch_to_lane(
                notes[idx].pitch, min_pitch, max_pitch
            )

    # Extract pitches for direction preservation
    all_pitches = [n.pitch for n in notes]

    # Smooth the lanes
    lanes = smooth_lanes(lanes, max_lane_jump, smoothing_passes)

    # Preserve melodic direction
    lanes = preserve_direction(lanes, all_pitches)

    # Final clamp
    lanes = [max(0, min(4, lane)) for lane in lanes]

    return lanes


def detect_qa_issues(
    notes: list[NoteEvent],
    lanes: list[int]
) -> list[list[QAIssue]]:
    """
    Detect potential charting quality issues (inspired by midi-ch).

    Identifies:
    - TOO_LOW: Higher pitch charted to lower lane than previous
    - TOO_HIGH: Lower pitch charted to higher lane than previous
    - DIFFERENT_FRET: Same pitch mapped to different lanes in the song

    Args:
        notes: Original note events.
        lanes: Lane assignments.

    Returns:
        List of issue lists, one per note.
    """
    issues: list[list[QAIssue]] = [[] for _ in notes]

    # Track pitch -> lane mappings to detect inconsistencies
    pitch_to_lanes: dict[int, set[int]] = {}

    for i, (note, lane) in enumerate(zip(notes, lanes)):
        # Check for different fret mapping
        if note.pitch in pitch_to_lanes:
            if lane not in pitch_to_lanes[note.pitch]:
                issues[i].append(QAIssue.DIFFERENT_FRET)
            pitch_to_lanes[note.pitch].add(lane)
        else:
            pitch_to_lanes[note.pitch] = {lane}

        # Check pitch vs lane direction (compare to previous note)
        if i > 0:
            prev_pitch = notes[i - 1].pitch
            prev_lane = lanes[i - 1]

            pitch_diff = note.pitch - prev_pitch
            lane_diff = lane - prev_lane

            # Higher pitch but lower lane
            if pitch_diff > 2 and lane_diff < -1:
                issues[i].append(QAIssue.TOO_LOW)

            # Lower pitch but higher lane
            if pitch_diff < -2 and lane_diff > 1:
                issues[i].append(QAIssue.TOO_HIGH)

    return issues


def create_mapped_notes(
    notes: list[NoteEvent],
    lanes: list[int],
    include_qa: bool = True
) -> list[MappedNote]:
    """
    Combine notes with their lane assignments and QA issues.

    Args:
        notes: Original note events.
        lanes: Lane assignments (same length).
        include_qa: Whether to run QA issue detection.

    Returns:
        List of MappedNote objects.
    """
    if len(notes) != len(lanes):
        raise ValueError(f"Notes ({len(notes)}) and lanes ({len(lanes)}) must have same length")

    if include_qa:
        issues = detect_qa_issues(notes, lanes)
        return [MappedNote(note=n, lane=l, issues=iss)
                for n, l, iss in zip(notes, lanes, issues)]
    else:
        return [MappedNote(note=n, lane=l) for n, l in zip(notes, lanes)]


def summarize_qa_issues(mapped_notes: list[MappedNote]) -> dict[str, int]:
    """
    Summarize QA issues across all mapped notes.

    Returns:
        Dictionary of issue type -> count.
    """
    summary: dict[str, int] = {}
    for mn in mapped_notes:
        for issue in mn.issues:
            summary[issue.value] = summary.get(issue.value, 0) + 1
    return summary


def preview_lanes_ascii(
    notes: list[NoteEvent],
    lanes: list[int],
    ticks_per_beat: int,
    width: int = 80
) -> str:
    """
    Generate an ASCII preview of the lane mapping.

    Shows a timeline with lanes represented as rows.

    Args:
        notes: Note events.
        lanes: Lane assignments.
        ticks_per_beat: MIDI ticks per beat.
        width: Character width of the output.

    Returns:
        ASCII string representation.
    """
    if not notes:
        return "No notes to preview."

    lane_names = ["G", "R", "Y", "B", "O"]
    lines = {i: [] for i in range(5)}

    # Calculate time range
    start_tick = notes[0].start_tick
    end_tick = max(n.end_tick for n in notes)
    total_ticks = end_tick - start_tick

    if total_ticks == 0:
        total_ticks = 1

    # Map notes to positions
    for note, lane in zip(notes, lanes):
        pos = int((note.start_tick - start_tick) / total_ticks * (width - 10))
        lines[lane].append(pos)

    # Build output
    output = []
    output.append(f"\nLane Preview ({len(notes)} notes)")
    output.append("-" * (width - 5))

    for lane in range(4, -1, -1):  # Orange to Green (top to bottom)
        row = [" "] * (width - 5)
        for pos in lines[lane]:
            if 0 <= pos < len(row):
                row[pos] = "*"
        output.append(f"{lane_names[lane]}|{''.join(row)}|")

    output.append("-" * (width - 5))

    # Show beat markers
    beats = total_ticks / ticks_per_beat
    output.append(f"Duration: {beats:.1f} beats")

    return "\n".join(output)


if __name__ == "__main__":
    # Demo with synthetic data
    from src.parse_midi import NoteEvent

    print("Testing pitch-to-lane mapping with synthetic scale...")

    # Create an ascending scale (C4 to C5)
    test_notes = []
    for i, pitch in enumerate(range(60, 73)):  # C4 to C5
        test_notes.append(NoteEvent(
            start_tick=i * 480,
            end_tick=(i + 1) * 480 - 10,
            pitch=pitch,
            velocity=100
        ))

    ticks_per_beat = 480
    lanes = map_pitches_to_lanes(test_notes, ticks_per_beat)

    print("\nAscending scale C4-C5:")
    for note, lane in zip(test_notes, lanes):
        lane_name = ["Green", "Red", "Yellow", "Blue", "Orange"][lane]
        print(f"  Pitch {note.pitch:3d} -> Lane {lane} ({lane_name})")

    print(preview_lanes_ascii(test_notes, lanes, ticks_per_beat))

    # Test descending scale
    print("\n\nTesting with descending scale...")
    desc_notes = []
    for i, pitch in enumerate(range(72, 59, -1)):  # C5 down to C4
        desc_notes.append(NoteEvent(
            start_tick=i * 480,
            end_tick=(i + 1) * 480 - 10,
            pitch=pitch,
            velocity=100
        ))

    lanes = map_pitches_to_lanes(desc_notes, ticks_per_beat)

    print("\nDescending scale C5-C4:")
    for note, lane in zip(desc_notes, lanes):
        lane_name = ["Green", "Red", "Yellow", "Blue", "Orange"][lane]
        print(f"  Pitch {note.pitch:3d} -> Lane {lane} ({lane_name})")

    print(preview_lanes_ascii(desc_notes, lanes, ticks_per_beat))
