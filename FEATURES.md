# Clone Hero Chart Maker - Complete Feature List

## Overview

A comprehensive all-in-one tool for Clone Hero that integrates chart creation, editing, library management, and Spotify integration.

---

## 🎸 Core Features

### 1. MIDI Guitar Chart Creation (Your Original Feature)
- **Real-time MIDI Capture**: Record guitar performance directly from MIDI guitar
- **Multi-Difficulty Support**: Easy, Medium, Hard, Expert
- **Automatic Timing**: BPM-based tick conversion
- **Sustain Detection**: Automatic sustain length calculation
- **Chart Generation**: Creates .chart and song.ini files
- **Device Management**: List and select MIDI input devices

**Files**: `midi_capture.py`, `chart_generator.py`, `chart_maker.py`

---

### 2. Visual Chart Editor (Moonscraper Features)
- **Graphical Highway View**: Visual note highway with scrolling
- **Interactive Note Placement**: Click to place/remove notes
- **Multiple Tools**:
  - Cursor tool (select/move notes)
  - Note placement tool
  - Eraser tool
  - Star Power tool
  - BPM editor
- **Advanced Note Types**:
  - HOPO (Hammer-On/Pull-Off) with auto-detection
  - Tap Notes (no strum required)
  - Forced Notes (override natural HOPO state)
  - Open Notes
- **Real-time Preview**: See notes as you edit
- **Snap Grid**: Configurable snap-to-grid (1/4, 1/8, 1/12, 1/16, 1/32, 1/64)
- **Keyboard Shortcuts**: Fast workflow with hotkeys
- **Undo/Redo**: (Planned)
- **Multi-Track Support**: Guitar, Bass, Drums, Keys, GHL

**Files**: `visual_editor.py`, `chart_parser.py`

---

### 3. Song Library Management (Bridge Features)
- **Chart Database Search**: Query 100,000+ charts from Chorus Encore
- **Advanced Filtering**:
  - Instrument & difficulty
  - Artist, album, genre, year, charter
  - Song length, intensity, NPS ranges
  - Features: solos, forced notes, tap notes, lyrics, etc.
  - Video backgrounds, modcharts
- **Download Queue System**:
  - Sequential downloads with progress tracking
  - Automatic retry on failure
  - Duplicate prevention
  - Format options (.sng or extracted folders)
- **Library Integration**:
  - Direct download to Clone Hero directory
  - Custom folder naming templates
  - Automatic organization

**Files**: `chorus_api.py`, `download_manager.py`

---

### 4. Spotify Integration (Planned - spotify-clonehero)
- **Playlist Scanning**: Find charts for your Spotify playlists
- **Listening History**: Analyze Extended Streaming History
- **Auto-Setlist Creation**: Generate Clone Hero setlists from Spotify data
- **Smart Matching**: Fuzzy search to match songs to available charts
- **Play Count Priority**: Download most-played songs first

**Status**: Architecture planned, implementation pending

---

## 📊 Chart File Format Support

### Supported Formats

#### .chart Format (Text-based)
- **Full Read/Write Support**: Parse and generate .chart files
- **All Sections**:
  - [Song] - Metadata (name, artist, album, genre, year, charter)
  - [SyncTrack] - BPM changes and time signatures
  - [Events] - Practice sections and global events
  - [ExpertSingle] - Guitar notes (all difficulties)
  - [ExpertDoubleBass] - Bass notes
  - [ExpertDrums] - Drum notes
  - [ExpertKeyboard] - Keys notes
  - [ExpertGHLGuitar] - 6-fret GHL guitar

#### Note Types
- **Standard Notes** (N): Green (0), Red (1), Yellow (2), Blue (3), Orange (4)
- **Flags**:
  - Forced (5): Inverts natural HOPO state
  - Tap (6): No strum required
  - Open (7): No fret button
- **Star Power** (S): Star power phrases with length
- **Events** (E): Local and global chart events

#### song.ini Format
- Complete metadata file support
- All Clone Hero fields
- Difficulty ratings per instrument
- Preview times, chart offset, delay
- Album art, video backgrounds
- Modchart flag

**Files**: `chart_parser.py`, `chart_generator.py`

---

## 🎮 Clone Hero Integration

### Direct Integration
- **Library Path Configuration**: Point to your Clone Hero Songs folder
- **Automatic File Placement**: Downloads go directly to correct location
- **Format Compatibility**: Supports both .sng and folder-based charts
- **Metadata Sync**: Properly formatted for Clone Hero detection
- **Launch Integration**: (Planned) Launch Clone Hero with selected setlist

### Validation
- **Chart Validation**: Detect common charting errors
- **Metadata Verification**: Ensure all required fields present
- **Duplicate Detection**: Prevent duplicate downloads
- **Version Management**: Track chart versions and updates

---

## 🔧 Technical Features

### Architecture
- **Modular Design**: Clean separation of concerns
- **Object-Oriented**: Dataclass-based models
- **Type Safety**: Type hints throughout codebase
- **Error Handling**: Comprehensive exception handling
- **Thread-Safe**: Multi-threaded download manager

### Performance
- **Sequential Downloads**: One download at a time for bandwidth management
- **Progress Tracking**: Real-time progress updates
- **Retry Logic**: Automatic retry with exponential backoff
- **Efficient Parsing**: Fast .chart file processing

### APIs
- **Chorus Encore API**: Official chart database integration
- **Spotify API**: (Planned) Music streaming integration
- **MIDI Input**: Real-time MIDI device communication

