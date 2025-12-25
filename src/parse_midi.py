"""
MIDI Parser for Hooktheory/Hookpad MIDI files.

Extracts lead melody notes from MIDI files and converts them to an internal
NoteEvent representation with absolute timing.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import mido


@dataclass
class NoteEvent:
    """Represents a single note with absolute timing."""
    start_tick: int      # Absolute tick when note starts
    end_tick: int        # Absolute tick when note ends
    pitch: int           # MIDI pitch (0-127)
    velocity: int        # Note velocity (0-127)

    @property
    def duration_ticks(self) -> int:
        """Duration of the note in ticks."""
        return self.end_tick - self.start_tick


@dataclass
class MidiData:
    """Container for extracted MIDI data."""
    notes: list[NoteEvent]
    ticks_per_beat: int
    bpm: float
    track_name: str


def inspect_midi(midi_path: str) -> dict:
    """
    Inspect a MIDI file and return track information.

    Useful for debugging and understanding Hookpad MIDI structure.

    Args:
        midi_path: Path to the MIDI file.

    Returns:
        Dictionary with track names, message counts, and sample events.
    """
    mid = mido.MidiFile(midi_path)

    info = {
        "ticks_per_beat": mid.ticks_per_beat,
        "type": mid.type,
        "tracks": []
    }

    for i, track in enumerate(mid.tracks):
        track_info = {
            "index": i,
            "name": track.name or f"Track {i}",
            "message_count": len(track),
            "note_on_count": 0,
            "sample_notes": [],
            "has_tempo": False,
            "tempo_bpm": None,
        }

        abs_time = 0
        note_count = 0

        for msg in track:
            abs_time += msg.time

            if msg.type == "set_tempo":
                track_info["has_tempo"] = True
                track_info["tempo_bpm"] = round(mido.tempo2bpm(msg.tempo), 2)

            if msg.type == "note_on" and msg.velocity > 0:
                note_count += 1
                if len(track_info["sample_notes"]) < 10:
                    track_info["sample_notes"].append({
                        "time": abs_time,
                        "note": msg.note,
                        "velocity": msg.velocity
                    })

        track_info["note_on_count"] = note_count
        info["tracks"].append(track_info)

    return info


def find_lead_track(mid: mido.MidiFile, patterns: Optional[list[str]] = None) -> int:
    """
    Find the most likely lead melody track.

    Strategy:
    1. Look for tracks matching name patterns (lead, melody, vocal, etc.)
    2. Fall back to track with highest average pitch (likely melody)
    3. Fall back to first track with notes

    Args:
        mid: Loaded MIDI file.
        patterns: List of track name patterns to match (case-insensitive).

    Returns:
        Track index.
    """
    if patterns is None:
        patterns = ["lead", "melody", "vocal", "synth"]

    # Strategy 1: Match by name patterns
    for pattern in patterns:
        for i, track in enumerate(mid.tracks):
            if track.name and pattern.lower() in track.name.lower():
                # Verify it has notes
                has_notes = any(
                    msg.type == "note_on" and msg.velocity > 0
                    for msg in track
                )
                if has_notes:
                    return i

    # Strategy 2: Find track with highest average pitch (likely melody)
    best_track = -1
    best_avg_pitch = -1

    for i, track in enumerate(mid.tracks):
        pitches = [
            msg.note for msg in track
            if msg.type == "note_on" and msg.velocity > 0
        ]
        if pitches:
            avg_pitch = sum(pitches) / len(pitches)
            if avg_pitch > best_avg_pitch:
                best_avg_pitch = avg_pitch
                best_track = i

    if best_track >= 0:
        return best_track

    # Strategy 3: First track with any notes
    for i, track in enumerate(mid.tracks):
        has_notes = any(
            msg.type == "note_on" and msg.velocity > 0
            for msg in track
        )
        if has_notes:
            return i

    raise ValueError("No tracks with notes found in MIDI file")


def extract_tempo(mid: mido.MidiFile, default_bpm: float = 120.0) -> float:
    """
    Extract BPM from MIDI file.

    Args:
        mid: Loaded MIDI file.
        default_bpm: Default BPM if no tempo event found.

    Returns:
        BPM as float.
    """
    for track in mid.tracks:
        for msg in track:
            if msg.type == "set_tempo":
                return mido.tempo2bpm(msg.tempo)
    return default_bpm


def extract_lead_notes(
    midi_path: str,
    track_index: Optional[int] = None,
    lead_patterns: Optional[list[str]] = None,
    default_bpm: float = 120.0
) -> MidiData:
    """
    Extract lead melody notes from a MIDI file.

    Converts delta times to absolute ticks and merges note_on/note_off
    events into NoteEvent instances.

    Args:
        midi_path: Path to the MIDI file.
        track_index: Specific track index to use, or None to auto-detect.
        lead_patterns: Name patterns for lead track detection.
        default_bpm: Default BPM if no tempo event found.

    Returns:
        MidiData containing notes, timing info, and metadata.
    """
    mid = mido.MidiFile(midi_path)

    # Find lead track
    if track_index is None:
        track_index = find_lead_track(mid, lead_patterns)

    track = mid.tracks[track_index]
    track_name = track.name or f"Track {track_index}"

    # Extract tempo
    bpm = extract_tempo(mid, default_bpm)

    # Convert to absolute time and collect note events
    # Track active notes: pitch -> (start_tick, velocity)
    active_notes: dict[int, tuple[int, int]] = {}
    notes: list[NoteEvent] = []
    abs_time = 0

    for msg in track:
        abs_time += msg.time

        if msg.type == "note_on" and msg.velocity > 0:
            # Note starts
            active_notes[msg.note] = (abs_time, msg.velocity)

        elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
            # Note ends
            if msg.note in active_notes:
                start_tick, velocity = active_notes.pop(msg.note)
                notes.append(NoteEvent(
                    start_tick=start_tick,
                    end_tick=abs_time,
                    pitch=msg.note,
                    velocity=velocity
                ))

    # Handle any notes that never got a note_off (extend to end)
    for pitch, (start_tick, velocity) in active_notes.items():
        notes.append(NoteEvent(
            start_tick=start_tick,
            end_tick=abs_time,
            pitch=pitch,
            velocity=velocity
        ))

    # Sort by start time, then by pitch for consistent ordering
    notes.sort(key=lambda n: (n.start_tick, n.pitch))

    return MidiData(
        notes=notes,
        ticks_per_beat=mid.ticks_per_beat,
        bpm=bpm,
        track_name=track_name
    )


def print_midi_info(midi_path: str) -> None:
    """Print detailed MIDI file information for debugging."""
    info = inspect_midi(midi_path)

    print(f"\n{'='*60}")
    print(f"MIDI File: {midi_path}")
    print(f"{'='*60}")
    print(f"Ticks per beat (PPQ): {info['ticks_per_beat']}")
    print(f"Type: {info['type']}")
    print(f"\nTracks ({len(info['tracks'])}):")
    print("-" * 60)

    for track in info["tracks"]:
        print(f"\n[{track['index']}] {track['name']}")
        print(f"    Messages: {track['message_count']}, Notes: {track['note_on_count']}")
        if track["has_tempo"]:
            print(f"    Tempo: {track['tempo_bpm']} BPM")
        if track["sample_notes"]:
            print(f"    Sample notes (first {len(track['sample_notes'])}):")
            for note in track["sample_notes"]:
                print(f"      tick={note['time']:6d}  note={note['note']:3d}  vel={note['velocity']:3d}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.parse_midi <midi_file>")
        print("  Prints track information and sample notes from a MIDI file.")
        sys.exit(1)

    midi_file = sys.argv[1]
    if not Path(midi_file).exists():
        print(f"Error: File not found: {midi_file}")
        sys.exit(1)

    print_midi_info(midi_file)

    # Also extract and show lead notes
    print(f"\n{'='*60}")
    print("Lead Track Extraction:")
    print("="*60)

    try:
        data = extract_lead_notes(midi_file)
        print(f"Selected track: {data.track_name}")
        print(f"BPM: {data.bpm}")
        print(f"Ticks per beat: {data.ticks_per_beat}")
        print(f"Total notes extracted: {len(data.notes)}")

        if data.notes:
            print(f"\nFirst 10 notes:")
            for i, note in enumerate(data.notes[:10]):
                print(f"  {i+1:2d}. tick={note.start_tick:6d}-{note.end_tick:6d}  "
                      f"pitch={note.pitch:3d}  vel={note.velocity:3d}  "
                      f"dur={note.duration_ticks:5d}")
    except Exception as e:
        print(f"Error extracting lead notes: {e}")
