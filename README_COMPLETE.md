# 🎸 Clone Hero Chart Maker - COMPLETE SUITE

> **The Ultimate All-in-One Clone Hero Tool**
>
> Combines YOUR GitHub AI features + Moonscraper editing + Bridge library + Spotify integration

---

## 🚀 QUICK START

### **Double-click: `LAUNCH.bat`**

Choose from 5 different tools depending on what you need!

---

## 🎯 WHAT'S INCLUDED

### 1. **WEB APP** (Your Original GitHub Version) ⭐ RECOMMENDED

**What it does:**
- 🤖 **AI Audio-to-Chart** - Convert any audio file to Clone Hero charts
- 📹 **YouTube Downloads** - Paste YouTube URL → instant chart
- 🎵 **Stem Separation** - AI separates vocals, drums, bass, guitar, piano
- 🎹 **Web-based Chart Editor** - Edit charts in your browser
- 📊 **Waveform Visualization** - See audio while editing
- 🎼 **MIDI to Chart** - Convert MIDI files

**How to run:**
```bash
python app.py
```
Then open: http://localhost:8080

**Features:**
- Demucs AI stem separation
- Basic Pitch neural audio-to-MIDI
- In-browser playback and editing
- Drag-and-drop interface
- Quality assurance detection

---

### 2. **DESKTOP APP** (Tkinter GUI)

**What it does:**
- 🎸 **MIDI Guitar Recording** - Capture your guitar performance
- 📚 **Chart Library Browser** - Search 100,000+ charts from Chorus
- 📥 **Download Manager** - Queue and download charts
- 🎵 **Spotify Search** - Find charts for your playlists (partial)

**How to run:**
```bash
python main_app.py
```

**Features:**
- 4 tabbed interface
- MIDI device selection
- Chorus Encore search
- Download queue with progress
- Clone Hero integration

---

### 3. **MIDI CHART CREATOR** (CLI)

**What it does:**
- Record MIDI guitar in real-time
- Convert performance to .chart files
- Simple command-line workflow

**How to run:**
```bash
python chart_maker.py
```

---

### 4. **VISUAL EDITOR** (Pygame)

**What it does:**
- Visual highway editor
- Click to place/remove notes
- HOPO, tap, forced, open notes
- Keyboard shortcuts

**How to run:**
```bash
python visual_editor.py
```

**Controls:**
- `1-5` - Tools
- `F1-F4` - Difficulty
- `Ctrl+S` - Save
- Arrow keys - Navigate

---

### 5. **CLI CONVERTER** (Batch Processing)

**What it does:**
- Command-line MIDI to chart conversion
- Batch processing
- MIDI inspection

**How to run:**
```bash
python -m src.cli input.mid output.chart
python -m src.cli --inspect song.mid
python -m src.cli --preview song.mid
```

---

## 📦 INSTALLATION

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Optional: AI Features

For best quality audio conversion:

```bash
pip install demucs basic-pitch torch
```

**Note:** Requires 4GB+ RAM, GPU recommended

---

## 🎮 FEATURE COMPARISON

| Feature | Web App | Desktop App | MIDI Creator | Visual Editor | CLI |
|---------|---------|-------------|--------------|---------------|-----|
| **AI Audio-to-Chart** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **YouTube Downloads** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Stem Separation** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Web Chart Editor** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **MIDI Recording** | ❌ | ✅ | ✅ | ✅ | ❌ |
| **Chart Library Search** | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Download Manager** | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Visual Editing** | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Batch Processing** | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 🔧 COMPLETE WORKFLOWS

### Workflow 1: Audio File → Chart (Web App)

1. Launch web app: `python app.py`
2. Drag audio file (MP3, WAV, etc.)
3. Wait for AI stem separation
4. Select instrument (vocals, guitar, etc.)
5. Enter song metadata
6. Download chart + audio

**Result:** Ready-to-play Clone Hero chart!

---

### Workflow 2: YouTube → Chart (Web App)

1. Launch web app
2. Paste YouTube URL
3. Select separated instrument
4. Download chart

**Result:** Chart created from YouTube video!

---

### Workflow 3: MIDI Guitar → Chart (MIDI Creator)

1. Connect MIDI guitar
2. Run: `python chart_maker.py`
3. Select device
4. Record performance
5. Generate chart

**Result:** Chart from your playing!

---

### Workflow 4: Search & Download Charts (Desktop App)

1. Run: `python main_app.py`
2. Go to "Chart Library" tab
3. Search song name
4. Select charts
5. Download to Clone Hero

