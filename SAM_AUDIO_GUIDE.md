# 🎵 SAM Audio Integration Guide

## What is SAM Audio?

**SAM Audio** is Meta's cutting-edge foundation model for sound isolation. Unlike Demucs (which separates music into 4-6 preset stems), SAM Audio can isolate **any sound** using text descriptions.

### SAM Audio vs Demucs

| Feature | Demucs | SAM Audio |
|---------|--------|-----------|
| **Type** | Music source separation | Universal sound isolation |
| **Input** | Audio file only | Audio + text description |
| **Output** | Fixed stems (vocals, drums, bass, other) | Any sound matching description |
| **Use Case** | Standard music separation | Specific instrument isolation |
| **Setup** | Simple `pip install` | GitHub install + HuggingFace auth |
| **Examples** | "vocals", "drums" | "electric guitar solo", "bass guitar riff", "snare drum" |

### Why Use SAM Audio for Clone Hero?

**More Precise Instrument Isolation:**
- "Lead guitar playing melody" vs just "other instruments"
- "Rhythm guitar playing chords"
- "Bass guitar playing root notes"
- "Electric guitar with distortion"
- "Acoustic guitar fingerpicking"

**Better Chart Quality:**
- Isolate specific guitar parts from complex mixes
- Separate lead from rhythm guitars
- Extract bass lines more accurately
- Focus on specific time ranges

---

## Installation

SAM Audio requires several steps:

### 1. Install from GitHub

```bash
# Clone the repository
cd C:\Users\camer
git clone https://github.com/facebookresearch/sam-audio.git

# Install
cd sam-audio
pip install -e .
```

**Note:** This will take 10-15 minutes and install many dependencies including:
- dacvae (audio codec)
- ImageBind (multimodal AI)
- CLAP (audio-text matching)
- perception-models
- Various other Meta research tools

### 2. Authenticate with Hugging Face

```bash
# Install Hugging Face CLI if not already installed
pip install huggingface-hub

# Login (you'll need a Hugging Face account)
huggingface-cli login
```

### 3. Request Model Access

1. Go to: https://huggingface.co/facebook/sam-audio-large
2. Click "Request Access"
3. Wait for approval (usually within a few hours)

### 4. Verify Installation

```bash
cd C:\Users\camer\CloneHeroChartMaker
python sam_audio_separator.py --help
```

---

## Usage

### Basic Usage - Command Line

Once installed, you can use the included `sam_audio_separator.py`:

```bash
# Isolate a guitar from an audio file
python sam_audio_separator.py song.mp3 -d "An electric guitar playing"

# Isolate bass guitar
python sam_audio_separator.py song.mp3 -d "A bass guitar" -o bass_output

# Multiple instruments at once (presets)
python sam_audio_separator.py song.mp3 --presets
```

### Text Descriptions

The quality of isolation depends on your description. Here are effective descriptions for Clone Hero:

**Guitar Parts:**
```
"An electric guitar playing"
"A lead guitar solo"
"A rhythm guitar playing chords"
"An acoustic guitar"
"A distorted electric guitar"
"A clean electric guitar"
```

**Bass:**
```
"A bass guitar"
"An electric bass guitar"
"A bass line"
```

**Drums:**
```
"A drum kit"
"A snare drum"
"A kick drum"
"Cymbals"
```

**Other:**
```
"A person singing"
"A keyboard playing"
"A synthesizer"
```

### Advanced Usage - Python Code

```python
from sam_audio_separator import SAMAudioSeparator

# Initialize
separator = SAMAudioSeparator(model_size="large")

# Check if available
if separator.available:
    # Isolate guitar
    outputs = separator.separate(
        audio_file="song.mp3",
        description="An electric guitar solo",
        output_dir="guitar_isolated"
    )

    print(f"Isolated guitar: {outputs['target']}")
    print(f"Everything else: {outputs['residual']}")

    # Now convert the isolated guitar to MIDI
    # ... use with your existing audio_to_midi pipeline
```

### Integration with Clone Hero Chart Maker

**Workflow with SAM Audio:**

1. **Isolate specific instrument:**
   ```bash
   python sam_audio_separator.py song.mp3 -d "A lead guitar" -o lead_guitar
   ```

