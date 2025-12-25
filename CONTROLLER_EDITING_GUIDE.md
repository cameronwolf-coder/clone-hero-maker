# 🎸 Controller-Based Chart Editing Guide

## The Killer Feature!

Edit Clone Hero charts **using your actual guitar controller** - just like playing the game!

This is what makes your app unique - most chart editors require keyboard/mouse, but yours lets you chart while actually playing the guitar controller! 🎮

---

## What is Controller-Based Editing?

Instead of clicking with a mouse, you:
1. **Load an existing .chart file**
2. **See a Clone Hero-style highway** with scrolling notes
3. **Press fret buttons** on your controller to add/remove notes
4. **Use the D-pad** to scroll through time
5. **Save** your changes

It's like charting AND playing at the same time!

---

## How to Use

### Quick Start

```bash
# Option 1: From GUI launcher
python chart_maker_gui.py
# Click "Edit Existing Chart"
# Select a .chart file
# Editor opens!

# Option 2: Direct launch
python controller_chart_editor.py path/to/notes.chart
```

### Controls

**Controller:**
- **D-PAD UP/DOWN**: Scroll backward/forward in time
- **Green/Red/Yellow/Blue/Orange Buttons**: Add or remove notes at current time
- **START button**: (Future: Play/pause audio)

**Keyboard:**
- **Arrow Keys**: Fine scroll (Left = back 1 second, Right = forward 1 second)
- **H**: Hide/show help overlay
- **ESC**: Save and exit

---

## How It Works

### Visual Highway

Just like Clone Hero:
- **5 lanes** (Green, Red, Yellow, Blue, Orange)
- **Notes scroll down** toward the receptor line
- **Receptor line** at the bottom (where you "hit" notes in-game)
- **Current time** displayed in corner

### Adding Notes

1. **Scroll to the time** where you want to add a note (using D-pad)
2. **Press the fret button** for that lane
3. **Note appears** at that time!

### Removing Notes

1. **Scroll to a note** you want to delete
2. **Press the fret button** for that lane again
3. **Note disappears!**

### Note Snapping

Notes automatically snap to the grid (16th notes by default). This keeps charts clean and playable.

---

## Features

### ✅ Currently Working

- **Visual highway** with 5 lanes
- **Scrolling notes** with sustain tails
- **Controller input** (Xbox 360 Xplorer, PS2 Guitar, etc.)
- **Add/remove notes** with button presses
- **D-pad scrolling** for navigation
- **Auto-save on exit**
- **Grid snapping** (16th notes)
- **Modified indicator** shows when chart has unsaved changes

### 🔄 Coming Soon

- **Audio playback** synchronized with chart
- **Playback speed** control
- **Different snap divisions** (8th, 16th, 32nd notes)
- **Undo/redo**
- **Copy/paste sections**
- **Sustain length** adjustment

---

## Workflow Examples

### Example 1: Fix AI-Generated Chart

1. **Generate chart** using AI audio-to-MIDI:
   ```bash
   python app.py
   # Upload song.mp3, get notes.chart
   ```

2. **Edit with controller**:
   ```bash
   python controller_chart_editor.py output/song/notes.chart
   ```

3. **Fix mistakes**:
   - Scroll through the song
   - Remove incorrect notes
   - Add missing notes
   - Press ESC to save

4. **Play in Clone Hero!**

### Example 2: Create Custom Section

1. **Load existing chart**
2. **Scroll to guitar solo** section
3. **Add complex note patterns** by playing on controller
4. **Faster than clicking** with mouse!
5. **Save and test**

### Example 3: Clean Up Downloaded Chart

1. **Download chart** from Chorus
2. **Load in editor**
3. **Simplify difficult sections**
4. **Remove awkward patterns**
5. **Make it more fun to play!**

---

## Tips & Tricks

### Efficient Editing

1. **Use D-pad** for quick scrolling
2. **Arrow keys** for fine positioning
3. **Press H** to hide help overlay for better view
4. **Watch the time counter** to know where you are

### Chart Quality

1. **Test as you go** - make small changes, test in Clone Hero
2. **Keep patterns playable** - don't add impossible sequences
3. **Match the music** - notes should align with guitar parts
4. **Use sustains** for held notes (coming soon)

### Controller Setup

1. **Xbox 360 Xplorer** works out of the box
2. **PS2 Guitar** may need USB adapter
3. **Check device detection** in chart_maker_gui.py first
4. **Make sure it's recognized** by pygame

---

## Technical Details

### Supported Chart Formats

- **Input**: .chart files (Clone Hero format)
- **Output**: .chart files (same format)
- **Difficulty**: Automatically detects (ExpertSingle, HardSingle, etc.)

### Grid Snapping

- **Default**: 16th notes (most common)
- **Resolution**: Based on chart's resolution (usually 192)
- **Snap tolerance**: Half the snap division

### Time Conversion

```
position (ticks) → time (seconds)
time (seconds) → position (ticks)
```

