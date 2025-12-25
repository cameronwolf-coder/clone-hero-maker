"""
Audio to MIDI Converter.

Two-stage pipeline:
1. Demucs (Meta) - Stem separation to isolate melody/vocals
2. Basic Pitch (Spotify) - Neural network audio-to-MIDI transcription

Falls back to librosa pYIN if dependencies not available.
"""

import numpy as np
from pathlib import Path
from typing import Optional, Tuple
import pretty_midi
import tempfile
import shutil


def check_demucs_available() -> bool:
    """Check if demucs is installed."""
    try:
        import demucs
        return True
    except ImportError:
        return False


def check_basic_pitch_available() -> bool:
    """Check if basic-pitch is installed."""
    try:
        from basic_pitch.inference import predict
        return True
    except ImportError:
        return False


def separate_stems_demucs(
    audio_path: str,
    output_dir: str,
    stem: str = 'vocals',  # 'vocals', 'drums', 'bass', 'other', 'guitar', 'piano'
    model: str = 'htdemucs_6s',  # Use 6-stem model by default
) -> Optional[str]:
    """
    Separate audio into stems using Demucs.

    Args:
        audio_path: Path to input audio file.
        output_dir: Directory to save separated stems.
        stem: Which stem to extract:
            - 4-stem model (htdemucs): 'vocals', 'drums', 'bass', 'other'
            - 6-stem model (htdemucs_6s): 'vocals', 'drums', 'bass', 'guitar', 'piano', 'other'
        model: Demucs model to use. Auto-selects based on stem if None.

    Returns:
        Path to the extracted stem file, or None if failed.
    """
    return separate_stems_demucs_api(audio_path, output_dir, stems=[stem], model=model).get(stem)


def separate_stems_demucs_api(
    audio_path: str,
    output_dir: str,
    stems: list = None,  # List of stems to extract, or None for all
    model: str = 'htdemucs_6s',
) -> dict:
    """
    Separate audio into stems using Demucs Python API directly.

    This avoids the subprocess/torchaudio.save() issue by using soundfile.

    Returns:
        Dict mapping stem name to file path.
    """
    try:
        import torch
        import soundfile as sf
        import librosa
        from demucs.pretrained import get_model
        from demucs.apply import apply_model

        print(f"Loading Demucs model {model}...")
        demucs_model = get_model(model)
        demucs_model.eval()

        # Use CPU if no CUDA, or MPS on Apple Silicon
        if torch.cuda.is_available():
            device = torch.device('cuda')
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device = torch.device('mps')
        else:
            device = torch.device('cpu')

        demucs_model.to(device)

        # Get the sample rate the model expects
        target_sr = demucs_model.samplerate

        print(f"Loading audio from {audio_path}...")
        # Load audio using librosa (more reliable than demucs AudioFile)
        # Load as mono first, then duplicate to stereo
        y, sr = librosa.load(audio_path, sr=target_sr, mono=False)

        # Ensure stereo
        if y.ndim == 1:
            y = np.stack([y, y])  # Mono to stereo
        elif y.shape[0] > 2:
            y = y[:2]  # Take first 2 channels

        # Convert to torch tensor: (channels, samples) -> (batch, channels, samples)
        wav = torch.from_numpy(y).float().unsqueeze(0).to(device)

        print("Running separation (this may take a few minutes)...")
        with torch.no_grad():
            sources = apply_model(demucs_model, wav, device=device)

        # sources shape: (batch, num_sources, channels, samples)
        sources = sources[0]  # Remove batch dimension

        # Get source names from model
        source_names = demucs_model.sources
        print(f"Separated sources: {source_names}")

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save each stem using soundfile (avoids torchaudio issue)
        result = {}
        sample_rate = demucs_model.samplerate

        if stems is None:
            stems = source_names

        for i, name in enumerate(source_names):
            if name not in stems:
                continue

            stem_path = output_path / f'{name}.wav'
            stem_audio = sources[i].cpu().numpy().T  # (samples, channels)

            print(f"  Saving {name} to {stem_path}...")
            sf.write(str(stem_path), stem_audio, sample_rate)
            result[name] = str(stem_path)

        return result

    except Exception as e:
        print(f"Demucs separation failed: {e}")
        import traceback
        traceback.print_exc()
        return {}