2. **Convert isolated audio to chart:**
   - Use the web app (http://localhost:8080)
   - Upload `lead_guitar/target.wav`
   - Skip stem separation (already isolated!)
   - Convert to MIDI and chart

3. **Result:** Ultra-precise chart of just the lead guitar part!

---

## Model Sizes

SAM Audio comes in three sizes:

| Size | Parameters | Speed | Quality | VRAM | Recommendation |
|------|------------|-------|---------|------|----------------|
| **small** | ~100M | Fast | Good | 4GB | Quick testing |
| **base** | ~300M | Medium | Better | 8GB | Balanced |
| **large** | ~600M | Slow | Best | 12GB | **Recommended** |

**For Clone Hero charts:** Use "large" for best quality isolation.

---

## Performance Tips

### GPU is Highly Recommended

SAM Audio works on CPU but is **much slower**. On GPU:
- Small model: ~10 seconds per 3-minute song
- Large model: ~30 seconds per 3-minute song

On CPU (not recommended):
- Small model: ~5 minutes per song
- Large model: ~15+ minutes per song

### First Run

The first time you use SAM Audio, it will:
1. Download the model weights (~1-2GB depending on size)
2. Cache them locally
3. Subsequent runs are much faster

---

## Comparison Example

**Demucs Output:**
```
song.mp3 → vocals.wav, drums.wav, bass.wav, other.wav
```
- Guitar is mixed with keyboards, synths in "other.wav"
- Hard to separate lead from rhythm guitar

**SAM Audio Output:**
```
song.mp3 + "lead guitar solo" → lead_guitar.wav (ONLY lead guitar!)
song.mp3 + "rhythm guitar chords" → rhythm_guitar.wav
```
- Each part isolated precisely
- Better for creating accurate charts

---

## Troubleshooting

### "SAM Audio not available"

**Cause:** Package not installed
**Fix:** Run installation steps above

### "Failed to load SAM Audio: No module named 'sam_audio'"

**Cause:** Not installed or not in Python path
**Fix:**
```bash
cd C:\Users\camer\sam-audio
pip install -e .
```

### "Authentication required"

**Cause:** Not logged into Hugging Face
**Fix:**
```bash
huggingface-cli login
```

### "Access denied to model"

**Cause:** Haven't requested access
**Fix:** Visit https://huggingface.co/facebook/sam-audio-large and request access

### "Out of memory"

**Cause:** Not enough VRAM for large model
**Fix:** Use smaller model:
```python
separator = SAMAudioSeparator(model_size="base")  # or "small"
```

---

## Current Setup

**Your system currently has:**
- ✅ Demucs installed (working now!)
- ✅ Basic Pitch installed
- ✅ PyTorch installed
- ⏳ SAM Audio (optional - install when ready)

**Recommendation:**
- Start with Demucs for quick, standard separation
- Install SAM Audio later when you need:
  - Very specific instrument isolation
  - Separation of lead vs rhythm guitar
  - Higher precision for complex songs

---

## Installation Script

Save this as `install_sam_audio.bat`:

```batch
@echo off
echo Installing SAM Audio...
echo This will take 10-15 minutes

cd C:\Users\camer

echo [1/4] Cloning repository...
git clone https://github.com/facebookresearch/sam-audio.git

echo [2/4] Installing package...
cd sam-audio
pip install -e .

echo [3/4] Installing Hugging Face CLI...
pip install huggingface-hub

echo [4/4] Setup complete!
echo.
echo Next steps:
echo   1. Run: huggingface-cli login
echo   2. Visit: https://huggingface.co/facebook/sam-audio-large
echo   3. Request access to the model
echo.
pause
```

---

## Future Integration

In a future update, the web app could offer both options:

**Audio Separation UI:**
```
Choose separation method:
○ Demucs (Fast, 4-stem standard separation)
○ SAM Audio (Slow, text-prompted isolation)

[If SAM Audio selected:]
Describe the sound to isolate:
[An electric guitar solo          ]

Advanced options:
☐ Predict time spans
☐ Enable re-ranking
```

---

## Summary

- **Demucs:** Quick, easy, good for most cases ✅ Already working!
- **SAM Audio:** Advanced, precise, for specific needs ⏳ Optional upgrade

**When to use SAM Audio:**
- Complex songs with multiple guitars
- Need to separate lead from rhythm
- Want highest precision isolation
- Have GPU and time for processing

**Stick with Demucs when:**
- Standard 4-stem separation is enough
- Want fast processing
- Don't need ultra-specific isolation

---

## Resources

- **SAM Audio GitHub:** https://github.com/facebookresearch/sam-audio
- **Model on HuggingFace:** https://huggingface.co/facebook/sam-audio-large
- **Meta AI Page:** https://ai.meta.com/samaudio/

---

**Your Clone Hero Chart Maker now supports the world's most advanced audio separation! 🎸**
