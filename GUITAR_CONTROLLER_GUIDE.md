# 🎮 Guitar Controller Guide

## Your Xbox 360 Xplorer is Detected! ✓

Your **Guitar Hero X-plorer** controller has been successfully detected with:
- 11 buttons
- 2 axes (whammy bar and tilt sensor)
- 1 D-pad

---

## 🎯 How to Create Charts with Your Controller

### Method 1: Using the AIO Launcher (Recommended)

1. **Launch the AIO Launcher:**
   ```bash
   python AIO_LAUNCHER.py
   ```

2. **Go to the "Guitar Recording" tab**

3. **Click "Detect Devices"** to see your controller

4. **Click "Launch Guitar Chart Maker"**

5. **Follow the prompts:**
   - Choose option [1] for Game Controller
   - Enter song name and artist
   - Enter BPM (beats per minute)
   - Press buttons to map them (or use default Xplorer mapping)
   - Play your performance!
   - Press START button when done

### Method 2: Direct Launch

```bash
python guitar_chart_maker.py
```

---

## 🎸 Button Mapping

### Default Xbox 360 Xplorer Mapping:

| Controller Button | Clone Hero Fret | Color  |
|-------------------|-----------------|--------|
| A Button (0)      | Fret 0          | GREEN  |
| B Button (1)      | Fret 1          | RED    |
| X Button (2)      | Fret 2          | YELLOW |
| Y Button (3)      | Fret 3          | BLUE   |
| LB/Left Bumper (4)| Fret 4          | ORANGE |
| START Button (7)  | Stop Recording  | -      |

### Custom Mapping:

If your controller uses different buttons, you can create a custom mapping:
- When prompted, choose "No" for default mapping
- The tool will ask you to press each fret button in order
- Press: GREEN → RED → YELLOW → BLUE → ORANGE

---

## 📝 Recording Tips

### For Best Results:

1. **Know Your BPM:**
   - Use a metronome or BPM counter
   - Common tempos: 120 BPM (medium), 140 BPM (fast), 90 BPM (slow)
   - You can use online BPM detectors for existing songs

2. **Practice First:**
   - The tool captures exactly what you play
   - Practice your performance before recording

3. **Hold for Sustains:**
   - Hold buttons down for sustained notes
   - The tool automatically calculates sustain length

4. **Use the Strumming:**
   - While the current version captures button presses
   - Future updates may include strum bar detection

5. **Stop Recording:**
   - Press the START button to stop
   - Or let it run for the full duration

---

## 🔧 Troubleshooting

### Controller Not Detected:

**Windows:**
1. Check if controller shows up in "Devices and Printers"
2. Try a different USB port
3. Reinstall Xbox 360 controller drivers
4. Restart Python and try again

**Detection Command:**
```bash
python controller_capture.py
```
This will show if your controller is detected.

### Wrong Button Mapping:

If the buttons don't match your controller:
1. Use custom mapping mode
2. Or edit the mapping in `controller_capture.py`:
   ```python
   def get_guitar_button_mapping(self):
       return {
           0: GuitarButton.GREEN,    # Change these numbers
           1: GuitarButton.RED,      # to match your controller
           # ... etc
       }
   ```

### Notes Not Recording:

- Make sure you're holding buttons long enough (at least 0.1 seconds)
- Check that START button isn't being accidentally pressed
- Try the interactive test: `python controller_capture.py`

---

## 🎵 Complete Workflow Example

### Creating a Chart from Your Xplorer:

```bash
# 1. Launch the guitar chart maker
python guitar_chart_maker.py

# 2. When prompted:
#    - Choose [1] Game Controller
#    - Song name: "Through the Fire and Flames"
#    - Artist: "DragonForce"
#    - BPM: 200
#    - Use default mapping: y

# 3. Press Enter to start recording

# 4. Play your performance on the controller

# 5. Press START button when done

# 6. Chart saved as "Through_the_Fire_and_Flames.chart"
```

### What You Get:

- `song_name.chart` file with your performance
- Properly timed notes based on BPM
- Sustain lengths from button holds
- Ready for Clone Hero!

---

## 📁 Adding to Clone Hero

1. **Create song folder:**
   ```
   Clone Hero/Songs/MyCustomChart/
   ```

2. **Add your files:**
   ```
   MyCustomChart/
   ├── notes.chart          (your generated chart)
   ├── song.ogg             (audio file)
   └── song.ini             (metadata)
   ```

3. **Create song.ini:**
   ```ini
   [song]
   name = Your Song Name
   artist = Artist Name
   charter = YourName
   album = Album Name
   year = 2024
   genre = rock
   ```

4. **Launch Clone Hero and play!**

---

## 🚀 Advanced Features

### Multiple Difficulties:

Currently generates Expert difficulty. For other difficulties:
1. Record different performances
2. Edit the chart file manually
3. Use the Visual Editor (`python visual_editor.py`)

### Editing Your Chart:

After recording, you can refine it:

**Visual Editor:**
```bash
python visual_editor.py
```
- Load your chart
- Click to add/remove notes
- Save changes

**Web Editor:**
- Launch web app: `python app.py`
- Upload your chart
- Edit in browser

---

## 💡 Tips from Experience

### Recording Guitar Hero Songs:

1. **Start Simple:** Try slower songs first (90-110 BPM)
2. **Use a Reference:** Play along with the actual song
3. **Sync to Metronome:** Keep steady timing
4. **Multiple Takes:** Record multiple times, pick the best

### Common BPM Ranges:

- **Slow/Ballads:** 60-90 BPM
- **Medium Rock:** 100-130 BPM
- **Fast Rock:** 140-180 BPM
- **Speed Metal:** 180-240 BPM

### Button Press Duration:

- **Tap notes:** Quick press/release (< 0.2 seconds)
- **Short sustains:** 0.5-1 second holds
- **Long sustains:** 2+ seconds

---

## 📊 Technical Details

### How It Works:

1. **pygame** detects your controller as a joystick
2. Monitors button presses in real-time
3. Records timestamps for note-on and note-off
4. Converts time to Clone Hero ticks based on BPM
5. Calculates sustain lengths
6. Generates standard .chart format

### Timing Accuracy:

- Poll rate: ~100 Hz (10ms accuracy)
- Tick resolution: 192 ticks per quarter note
- Sustain precision: ±1 tick

---

## 🎉 You're Ready!

Your Xbox 360 Xplorer controller is ready to create Clone Hero charts!

**Quick Start:**
```bash
python AIO_LAUNCHER.py
```
→ Guitar Recording tab → Detect Devices → Launch Guitar Chart Maker

**Have fun charting! 🎸**