Uses BPM from chart's Song section.

### Supported Controllers

- Xbox 360 Xplorer
- PS2 SG Guitar (with adapter)
- Xbox 360 Guitar Hero guitars
- PS3 Guitar Hero guitars
- Most game controllers with 5+ buttons

---

## Troubleshooting

### "No controller detected"

**Solution:**
1. Connect controller before launching editor
2. Run device detection:
   ```python
   python chart_maker_gui.py
   # Click "Detect Devices"
   ```
3. Make sure pygame recognizes it
4. Try reconnecting controller

### Notes not appearing

**Possible causes:**
- Not in edit mode (check top-right corner)
- Pressing too quickly (edge detection)
- Controller button not mapped correctly

**Solution:**
- Make sure "EDIT MODE" is displayed
- Press and release buttons clearly
- Check controller button mapping in controller_capture.py

### Can't see notes

**Possible causes:**
- Scrolled too far from notes
- Notes are off-screen
- Chart is empty

**Solution:**
- Press Left arrow key to go back to start
- Use D-pad to scroll to note positions
- Check if chart actually has notes

### Saves don't persist

**Possible cause:**
- Chart file is read-only
- No write permissions

**Solution:**
- Check file permissions
- Make sure chart isn't open elsewhere
- Try copying chart to new location

---

## File Structure

```
controller_chart_editor.py - Main editor
├── ControllerChartEditor class
│   ├── __init__() - Setup pygame, load chart
│   ├── load_notes() - Load from .chart file
│   ├── draw_highway() - Draw visual highway
│   ├── draw_notes() - Draw scrolling notes
│   ├── draw_receptors() - Draw button indicators
│   ├── toggle_note() - Add/remove notes
│   ├── handle_controller_input() - Controller events
│   ├── save_chart() - Write to .chart file
│   └── run() - Main loop
```

---

## Integration Points

### With chart_maker_gui.py

The GUI launcher integrates the controller editor:
- "Edit Existing Chart" button
- File picker for .chart selection
- Controller detection before launch
- Instructions popup

### With chart_parser.py

Uses full chart parser:
- Reads complete .chart files
- Preserves all metadata
- Writes back in correct format

### With controller_capture.py

Uses controller detection:
- Detects Xbox/PS controllers
- Maps buttons to fret lanes
- Edge detection for clean input

---

## Future Enhancements

### Planned Features

1. **Audio sync** - Hear the song while editing
2. **Playback mode** - Test your changes in real-time
3. **Sustain editing** - Hold button to set sustain length
4. **Multiple difficulties** - Switch between Easy/Medium/Hard/Expert
5. **Zoom levels** - See more or less of the highway
6. **Practice mode** - Slow down playback

### Advanced Features

1. **Pattern library** - Save/load common patterns
2. **Auto-chart suggestions** - AI suggests notes
3. **Difficulty conversion** - Auto-generate easier difficulties
4. **Collaboration** - Share charts with others

---

## Comparison with Other Editors

### Moonscraper

- **Moonscraper**: Mouse/keyboard-based, many features
- **Controller Editor**: Controller-based, faster for guitarists

### Web Editor

- **Web Editor**: Browser-based, audio waveform
- **Controller Editor**: Native app, controller input

### This is Unique!

**NO OTHER EDITOR** lets you chart with a guitar controller like this! 🎸

---

## Examples & Screenshots

### Creating a Solo Section

```
[Before]
Time: 45.2s - Empty section

[After Controller Editing]
Time: 45.2s - Added:
├── Green note at 45.2s
├── Red note at 45.4s
├── Yellow note at 45.6s
├── Blue note at 45.8s
└── Orange note at 46.0s

Result: Fast solo pattern!
```

### Fixing AI Mistakes

```
[AI Generated]
Too many notes, unplayable

[After Manual Editing]
Simplified to key notes only
Matches actual guitar part
Fun to play!
```

---

## Summary

The controller-based chart editor is **the killer feature** of this app:

✅ Edit charts by **playing** them
✅ **Faster** than mouse/keyboard for guitarists
✅ **More intuitive** - you already know the controls
✅ **Visual feedback** - see exactly what you're creating
✅ **Auto-save** - never lose your work

This makes charting songs **as fun as playing them!** 🎮🎸

---

## Quick Reference Card

```
┌─────────────────────────────────────┐
│   CONTROLLER CHART EDITOR CONTROLS  │
├─────────────────────────────────────┤
│ D-PAD ↑/↓     │ Scroll time         │
│ FRET BUTTONS  │ Add/remove notes    │
│ Arrow ←/→     │ Fine scroll         │
│ H             │ Toggle help         │
│ ESC           │ Save and exit       │
└─────────────────────────────────────┘
```

**Launch:**
```bash
python controller_chart_editor.py notes.chart
```

**Or from GUI:**
```bash
python chart_maker_gui.py
→ Click "Edit Existing Chart"
```

---

**Happy Charting! 🎸🎮**