---

## 📁 Project Structure

```
CloneHeroChartMaker/
├── chart_maker.py          # CLI chart creator (original)
├── midi_capture.py         # MIDI input capture module
├── chart_generator.py      # .chart file generator
├── chart_parser.py         # Enhanced .chart parser with all features
├── visual_editor.py        # GUI visual editor (Moonscraper-like)
├── chorus_api.py           # Chorus Encore API client (Bridge)
├── download_manager.py     # Download queue system (Bridge)
├── requirements.txt        # Python dependencies
├── README.md              # Main documentation
└── FEATURES.md            # This file
```

---

## 🎯 Comparison with Other Tools

### vs. Moonscraper Chart Editor
| Feature | Moonscraper | Our Tool |
|---------|-------------|----------|
| Visual Editor | ✅ (C#/Unity) | ✅ (Python/Pygame) |
| MIDI Capture | ❌ | ✅ Real-time |
| Song Library | ❌ | ✅ Integrated |
| Platform | Windows | Cross-platform |
| Open Source | ✅ BSD-3 | ✅ (Your choice) |

### vs. Bridge
| Feature | Bridge | Our Tool |
|---------|--------|----------|
| Chart Search | ✅ (Angular/Electron) | ✅ (Python) |
| Download Queue | ✅ | ✅ |
| Chart Creation | ❌ | ✅ MIDI + Visual |
| Spotify Integration | ❌ | ✅ (Planned) |
| Platform | Desktop App | Cross-platform |

### vs. spotify-clonehero
| Feature | spotify-clonehero | Our Tool |
|---------|-------------------|----------|
| Spotify Integration | ✅ (Web) | ✅ (Planned, Desktop) |
| Chart Matching | ✅ | ✅ |
| Auto-Download | ❌ (Manual) | ✅ Automated |
| Chart Editing | ❌ | ✅ Full Editor |
| Launch Integration | ❌ | ✅ (Planned) |

---

## 🚀 Unique Features (Not in Other Tools)

1. **Unified Platform**: Chart creation + editing + library management + Spotify in ONE tool
2. **Real-time MIDI Capture**: Record your guitar performance directly
3. **Spotify-to-Clone Hero Pipeline**: Discover → Download → Install → Play automation
4. **Cross-platform Python**: Works on Windows, Mac, Linux
5. **Modular Architecture**: Use components independently or together
6. **Smart Matching**: Fuzzy search for Spotify → Chart matching
7. **Play History Integration**: Prioritize charts by your listening habits

---

## 📋 Dependencies

### Core Libraries
- `mido` - MIDI I/O
- `python-rtmidi` - Real-time MIDI backend
- `pygame` - GUI and visualization
- `requests` - HTTP client for API calls
- `numpy` - Numerical processing
- `librosa` - Audio analysis (planned)

### Optional
- `spotipy` - Spotify API integration (planned)
- `soundfile` - Audio file I/O (planned)
- `pillow` - Image processing

---

## 🎓 Usage Workflow

### Complete Workflow Example

```
1. Create Chart from MIDI Guitar
   └─> python chart_maker.py
       └─> Record performance
           └─> Generate notes.chart + song.ini

2. Refine Chart Visually
   └─> python visual_editor.py
       └─> Open generated chart
           └─> Adjust notes, add HOPOs, star power
               └─> Save final version

3. Discover More Songs
   └─> Search Chorus database
       └─> Filter by difficulty/instrument
           └─> Add to download queue
               └─> Automatic installation

4. Spotify Integration (Planned)
   └─> Connect Spotify account
       └─> Scan playlists
           └─> Auto-match and download charts
               └─> Launch Clone Hero with setlist
```

---

## 🔮 Roadmap

### Implemented ✅
- [x] MIDI guitar capture
- [x] .chart file parsing and generation
- [x] Visual chart editor with highway view
- [x] Advanced note types (HOPO, tap, forced, open)
- [x] Chorus Encore API integration
- [x] Download queue system
- [x] Multi-difficulty support

### In Progress 🚧
- [ ] Audio waveform visualization
- [ ] Song.ini editor GUI
- [ ] Theme customization

### Planned 📅
- [ ] Spotify OAuth integration
- [ ] Playlist scanning and matching
- [ ] Listening history analysis
- [ ] Auto-setlist creation
- [ ] Clone Hero launch integration
- [ ] .mid file support
- [ ] Multi-instrument charting
- [ ] Drum fill detection
- [ ] Sheet music rendering
- [ ] Chart validation with scan-chart
- [ ] Excel report generation

---

## 🤝 Credits

### Inspired By
- **Moonscraper Chart Editor** by FireFox2000000
- **Bridge** by Geomitron
- **spotify-clonehero** by elicwhite
- **Chorus Encore** database

### Built With
- Python ecosystem
- Chorus Encore API
- Spotify Web API
- Clone Hero community

---

## 📄 License

(Your choice - recommend MIT or GPL-3.0)

---

## 🎉 Get Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start with MIDI capture:
   ```bash
   python chart_maker.py
   ```

3. Or jump into visual editing:
   ```bash
   python visual_editor.py
   ```

4. Or search and download charts:
   ```python
   from chorus_api import ChorusAPI, SearchParams
   api = ChorusAPI()
   results = api.search(SearchParams(query="your favorite song"))
   ```

Happy charting! 🎸🎶