**Result:** Instant chart library!

---

### Workflow 5: Edit Existing Chart (Visual Editor)

1. Run: `python visual_editor.py`
2. Open chart file
3. Place/edit notes
4. Save changes

**Result:** Polished chart!

---

## 📚 TECHNICAL DETAILS

### Your GitHub Features (app.py)

**AI/ML:**
- **Demucs** - Meta's 4-stem or 6-stem separation
- **Basic Pitch** - Spotify's neural audio-to-MIDI
- **pYIN fallback** - Librosa pitch detection

**Audio Processing:**
- Automatic BPM detection
- Waveform visualization
- Multi-format support

**Conversion Algorithm:**
- Phrase-based pitch mapping
- Direction preservation
- Lane smoothing
- Note density reduction
- Quality assurance

**File Structure:**
```
uploads/{job_id}/
  input.mid or input.mp3
  separated/
    vocals.wav
    drums.wav
    bass.wav
    other.wav
  output.chart
  audio.wav
```

---

### Integrated Features (Others)

**Chart Parser (chart_parser.py):**
- Full .chart format support
- HOPO, tap, forced, open notes
- Multi-instrument tracks
- BPM changes, time signatures

**Chorus API (chorus_api.py):**
- Search 100,000+ charts
- Advanced filtering
- Download from CDN

**Download Manager (download_manager.py):**
- Queue system
- Auto-retry
- Progress tracking

**Visual Editor (visual_editor.py):**
- Pygame highway view
- Interactive editing
- Real-time preview

---

## 🎯 RECOMMENDED USAGE

### For Audio Files:
✅ **Use Web App** - Best AI conversion

### For MIDI Files:
✅ **Use Web App** (drag MIDI) OR
✅ **Use CLI** (batch processing)

### For MIDI Guitar:
✅ **Use MIDI Creator** OR
✅ **Use Desktop App** (Tab 1)

### For Chart Editing:
✅ **Use Web App Editor** OR
✅ **Use Visual Editor**

### For Finding Charts:
✅ **Use Desktop App** (Tab 2)

---

## 📖 CONFIGURATION

### config.yaml

```yaml
# Phrase Detection
phrase_silence_beats: 1.0

# Note Processing
max_lane_jump: 2
smoothing_passes: 1

# Defaults
default_tempo_bpm: 120
default_resolution: 192
```

Customize these for different conversion styles!

---

## 🐛 TROUBLESHOOTING

### Web App Won't Start
```bash
# Check if port 5000 is in use
# Try different port:
flask run --port 5001
```

### AI Features Not Working
```bash
# Install AI dependencies:
pip install demucs basic-pitch torch
```

### MIDI Devices Not Found
- Check MIDI drivers installed
- Reconnect device
- Restart Python

### Charts Not Loading in Clone Hero
- Verify .chart file syntax
- Check song.ini has required fields
- Add audio file (song.ogg)

---

## 💡 TIPS & TRICKS

### Best Audio Quality:
1. Use WAV or FLAC files
2. Enable Demucs 6-stem mode
3. Select isolated instrument

### Fastest Conversion:
1. Use MIDI files directly
2. Or use CLI batch mode

### Best Charts:
1. Start with Web App AI conversion
2. Fine-tune in Visual Editor
3. Test in Clone Hero
4. Re-edit if needed

---

## 🤝 CREDITS

### Your GitHub Repository Features:
- AI audio-to-MIDI conversion
- Stem separation (Demucs)
- Web-based chart editor
- YouTube integration
- Phrase-based fret mapping

### Integrated From:
- **Moonscraper** - Visual editing concepts
- **Bridge** - Library management (Chorus API)
- **spotify-clonehero** - Search architecture

### AI Models:
- **Demucs** (Meta) - Stem separation
- **Basic Pitch** (Spotify) - Audio-to-MIDI

---

## 📄 LICENSE

(Your choice - recommend MIT or GPL-3.0)

---

## 🎉 GET STARTED

### Quickest Way:

1. **Double-click `LAUNCH.bat`**
2. **Choose Option 1 (Web App)**
3. **Drag an audio file or paste YouTube URL**
4. **Download your chart!**

### Most Features:

Try ALL 5 tools to see which workflow you prefer!

---

## 📞 SUPPORT

- **Documentation**: See this README
- **Features**: See FEATURES.md
- **Setup**: See SETUP_COMPLETE.md

---

**Happy Charting! 🎸🎶**

*This suite combines the best of everything - Your AI features, professional chart tools, and library management!*