def convert_with_basic_pitch(
    audio_path: str,
    output_path: str,
    onset_threshold: float = 0.5,
    frame_threshold: float = 0.3,
    min_note_length: float = 50,  # ms
    min_freq: Optional[float] = None,
    max_freq: Optional[float] = None,
) -> dict:
    """
    Convert audio to MIDI using Spotify's Basic Pitch.

    Args:
        audio_path: Path to input audio file.
        output_path: Path to save MIDI file.
        onset_threshold: Threshold for note onset detection.
        frame_threshold: Threshold for frame-level detection.
        min_note_length: Minimum note length in ms.
        min_freq: Minimum frequency to detect (Hz).
        max_freq: Maximum frequency to detect (Hz).

    Returns:
        Dict with conversion stats.
    """
    from basic_pitch.inference import predict
    import basic_pitch

    # Use ONNX model explicitly (TF saved model doesn't work with TF 2.20+)
    onnx_model_path = Path(basic_pitch.__file__).parent / 'saved_models' / 'icassp_2022' / 'nmp.onnx'

    # Run Basic Pitch prediction
    model_output, midi_data, note_events = predict(
        audio_path,
        model_or_model_path=str(onnx_model_path),
        onset_threshold=onset_threshold,
        frame_threshold=frame_threshold,
        minimum_note_length=min_note_length,
        minimum_frequency=min_freq,
        maximum_frequency=max_freq,
    )

    # Save MIDI
    midi_data.write(output_path)

    # Calculate stats
    all_notes = []
    for instrument in midi_data.instruments:
        all_notes.extend(instrument.notes)

    if not all_notes:
        raise ValueError("No notes detected in audio")

    duration = max(n.end for n in all_notes) - min(n.start for n in all_notes)
    bpm = midi_data.estimate_tempo() if hasattr(midi_data, 'estimate_tempo') else 120.0

    return {
        'notes': len(all_notes),
        'duration': duration,
        'bpm': bpm,
        'pitch_range': (
            min(n.pitch for n in all_notes),
            max(n.pitch for n in all_notes)
        ),
        'method': 'basic_pitch',
    }


def load_audio(audio_path: str, sr: int = 22050) -> Tuple[np.ndarray, int]:
    """Load audio file and return samples and sample rate."""
    import librosa
    y, sr = librosa.load(audio_path, sr=sr, mono=True)
    return y, sr


