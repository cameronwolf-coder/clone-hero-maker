"""
CLI for Hooktheory MIDI to Clone Hero .chart Converter.

Usage:
    python -m src.cli input.mid output.chart [options]

Example:
    python -m src.cli hookpad_midis/song.mid out/song.chart --name "My Song" --artist "Artist"
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

import yaml

from src.parse_midi import extract_lead_notes, print_midi_info, MidiData
from src.map_to_frets import (
    map_pitches_to_lanes,
    create_mapped_notes,
    preview_lanes_ascii,
    summarize_qa_issues,
    MappedNote,
)
from src.chart_writer import write_chart, ChartMetadata


def load_config(config_path: Optional[str] = None) -> dict:
    """Load configuration from YAML file."""
    default_config = {
        "phrase_silence_beats": 1.0,
        "max_lane_jump": 2,
        "smoothing_passes": 1,
        "default_bpm": 120.0,
        "lead_track_patterns": ["lead", "melody", "vocal", "synth"],
        "chart_defaults": {
            "resolution": 192,
            "difficulty": "Expert",
            "charter": "Auto-Generated",
        },
    }

    if config_path is None:
        # Look for config.yaml in current dir or project root
        possible_paths = [
            Path("config.yaml"),
            Path(__file__).parent.parent / "config.yaml",
        ]
        for p in possible_paths:
            if p.exists():
                config_path = str(p)
                break

    if config_path and Path(config_path).exists():
        with open(config_path, "r") as f:
            user_config = yaml.safe_load(f) or {}
            # Merge with defaults
            for key, value in user_config.items():
                if isinstance(value, dict) and key in default_config:
                    default_config[key].update(value)
                else:
                    default_config[key] = value

    return default_config


def convert_midi_to_chart(
    midi_path: str,
    chart_path: str,
    song_name: Optional[str] = None,
    artist: Optional[str] = None,
    charter: Optional[str] = None,
    track_index: Optional[int] = None,
    config: Optional[dict] = None,
    preview: bool = False,
    verbose: bool = False,
    include_qa: bool = True,
) -> dict:
    """
    Convert a Hookpad MIDI file to a Clone Hero .chart file.

    Args:
        midi_path: Path to input MIDI file.
        chart_path: Path to output .chart file.
        song_name: Song name for chart metadata.
        artist: Artist name for chart metadata.
        charter: Charter name for chart metadata.
        track_index: Specific track to use (auto-detect if None).
        config: Configuration dictionary.
        preview: Show ASCII lane preview.
        verbose: Print detailed progress.
        include_qa: Include QA issue markers in chart.

    Returns:
        Dictionary with conversion statistics.
    """
    if config is None:
        config = load_config()

    # Extract notes from MIDI
    if verbose:
        print(f"Reading MIDI: {midi_path}")

    midi_data = extract_lead_notes(
        midi_path,
        track_index=track_index,
        lead_patterns=config.get("lead_track_patterns"),
        default_bpm=config.get("default_bpm", 120.0),
    )

    if verbose:
        print(f"  Track: {midi_data.track_name}")
        print(f"  BPM: {midi_data.bpm}")
        print(f"  Notes: {len(midi_data.notes)}")
        print(f"  Ticks/beat: {midi_data.ticks_per_beat}")

    if not midi_data.notes:
        raise ValueError("No notes found in the selected track")

    # Map pitches to lanes
    if verbose:
        print("\nMapping pitches to lanes...")

    lanes = map_pitches_to_lanes(
        midi_data.notes,
        midi_data.ticks_per_beat,
        phrase_silence_beats=config.get("phrase_silence_beats", 1.0),
        max_lane_jump=config.get("max_lane_jump", 2),
        smoothing_passes=config.get("smoothing_passes", 1),
    )

    # Create mapped notes with QA detection
    mapped_notes = create_mapped_notes(midi_data.notes, lanes, include_qa=include_qa)

    # QA summary
    qa_summary = summarize_qa_issues(mapped_notes)
    if verbose and qa_summary:
        print("\nQA Issues Detected:")
        for issue, count in qa_summary.items():
            print(f"  {issue}: {count}")

    # Preview
    if preview:
        print(preview_lanes_ascii(
            midi_data.notes, lanes, midi_data.ticks_per_beat
        ))

    # Build metadata
    chart_defaults = config.get("chart_defaults", {})
    metadata = ChartMetadata(
        name=song_name or Path(midi_path).stem,
        artist=artist or "Unknown",
        charter=charter or chart_defaults.get("charter", "Auto-Generated"),
        resolution=chart_defaults.get("resolution", 192),
    )

    # Write chart
    if verbose:
        print(f"\nWriting chart: {chart_path}")

    write_chart(
        chart_path,
        midi_data.notes,
        lanes,
        midi_data.ticks_per_beat,
        midi_data.bpm,
        metadata=metadata,
        mapped_notes=mapped_notes if include_qa else None,
        include_qa_events=include_qa,
    )

    # Calculate duration
    if midi_data.notes:
        total_ticks = midi_data.notes[-1].end_tick - midi_data.notes[0].start_tick
        duration_beats = total_ticks / midi_data.ticks_per_beat
        duration_seconds = duration_beats * (60 / midi_data.bpm)
    else:
        duration_beats = 0
        duration_seconds = 0

    stats = {
        "notes": len(midi_data.notes),
        "track": midi_data.track_name,
        "bpm": midi_data.bpm,
        "duration_beats": duration_beats,
        "duration_seconds": duration_seconds,
        "qa_issues": qa_summary,
    }

    return stats


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert Hooktheory/Hookpad MIDI to Clone Hero .chart",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.cli song.mid song.chart
  python -m src.cli song.mid song.chart --name "My Song" --artist "Me"
  python -m src.cli song.mid song.chart --preview --verbose
  python -m src.cli --inspect song.mid
        """,
    )

    parser.add_argument("input", help="Input MIDI file path")
    parser.add_argument("output", nargs="?", help="Output .chart file path")

    # Metadata options
    parser.add_argument("--name", "-n", help="Song name")
    parser.add_argument("--artist", "-a", help="Artist name")
    parser.add_argument("--charter", "-c", help="Charter name")

    # Processing options
    parser.add_argument(
        "--track", "-t", type=int, help="Track index to use (0-based)"
    )
    parser.add_argument(
        "--config", help="Path to config.yaml"
    )
    parser.add_argument(
        "--no-qa", action="store_true", help="Skip QA issue detection"
    )

    # Output options
    parser.add_argument(
        "--preview", "-p", action="store_true", help="Show ASCII lane preview"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )
    parser.add_argument(
        "--inspect", "-i", action="store_true",
        help="Inspect MIDI file structure (don't convert)"
    )

    args = parser.parse_args()

    # Validate input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Inspect mode
    if args.inspect:
        print_midi_info(args.input)
        sys.exit(0)

    # Require output for conversion
    if not args.output:
        # Default output path
        args.output = str(input_path.with_suffix(".chart"))
        print(f"Output: {args.output}")

    # Load config
    config = load_config(args.config)

    try:
        stats = convert_midi_to_chart(
            midi_path=args.input,
            chart_path=args.output,
            song_name=args.name,
            artist=args.artist,
            charter=args.charter,
            track_index=args.track,
            config=config,
            preview=args.preview,
            verbose=args.verbose,
            include_qa=not args.no_qa,
        )

        # Print summary
        print(f"\nConversion complete!")
        print(f"  Notes: {stats['notes']}")
        print(f"  Track: {stats['track']}")
        print(f"  BPM: {stats['bpm']:.1f}")
        print(f"  Duration: {stats['duration_seconds']:.1f}s ({stats['duration_beats']:.1f} beats)")

        if stats["qa_issues"]:
            print(f"\n  QA Issues (review in Moonscraper):")
            for issue, count in stats["qa_issues"].items():
                print(f"    {issue}: {count}")

        print(f"\n  Output: {args.output}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
