# Clone Hero Converter

Convert Hooktheory/Hookpad MIDI files to Clone Hero `.chart` format for 5-fret guitar.

## Features

- **Web Interface**: Browser-based converter with drag & drop
- **YouTube Integration**: Download audio directly from YouTube URLs
- **MIDI Parsing**: Auto-detects lead melody track from Hookpad exports
- **Intelligent Mapping**: Phrase-based pitch-to-lane mapping with smoothing
- **QA Detection**: Flags potential charting issues (inspired by [midi-ch](https://github.com/EFHIII/midi-ch))
- **Configurable**: YAML config for tuning phrase detection, smoothing, etc.

## Installation

```bash
cd "Clone Hero Maker"
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Usage

### Web Interface (Recommended)

Start the web server:

```bash
python app.py
```

Then open http://localhost:5000 in your browser.

**Features:**
- Drag & drop MIDI upload
- YouTube audio download (just paste a URL)
- Track selection UI
- Live lane preview
- Download .chart or bundled .zip with audio

### CLI: Basic Conversion

```bash
python -m src.cli input.mid output.chart
```

### CLI: With Metadata

```bash
python -m src.cli song.mid song.chart --name "My Song" --artist "Artist Name"
```

### CLI: Inspect MIDI Structure

```bash
python -m src.cli --inspect song.mid
```

### CLI: With Preview

```bash
python -m src.cli song.mid song.chart --preview --verbose
```

## CLI Options

| Option | Description |
|--------|-------------|
| `--name, -n` | Song name |
| `--artist, -a` | Artist name |
| `--charter, -c` | Charter name |
| `--track, -t` | Track index (0-based, auto-detect if omitted) |
| `--config` | Path to config.yaml |
| `--preview, -p` | Show ASCII lane preview |
| `--verbose, -v` | Verbose output |
| `--inspect, -i` | Inspect MIDI without converting |
| `--no-qa` | Skip QA issue detection |

## Configuration

Edit `config.yaml` to adjust:

```yaml
# Phrase detection
phrase_silence_beats: 1.0

# Lane smoothing
max_lane_jump: 2
smoothing_passes: 1

# Track detection patterns
lead_track_patterns:
  - "lead"
  - "melody"
  - "vocal"
```

## Workflow

1. **Export MIDI from Hookpad** (lead melody track)
2. **Run converter**: `python -m src.cli song.mid out/song.chart`
3. **Review in Moonscraper** - QA markers show potential issues
4. **Add audio** and polish

## QA Markers

The converter embeds event markers for potential issues:

| Marker | Meaning |
|--------|---------|
| `Bad_Too_Low` | Higher pitch charted to lower fret |
| `Bad_Too_High` | Lower pitch charted to higher fret |
| `Bad_Different_Fret` | Same pitch on different frets |

These appear as events in Moonscraper for easy review.

## Project Structure

```
Clone Hero Maker/
├── app.py                 # Flask web server
├── templates/
│   └── index.html         # Web interface
├── static/
│   ├── style.css          # Dark theme styles
│   └── app.js             # Frontend logic
├── src/
│   ├── parse_midi.py      # MIDI parsing & note extraction
│   ├── map_to_frets.py    # Pitch → lane mapping
│   ├── chart_writer.py    # .chart file generation
│   └── cli.py             # Command-line interface
├── tests/
│   ├── test_mapping.py
│   └── test_chart_writer.py
├── uploads/               # Temporary job files
├── config.yaml            # Configuration
└── requirements.txt
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Algorithm Overview

1. **Extract lead notes** from MIDI with absolute timing
2. **Segment into phrases** based on silence gaps
3. **Scale each phrase** linearly to 0-4 lanes
4. **Smooth** to avoid large jumps between consecutive notes
5. **Preserve direction** - nudge lanes to match pitch motion
6. **Generate .chart** with proper timing and QA events