def detect_pitch_pyin(
    y: np.ndarray,
    sr: int,
    fmin: float = 65.0,
    fmax: float = 2093.0,
    frame_length: int = 2048,
    hop_length: int = 512,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Detect pitch using pYIN algorithm."""
    import librosa

    f0, voiced_flag, voiced_probs = librosa.pyin(
        y,
        sr=sr,
        fmin=fmin,
        fmax=fmax,
        frame_length=frame_length,
        hop_length=hop_length,
    )

    times = librosa.times_like(f0, sr=sr, hop_length=hop_length)
    return times, f0, voiced_flag


def hz_to_midi(freq: float) -> int:
    """Convert frequency in Hz to MIDI note number."""
    if freq <= 0 or np.isnan(freq):
        return 0
    return int(round(69 + 12 * np.log2(freq / 440.0)))


def segment_notes(
    times: np.ndarray,
    frequencies: np.ndarray,
    voiced: np.ndarray,
    min_note_duration: float = 0.05,
    pitch_tolerance: int = 1,
) -> list[dict]:
    """Segment continuous pitch data into discrete notes."""
    notes = []
    current_note = None

    for i, (t, freq, is_voiced) in enumerate(zip(times, frequencies, voiced)):
        midi_pitch = hz_to_midi(freq) if is_voiced and not np.isnan(freq) else 0

        if midi_pitch > 0:
            if current_note is None:
                current_note = {
                    'start': t,
                    'pitch': midi_pitch,
                    'pitches': [midi_pitch],
                }
            elif abs(midi_pitch - current_note['pitch']) <= pitch_tolerance:
                current_note['pitches'].append(midi_pitch)
            else:
                current_note['end'] = t
                current_note['pitch'] = int(np.median(current_note['pitches']))
                if current_note['end'] - current_note['start'] >= min_note_duration:
                    notes.append(current_note)
                current_note = {
                    'start': t,
                    'pitch': midi_pitch,
                    'pitches': [midi_pitch],
                }
        else:
            if current_note is not None:
                current_note['end'] = t
                current_note['pitch'] = int(np.median(current_note['pitches']))
                if current_note['end'] - current_note['start'] >= min_note_duration:
                    notes.append(current_note)
                current_note = None

    if current_note is not None:
        current_note['end'] = times[-1]
        current_note['pitch'] = int(np.median(current_note['pitches']))
        if current_note['end'] - current_note['start'] >= min_note_duration:
            notes.append(current_note)

    return notes


def notes_to_midi(
    notes: list[dict],
    output_path: str,
    bpm: float = 120.0,
    instrument_name: str = 'Lead',
    velocity: int = 100,
) -> pretty_midi.PrettyMIDI:
    """Convert note list to MIDI file."""
    midi = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    instrument = pretty_midi.Instrument(program=80, name=instrument_name)

    for note_data in notes:
        note = pretty_midi.Note(
            velocity=velocity,
            pitch=note_data['pitch'],
            start=note_data['start'],
            end=note_data['end'],
        )
        instrument.notes.append(note)

    midi.instruments.append(instrument)
    midi.write(output_path)
    return midi


def detect_bpm(y: np.ndarray, sr: int) -> float:
    """Detect tempo/BPM from audio."""
    import librosa
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    if hasattr(tempo, '__len__'):
        tempo = float(tempo[0]) if len(tempo) > 0 else 120.0
    return float(tempo)


def convert_with_librosa(
    audio_path: str,
    output_path: str,
    bpm: Optional[float] = None,
    min_note_duration: float = 0.05,
    fmin: float = 80.0,
    fmax: float = 1000.0,
) -> dict:
    """Fallback conversion using librosa pYIN."""
    y, sr = load_audio(audio_path)

    if bpm is None:
        bpm = detect_bpm(y, sr)

    times, frequencies, voiced = detect_pitch_pyin(y, sr, fmin=fmin, fmax=fmax)
    notes = segment_notes(times, frequencies, voiced, min_note_duration=min_note_duration)

    if not notes:
        raise ValueError("No notes detected in audio")

    midi = notes_to_midi(notes, output_path, bpm=bpm)
    duration = notes[-1]['end'] - notes[0]['start'] if notes else 0

    return {
        'notes': len(notes),
        'duration': duration,
        'bpm': bpm,
        'pitch_range': (
            min(n['pitch'] for n in notes),
            max(n['pitch'] for n in notes)
        ),
        'method': 'librosa_pyin',
    }


def convert_audio_to_midi(
    audio_path: str,
    output_path: str,
    bpm: Optional[float] = None,
    min_note_duration: float = 0.05,
    fmin: float = 80.0,
    fmax: float = 1000.0,
    use_stem_separation: bool = True,
    stem_type: str = 'vocals',  # 'vocals' or 'other' (for instrumental melody)
) -> dict:
    """
    Convert an audio file to MIDI using the best available method.

    Pipeline priority:
    1. Demucs stem separation + Basic Pitch (best quality)
    2. Basic Pitch only (good quality)
    3. Librosa pYIN (fallback)

    Args:
        audio_path: Path to input audio file.
        output_path: Path to save MIDI file.
        bpm: Tempo (auto-detected if None).
        min_note_duration: Minimum note length in seconds.
        fmin: Minimum frequency to detect.
        fmax: Maximum frequency to detect.
        use_stem_separation: Whether to try stem separation first.
        stem_type: Which stem to extract ('vocals' or 'other').

    Returns:
        Dict with conversion stats.
    """
    has_demucs = check_demucs_available()
    has_basic_pitch = check_basic_pitch_available()

    audio_to_process = audio_path
    temp_dir = None

    try:
        # Stage 1: Stem separation with Demucs (if available)
        if use_stem_separation and has_demucs:
            print(f"Using Demucs to separate {stem_type} stem...")
            temp_dir = tempfile.mkdtemp(prefix='demucs_')

            stem_path = separate_stems_demucs(
                audio_path,
                temp_dir,
                stem=stem_type,
            )

            if stem_path:
                print(f"Stem separation successful: {stem_path}")
                audio_to_process = stem_path
            else:
                print("Stem separation failed, using original audio")

        # Stage 2: Audio-to-MIDI conversion
        if has_basic_pitch:
            print("Using Basic Pitch for audio-to-MIDI conversion...")
            try:
                stats = convert_with_basic_pitch(
                    audio_to_process,
                    output_path,
                    min_note_length=min_note_duration * 1000,  # Convert to ms
                    min_freq=fmin,
                    max_freq=fmax,
                )

                # Add stem info to stats
                if audio_to_process != audio_path:
                    stats['stem_separated'] = True
                    stats['stem_type'] = stem_type

                return stats

            except Exception as e:
                print(f"Basic Pitch failed: {e}, falling back to librosa")

        # Fallback: librosa pYIN
        print("Using librosa pYIN for audio-to-MIDI conversion...")
        stats = convert_with_librosa(
            audio_to_process,
            output_path,
            bpm=bpm,
            min_note_duration=min_note_duration,
            fmin=fmin,
            fmax=fmax,
        )

        if audio_to_process != audio_path:
            stats['stem_separated'] = True
            stats['stem_type'] = stem_type

        return stats

    finally:
        # Cleanup temp directory
        if temp_dir and Path(temp_dir).exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    import sys

    print("Audio-to-MIDI Converter")
    print(f"  Demucs available: {check_demucs_available()}")
    print(f"  Basic Pitch available: {check_basic_pitch_available()}")
    print()

    if len(sys.argv) < 3:
        print("Usage: python -m src.audio_to_midi input.mp3 output.mid [--vocals|--other]")
        sys.exit(1)

    audio_file = sys.argv[1]
    midi_file = sys.argv[2]
    stem_type = 'other'  # Default to instrumental melody

    if '--vocals' in sys.argv:
        stem_type = 'vocals'
    elif '--other' in sys.argv:
        stem_type = 'other'

    print(f"Converting {audio_file} to MIDI (stem: {stem_type})...")

    try:
        stats = convert_audio_to_midi(
            audio_file,
            midi_file,
            stem_type=stem_type,
        )
        print(f"\nSuccess!")
        print(f"  Method: {stats.get('method', 'unknown')}")
        print(f"  Stem separated: {stats.get('stem_separated', False)}")
        print(f"  Notes: {stats['notes']}")
        print(f"  Duration: {stats['duration']:.1f}s")
        print(f"  BPM: {stats['bpm']:.1f}")
        print(f"  Pitch range: {stats['pitch_range']}")
        print(f"  Output: {midi_file}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
