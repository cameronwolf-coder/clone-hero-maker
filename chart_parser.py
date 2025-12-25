"""
Enhanced Clone Hero Chart Parser
Supports full .chart format with all Moonscraper features.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum


class NoteType(Enum):
    """Note types in Clone Hero."""
    STANDARD = "N"
    STAR_POWER = "S"
    EVENT = "E"


class NoteFlag(Enum):
    """Note flags for advanced note types."""
    FORCED = 5      # Forced strum/HOPO (inverts natural state)
    TAP = 6         # Tap note (no strum required)
    OPEN = 7        # Open note (no fret)


class Difficulty(Enum):
    """Chart difficulty levels."""
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
    EXPERT = "Expert"


class Instrument(Enum):
    """Supported instruments."""
    GUITAR = "Single"
    BASS = "DoubleBass"
    RHYTHM = "DoubleRhythm"
    COOP = "DoubleGuitar"
    KEYS = "Keyboard"
    DRUMS = "Drums"
    GHL_GUITAR = "GHLGuitar"
    GHL_BASS = "GHLBass"


@dataclass
class Note:
    """Represents a single note in the chart."""
    tick: int
    fret: int  # 0-4 for 5-fret, 0-7 for GHL
    sustain: int = 0
    is_forced: bool = False  # Forced HOPO/strum
    is_tap: bool = False
    is_open: bool = False
    velocity: int = 100  # MIDI velocity

    def is_chord_with(self, other: 'Note') -> bool:
        """Check if this note is part of a chord with another note."""
        return self.tick == other.tick

    def is_hopo(self, previous_note: Optional['Note'], resolution: int) -> bool:
        """
        Determine if this note is naturally a HOPO.

        Args:
            previous_note: The previous note in the chart
            resolution: Ticks per quarter note

        Returns:
            True if naturally a HOPO, False otherwise
        """
        if not previous_note:
            return False

        # HOPOs are notes within 1/12th of a beat
        hopo_threshold = resolution // 12
        tick_diff = self.tick - previous_note.tick

        # Must be close enough and different fret
        if tick_diff <= hopo_threshold and self.fret != previous_note.fret:
            return True

        return False

    def get_final_hopo_state(self, previous_note: Optional['Note'], resolution: int) -> bool:
        """
        Get the final HOPO state considering forced flag.

        Args:
            previous_note: The previous note
            resolution: Ticks per quarter note

        Returns:
            True if this should be a HOPO in game
        """
        natural_hopo = self.is_hopo(previous_note, resolution)

        # Forced flag inverts the natural state
        if self.is_forced:
            return not natural_hopo

        return natural_hopo


@dataclass
class StarPowerPhrase:
    """Represents a star power phrase."""
    tick: int
    length: int


@dataclass
class BPMChange:
    """Represents a BPM change event."""
    tick: int
    bpm: float  # Actual BPM (not milliBPM)

    @property
    def milli_bpm(self) -> int:
        """Get BPM in milliBPM format (BPM * 1000)."""
        return int(self.bpm * 1000)


@dataclass
class TimeSignature:
    """Represents a time signature change."""
    tick: int
    numerator: int = 4
    denominator: int = 4  # Stored as power of 2 (2^denominator)


@dataclass
class Section:
    """Represents a practice section marker."""
    tick: int
    name: str


@dataclass
class Event:
    """Represents a chart event."""
    tick: int
    text: str


@dataclass
class Track:
    """Represents a single difficulty track."""
    notes: List[Note] = field(default_factory=list)
    star_power: List[StarPowerPhrase] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)

    def add_note(self, note: Note):
        """Add a note and maintain sorting."""
        self.notes.append(note)
        self.notes.sort(key=lambda n: (n.tick, n.fret))

    def get_notes_at_tick(self, tick: int) -> List[Note]:
        """Get all notes at a specific tick (chord detection)."""
        return [n for n in self.notes if n.tick == tick]

    def get_note_count(self) -> int:
        """Get total note count."""
        return len(self.notes)


@dataclass
class Chart:
    """Represents a complete chart file."""
    # Metadata
    name: str = "Untitled"
    artist: str = "Unknown Artist"
    album: str = ""
    genre: str = "rock"
    year: str = ""
    charter: str = ""
    offset: float = 0.0
    resolution: int = 192
    difficulty: int = -1
    preview_start: float = 0.0
    preview_end: float = 0.0

    # Sync track
    bpm_changes: List[BPMChange] = field(default_factory=list)
    time_signatures: List[TimeSignature] = field(default_factory=list)

    # Global events
    sections: List[Section] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)

    # Instrument tracks (difficulty -> track)
    guitar: Dict[Difficulty, Track] = field(default_factory=dict)
    bass: Dict[Difficulty, Track] = field(default_factory=dict)
    rhythm: Dict[Difficulty, Track] = field(default_factory=dict)
    keys: Dict[Difficulty, Track] = field(default_factory=dict)
    drums: Dict[Difficulty, Track] = field(default_factory=dict)
    ghl_guitar: Dict[Difficulty, Track] = field(default_factory=dict)
    ghl_bass: Dict[Difficulty, Track] = field(default_factory=dict)

    def get_track(self, instrument: Instrument, difficulty: Difficulty) -> Optional[Track]:
        """Get a specific track."""
        track_map = {
            Instrument.GUITAR: self.guitar,
            Instrument.BASS: self.bass,
            Instrument.RHYTHM: self.rhythm,
            Instrument.KEYS: self.keys,
            Instrument.DRUMS: self.drums,
            Instrument.GHL_GUITAR: self.ghl_guitar,
            Instrument.GHL_BASS: self.ghl_bass,
        }

        tracks = track_map.get(instrument, {})
        return tracks.get(difficulty)

    def set_track(self, instrument: Instrument, difficulty: Difficulty, track: Track):
        """Set a specific track."""
        track_map = {
            Instrument.GUITAR: self.guitar,
            Instrument.BASS: self.bass,
            Instrument.RHYTHM: self.rhythm,
            Instrument.KEYS: self.keys,
            Instrument.DRUMS: self.drums,
            Instrument.GHL_GUITAR: self.ghl_guitar,
            Instrument.GHL_BASS: self.ghl_bass,
        }

        if instrument in track_map:
            track_map[instrument][difficulty] = track

    def get_initial_bpm(self) -> float:
        """Get the initial BPM."""
        if self.bpm_changes:
            return self.bpm_changes[0].bpm
        return 120.0  # Default


class ChartParser:
    """Parser for .chart files."""

    @staticmethod
    def parse_file(file_path: str) -> Chart:
        """
        Parse a .chart file.

        Args:
            file_path: Path to the .chart file

        Returns:
            Parsed Chart object
        """
        chart = Chart()

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split into sections
        sections = ChartParser._split_sections(content)

        # Parse each section
        for section_name, section_content in sections.items():
            if section_name == "Song":
                ChartParser._parse_song_section(chart, section_content)
            elif section_name == "SyncTrack":
                ChartParser._parse_sync_track(chart, section_content)
            elif section_name == "Events":
                ChartParser._parse_events(chart, section_content)
            else:
                # Parse instrument tracks
                ChartParser._parse_track_section(chart, section_name, section_content)

        return chart

    @staticmethod
    def _split_sections(content: str) -> Dict[str, str]:
        """Split content into named sections."""
        sections = {}
        current_section = None
        current_content = []

        for line in content.split('\n'):
            line = line.strip()

            # Section header
            if line.startswith('[') and line.endswith(']'):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content)

                # Start new section
                current_section = line[1:-1]
                current_content = []

            # Section content (skip braces)
            elif line and line != '{' and line != '}':
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content)

        return sections

    @staticmethod
    def _parse_song_section(chart: Chart, content: str):
        """Parse [Song] section."""
        for line in content.split('\n'):
            line = line.strip()
            if '=' not in line:
                continue

            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"')

            if key == "Name":
                chart.name = value
            elif key == "Artist":
                chart.artist = value
            elif key == "Album":
                chart.album = value
            elif key == "Genre":
                chart.genre = value
            elif key == "Year":
                chart.year = value
            elif key == "Charter":
                chart.charter = value
            elif key == "Offset":
                chart.offset = float(value)
            elif key == "Resolution":
                chart.resolution = int(value)
            elif key == "Difficulty":
                chart.difficulty = int(value)
            elif key == "PreviewStart":
                chart.preview_start = float(value)
            elif key == "PreviewEnd":
                chart.preview_end = float(value)

    @staticmethod
    def _parse_sync_track(chart: Chart, content: str):
        """Parse [SyncTrack] section."""
        for line in content.split('\n'):
            line = line.strip()
            if '=' not in line:
                continue

            parts = line.split('=', 1)
            tick = int(parts[0].strip())
            event_data = parts[1].strip().split()

            event_type = event_data[0]

            if event_type == "B":
                # BPM change: tick = B milliBPM
                milli_bpm = int(event_data[1])
                bpm = milli_bpm / 1000.0
                chart.bpm_changes.append(BPMChange(tick, bpm))

            elif event_type == "TS":
                # Time signature: tick = TS numerator [denominator]
                numerator = int(event_data[1])
                denominator = int(event_data[2]) if len(event_data) > 2 else 2
                chart.time_signatures.append(TimeSignature(tick, numerator, denominator))

    @staticmethod
    def _parse_events(chart: Chart, content: str):
        """Parse [Events] section."""
        for line in content.split('\n'):
            line = line.strip()
            if '=' not in line:
                continue

            parts = line.split('=', 1)
            tick = int(parts[0].strip())
            event_data = parts[1].strip()

            if event_data.startswith('E "section'):
                # Section marker
                section_name = event_data.split('"')[1].replace('section ', '')
                chart.sections.append(Section(tick, section_name))
            else:
                # General event
                event_text = event_data.strip('E ').strip('"')
                chart.events.append(Event(tick, event_text))

    @staticmethod
    def _parse_track_section(chart: Chart, section_name: str, content: str):
        """Parse instrument track sections like [ExpertSingle]."""
        # Parse difficulty and instrument from section name
        difficulty_map = {
            "Easy": Difficulty.EASY,
            "Medium": Difficulty.MEDIUM,
            "Hard": Difficulty.HARD,
            "Expert": Difficulty.EXPERT,
        }

        instrument_map = {
            "Single": Instrument.GUITAR,
            "DoubleBass": Instrument.BASS,
            "DoubleRhythm": Instrument.RHYTHM,
            "DoubleGuitar": Instrument.COOP,
            "Keyboard": Instrument.KEYS,
            "Drums": Instrument.DRUMS,
            "GHLGuitar": Instrument.GHL_GUITAR,
            "GHLBass": Instrument.GHL_BASS,
        }

        # Extract difficulty and instrument
        difficulty = None
        instrument = None

        for diff_name, diff_enum in difficulty_map.items():
            if section_name.startswith(diff_name):
                difficulty = diff_enum
                instrument_name = section_name[len(diff_name):]
                instrument = instrument_map.get(instrument_name)
                break

        if not difficulty or not instrument:
            return  # Unknown track

        # Create track
        track = Track()

        # Parse notes and events
        note_buffer = {}  # tick -> {fret -> Note} for combining flags

        for line in content.split('\n'):
            line = line.strip()
            if '=' not in line:
                continue

            parts = line.split('=', 1)
            tick = int(parts[0].strip())
            event_data = parts[1].strip().split()

            event_type = event_data[0]

            if event_type == "N":
                # Note: tick = N fret sustain
                fret = int(event_data[1])
                sustain = int(event_data[2])

                # Check if this is a flag
                if fret == NoteFlag.FORCED.value:
                    # Mark existing note as forced
                    if tick in note_buffer:
                        for note in note_buffer[tick].values():
                            note.is_forced = True

                elif fret == NoteFlag.TAP.value:
                    # Mark existing note as tap
                    if tick in note_buffer:
                        for note in note_buffer[tick].values():
                            note.is_tap = True

                elif fret == NoteFlag.OPEN.value:
                    # Open note
                    note = Note(tick, fret, sustain, is_open=True)
                    if tick not in note_buffer:
                        note_buffer[tick] = {}
                    note_buffer[tick][fret] = note

                else:
                    # Regular note (0-4 for 5-fret)
                    note = Note(tick, fret, sustain)
                    if tick not in note_buffer:
                        note_buffer[tick] = {}
                    note_buffer[tick][fret] = note

            elif event_type == "S":
                # Star power: tick = S type length
                sp_type = int(event_data[1])
                length = int(event_data[2])
                if sp_type == 2:  # Star power phrase
                    track.star_power.append(StarPowerPhrase(tick, length))

            elif event_type == "E":
                # Local event
                event_text = ' '.join(event_data[1:]).strip('"')
                track.events.append(Event(tick, event_text))

        # Add all notes to track
        for tick_notes in note_buffer.values():
            for note in tick_notes.values():
                track.add_note(note)

        # Set track in chart
        chart.set_track(instrument, difficulty, track)

    @staticmethod
    def write_file(chart: Chart, file_path: str):
        """
        Write a Chart object to a .chart file.

        Args:
            chart: Chart object to write
            file_path: Output file path
        """
        lines = []

        # [Song] section
        lines.append("[Song]")
        lines.append("{")
        lines.append(f'  Name = "{chart.name}"')
        lines.append(f'  Artist = "{chart.artist}"')
        if chart.album:
            lines.append(f'  Album = "{chart.album}"')
        if chart.genre:
            lines.append(f'  Genre = "{chart.genre}"')
        if chart.year:
            lines.append(f'  Year = "{chart.year}"')
        if chart.charter:
            lines.append(f'  Charter = "{chart.charter}"')
        lines.append(f"  Offset = {chart.offset}")
        lines.append(f"  Resolution = {chart.resolution}")
        if chart.difficulty >= 0:
            lines.append(f"  Difficulty = {chart.difficulty}")
        if chart.preview_start > 0:
            lines.append(f"  PreviewStart = {chart.preview_start}")
        if chart.preview_end > 0:
            lines.append(f"  PreviewEnd = {chart.preview_end}")
        lines.append("}")
        lines.append("")

        # [SyncTrack] section
        lines.append("[SyncTrack]")
        lines.append("{")

        # Add time signatures
        for ts in sorted(chart.time_signatures, key=lambda x: x.tick):
            lines.append(f"  {ts.tick} = TS {ts.numerator}")

        # Add BPM changes
        for bpm in sorted(chart.bpm_changes, key=lambda x: x.tick):
            lines.append(f"  {bpm.tick} = B {bpm.milli_bpm}")

        lines.append("}")
        lines.append("")

        # [Events] section
        lines.append("[Events]")
        lines.append("{")

        for section in sorted(chart.sections, key=lambda x: x.tick):
            lines.append(f'  {section.tick} = E "section {section.name}"')

        for event in sorted(chart.events, key=lambda x: x.tick):
            lines.append(f'  {event.tick} = E "{event.text}"')

        lines.append("}")
        lines.append("")

        # Instrument tracks
        ChartParser._write_tracks(lines, chart)

        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    @staticmethod
    def _write_tracks(lines: List[str], chart: Chart):
        """Write all instrument tracks."""
        instruments = [
            (Instrument.GUITAR, chart.guitar, "Single"),
            (Instrument.BASS, chart.bass, "DoubleBass"),
            (Instrument.RHYTHM, chart.rhythm, "DoubleRhythm"),
            (Instrument.KEYS, chart.keys, "Keyboard"),
            (Instrument.DRUMS, chart.drums, "Drums"),
            (Instrument.GHL_GUITAR, chart.ghl_guitar, "GHLGuitar"),
            (Instrument.GHL_BASS, chart.ghl_bass, "GHLBass"),
        ]

        difficulties = [
            (Difficulty.EASY, "Easy"),
            (Difficulty.MEDIUM, "Medium"),
            (Difficulty.HARD, "Hard"),
            (Difficulty.EXPERT, "Expert"),
        ]

        for instrument, tracks, inst_name in instruments:
            for difficulty, diff_name in difficulties:
                if difficulty in tracks:
                    track = tracks[difficulty]
                    section_name = f"{diff_name}{inst_name}"

                    lines.append(f"[{section_name}]")
                    lines.append("{")

                    # Write notes
                    for note in sorted(track.notes, key=lambda n: (n.tick, n.fret)):
                        # Main note
                        lines.append(f"  {note.tick} = N {note.fret} {note.sustain}")

                        # Flags
                        if note.is_forced:
                            lines.append(f"  {note.tick} = N {NoteFlag.FORCED.value} 0")
                        if note.is_tap:
                            lines.append(f"  {note.tick} = N {NoteFlag.TAP.value} 0")

                    # Write star power
                    for sp in sorted(track.star_power, key=lambda x: x.tick):
                        lines.append(f"  {sp.tick} = S 2 {sp.length}")

                    # Write local events
                    for event in sorted(track.events, key=lambda x: x.tick):
                        lines.append(f'  {event.tick} = E "{event.text}"')

                    lines.append("}")
                    lines.append("")


if __name__ == "__main__":
    # Test parser
    print("Chart Parser Test")
    print("=" * 60)

    # Create a test chart
    test_chart = Chart(
        name="Test Song",
        artist="Test Artist",
        resolution=192
    )

    # Add BPM
    test_chart.bpm_changes.append(BPMChange(0, 120.0))

    # Add time signature
    test_chart.time_signatures.append(TimeSignature(0, 4, 2))

    # Add some notes
    track = Track()
    track.add_note(Note(0, 0, 96))      # Green with sustain
    track.add_note(Note(192, 1, 0))     # Red
    track.add_note(Note(384, 2, 0, is_tap=True))  # Yellow tap
    track.add_note(Note(576, 3, 0, is_forced=True))  # Blue forced

    test_chart.set_track(Instrument.GUITAR, Difficulty.EXPERT, track)

    # Write test file
    output_path = "test_chart.chart"
    ChartParser.write_file(test_chart, output_path)
    print(f"Test chart written to: {output_path}")

    # Parse it back
    parsed = ChartParser.parse_file(output_path)
    print(f"\nParsed chart: {parsed.name} by {parsed.artist}")
    print(f"Resolution: {parsed.resolution}")
    print(f"BPM: {parsed.get_initial_bpm()}")

    expert_track = parsed.get_track(Instrument.GUITAR, Difficulty.EXPERT)
    if expert_track:
        print(f"Expert Guitar notes: {expert_track.get_note_count()}")
        for note in expert_track.notes:
            flags = []
            if note.is_tap:
                flags.append("TAP")
            if note.is_forced:
                flags.append("FORCED")
            flag_str = f" [{', '.join(flags)}]" if flags else ""
            print(f"  Tick {note.tick}: Fret {note.fret}, Sustain {note.sustain}{flag_str}")
