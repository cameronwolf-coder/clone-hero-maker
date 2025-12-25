"""
Clone Hero .chart File Generator
Converts MIDI notes to Clone Hero .chart format.
"""

from typing import List, Tuple
import os


class ChartGenerator:
    """Generates Clone Hero .chart files from MIDI note data."""

    # Clone Hero note mapping for 5-fret guitar
    # Maps MIDI note numbers to Clone Hero fret numbers (0-4)
    # Standard Guitar MIDI mapping (you may need to adjust based on your MIDI guitar)
    MIDI_TO_FRET = {
        # Expert difficulty (MIDI notes 96-100)
        96: 0,  # Green
        97: 1,  # Red
        98: 2,  # Yellow
        99: 3,  # Blue
        100: 4, # Orange

        # Hard difficulty (MIDI notes 84-88)
        84: 0,  # Green
        85: 1,  # Red
        86: 2,  # Yellow
        87: 3,  # Blue
        88: 4,  # Orange

        # Medium difficulty (MIDI notes 72-76)
        72: 0,  # Green
        73: 1,  # Red
        74: 2,  # Yellow
        75: 3,  # Blue
        76: 4,  # Orange

        # Easy difficulty (MIDI notes 60-64)
        60: 0,  # Green
        61: 1,  # Red
        62: 2,  # Yellow
        63: 3,  # Blue
        64: 4,  # Orange
    }

    # Difficulty track names
    DIFFICULTY_TRACKS = {
        "Expert": (96, 100),
        "Hard": (84, 88),
        "Medium": (72, 76),
        "Easy": (60, 64),
    }

    def __init__(self, resolution: int = 192):
        """
        Initialize chart generator.

        Args:
            resolution: Ticks per quarter note (default: 192)
        """
        self.resolution = resolution

    def seconds_to_ticks(self, seconds: float, bpm: float) -> int:
        """
        Convert seconds to ticks based on BPM.

        Args:
            seconds: Time in seconds
            bpm: Beats per minute

        Returns:
            Tick position
        """
        beats = seconds * (bpm / 60.0)
        ticks = int(beats * self.resolution)
        return ticks

    def midi_notes_to_chart_notes(
        self,
        midi_notes: List[Tuple[float, int, int, float]],
        bpm: float,
        difficulty: str = "Expert"
    ) -> List[Tuple[int, int, int]]:
        """
        Convert MIDI notes to Clone Hero chart notes.

        Args:
            midi_notes: List of (start_time, note_number, velocity, duration)
            bpm: Beats per minute
            difficulty: Difficulty level

        Returns:
            List of (tick, fret_number, sustain_ticks)
        """
        chart_notes = []

        if difficulty not in self.DIFFICULTY_TRACKS:
            raise ValueError(f"Invalid difficulty: {difficulty}")

        min_note, max_note = self.DIFFICULTY_TRACKS[difficulty]

        for start_time, note_num, velocity, duration in midi_notes:
            # Check if note is in the range for this difficulty
            if min_note <= note_num <= max_note:
                # Map MIDI note to fret number
                if note_num in self.MIDI_TO_FRET:
                    fret = self.MIDI_TO_FRET[note_num]
                    tick = self.seconds_to_ticks(start_time, bpm)
                    sustain = self.seconds_to_ticks(duration, bpm)

                    # Minimum sustain length (avoid very short sustains)
                    if sustain < 20:
                        sustain = 0

                    chart_notes.append((tick, fret, sustain))

        return sorted(chart_notes, key=lambda x: x[0])

    def generate_chart_file(
        self,
        midi_notes: List[Tuple[float, int, int, float]],
        output_path: str,
        song_name: str,
        artist: str,
        bpm: float,
        difficulty: str = "Expert"
    ):
        """
        Generate a complete .chart file.

        Args:
            midi_notes: List of (start_time, note_number, velocity, duration)
            output_path: Path to save the .chart file
            song_name: Name of the song
            artist: Artist name
            bpm: Beats per minute
            difficulty: Difficulty level to generate
        """
        chart_notes = self.midi_notes_to_chart_notes(midi_notes, bpm, difficulty)

        # Build .chart file content
        chart_content = self._build_chart_content(
            chart_notes, song_name, artist, bpm, difficulty
        )

        # Write to file
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(chart_content)

        print(f"Chart file created: {output_path}")
        print(f"Notes in chart: {len(chart_notes)}")

    def _build_chart_content(
        self,
        chart_notes: List[Tuple[int, int, int]],
        song_name: str,
        artist: str,
        bpm: float,
        difficulty: str
    ) -> str:
        """Build the complete .chart file content."""

        content = []

        # Header
        content.append("[Song]")
        content.append("{")
        content.append(f'  Name = "{song_name}"')
        content.append(f'  Artist = "{artist}"')
        content.append(f'  Charter = "MIDI Chart Maker"')
        content.append(f"  Resolution = {self.resolution}")
        content.append("}")
        content.append("")

        # Sync Track (BPM and Time Signature)
        content.append("[SyncTrack]")
        content.append("{")
        content.append("  0 = TS 4")  # 4/4 time signature
        content.append(f"  0 = B {int(bpm * 1000)}")  # BPM in milliBPM
        content.append("}")
        content.append("")

        # Events Track
        content.append("[Events]")
        content.append("{")
        content.append("}")
        content.append("")

        # Single Guitar Track (Expert difficulty)
        track_name = f"ExpertSingle"  # Clone Hero uses this naming
        content.append(f"[{track_name}]")
        content.append("{")

        # Add notes
        for tick, fret, sustain in chart_notes:
            if sustain > 0:
                content.append(f"  {tick} = N {fret} {sustain}")
            else:
                content.append(f"  {tick} = N {fret} 0")

        content.append("}")
        content.append("")

        return "\n".join(content)

    def generate_song_ini(
        self,
        output_path: str,
        song_name: str,
        artist: str,
        album: str = "",
        genre: str = "rock",
        year: str = "",
        charter: str = "MIDI Chart Maker"
    ):
        """
        Generate a song.ini metadata file.

        Args:
            output_path: Path to save the song.ini file
            song_name: Name of the song
            artist: Artist name
            album: Album name (optional)
            genre: Music genre
            year: Release year (optional)
            charter: Charter name
        """
        ini_content = [
            "[song]",
            f"name = {song_name}",
            f"artist = {artist}",
            f"album = {album}",
            f"genre = {genre}",
            f"year = {year}",
            f"charter = {charter}",
            "diff_guitar = -1",  # Auto-detect difficulty
            "diff_bass = -1",
            "diff_rhythm = -1",
            "diff_drums = -1",
            "diff_keys = -1",
            "diff_guitarghl = -1",
            "diff_bassghl = -1",
        ]

        with open(output_path, 'w') as f:
            f.write("\n".join(ini_content))

        print(f"Song.ini created: {output_path}")


if __name__ == "__main__":
    # Test chart generation
    generator = ChartGenerator()

    # Example MIDI notes: (start_time, note_number, velocity, duration)
    test_notes = [
        (0.0, 96, 100, 0.5),    # Green note at start
        (0.5, 97, 100, 0.5),    # Red note
        (1.0, 98, 100, 0.5),    # Yellow note
        (1.5, 99, 100, 0.5),    # Blue note
        (2.0, 100, 100, 0.5),   # Orange note
        (2.5, 96, 100, 1.0),    # Green note with sustain
    ]

    # Generate test chart
    test_dir = "test_song"
    os.makedirs(test_dir, exist_ok=True)

    generator.generate_chart_file(
        midi_notes=test_notes,
        output_path=f"{test_dir}/notes.chart",
        song_name="Test Song",
        artist="Test Artist",
        bpm=120.0,
        difficulty="Expert"
    )

    generator.generate_song_ini(
        output_path=f"{test_dir}/song.ini",
        song_name="Test Song",
        artist="Test Artist"
    )

    print(f"\nTest chart generated in '{test_dir}' folder")
