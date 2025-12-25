"""
Flask web app for Clone Hero Converter.

Provides a web interface for:
- Uploading MIDI files
- Downloading audio from YouTube URLs
- Converting to .chart format
"""

import os
import uuid
import tempfile
import shutil
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, url_for

from src.parse_midi import extract_lead_notes, inspect_midi
from src.map_to_frets import (
    map_pitches_to_lanes,
    create_mapped_notes,
    summarize_qa_issues,
    preview_lanes_ascii,
)
from src.chart_writer import write_chart, ChartMetadata
from src.cli import load_config
from src.audio_to_midi import (
    convert_audio_to_midi,
    check_demucs_available,
    check_basic_pitch_available,
    separate_stems_demucs,
    separate_stems_demucs_api,
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload
app.config['UPLOAD_FOLDER'] = Path(__file__).parent / 'uploads'
app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)

# Store conversion jobs
jobs = {}


def reduce_note_density(midi_data, max_notes_per_second=5):
    """
    Reduce note density to make charts playable.

    Keeps the most prominent notes while removing dense clusters.
    Clone Hero charts typically have 2-8 notes per second for playability.
    """
    import pretty_midi

    for instrument in midi_data.instruments:
        if not instrument.notes:
            continue

        # Sort notes by start time
        notes = sorted(instrument.notes, key=lambda n: n.start)

        # Group notes into time windows (e.g., 200ms windows)
        window_size = 1.0 / max_notes_per_second  # seconds per note max

        filtered_notes = []
        last_note_time = -window_size

        for note in notes:
            # Keep note if enough time has passed since last note
            if note.start >= last_note_time + window_size:
                filtered_notes.append(note)
                last_note_time = note.start
            # Or if it's a significantly different pitch (chord/melody change)
            elif filtered_notes and abs(note.pitch - filtered_notes[-1].pitch) >= 5:
                # Allow chord notes that are different enough
                if note.start >= last_note_time + (window_size * 0.3):
                    filtered_notes.append(note)
                    last_note_time = note.start

        instrument.notes = filtered_notes

    return midi_data


def get_job_folder(job_id: str) -> Path:
    """Get or create folder for a conversion job."""
    folder = app.config['UPLOAD_FOLDER'] / job_id
    folder.mkdir(exist_ok=True)
    return folder


def cleanup_old_jobs():
    """Remove jobs older than 1 hour."""
    import time
    cutoff = time.time() - 3600
    for folder in app.config['UPLOAD_FOLDER'].iterdir():
        if folder.is_dir():
            try:
                if folder.stat().st_mtime < cutoff:
                    shutil.rmtree(folder)
            except Exception:
                pass


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/api/capabilities')
def get_capabilities():
    """Report available conversion capabilities."""
    has_demucs = check_demucs_available()
    has_basic_pitch = check_basic_pitch_available()

    return jsonify({
        'demucs_available': has_demucs,
        'basic_pitch_available': has_basic_pitch,
        'best_method': (
            'demucs+basic_pitch' if has_demucs and has_basic_pitch else
            'basic_pitch' if has_basic_pitch else
            'librosa_pyin'
        ),
        'stem_separation': has_demucs,
    })


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle MIDI or audio file upload."""
    cleanup_old_jobs()

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Check file extension
    ext = Path(file.filename).suffix.lower()
    midi_exts = ['.mid', '.midi']
    audio_exts = ['.mp3', '.m4a', '.wav', '.ogg', '.flac', '.webm', '.opus']

    if ext not in midi_exts + audio_exts:
        return jsonify({'error': 'File must be MIDI (.mid) or audio (.mp3, .m4a, .wav, .ogg)'}), 400

    # Create job
    job_id = str(uuid.uuid4())[:8]
    job_folder = get_job_folder(job_id)

    try:
        if ext in midi_exts:
            # Direct MIDI upload
            midi_path = job_folder / 'input.mid'
            file.save(midi_path)
        else:
            # Audio upload - convert to MIDI
            audio_path = job_folder / f'audio{ext}'
            file.save(audio_path)

            # Get stem type from form data (default to 'other' for lead melody)
            stem_type = request.form.get('stem_type', 'other')
            use_stem_separation = bool(stem_type)  # Empty string means no separation

            midi_path = job_folder / 'converted.mid'
            midi_stats = convert_audio_to_midi(
                str(audio_path),
                str(midi_path),
                min_note_duration=0.08,
                use_stem_separation=use_stem_separation,
                stem_type=stem_type or 'other',
            )

            jobs[job_id] = {
                'audio_path': str(audio_path),
                'midi_stats': midi_stats,
            }

        # Inspect MIDI
        info = inspect_midi(str(midi_path))
        tracks = [
            {
                'index': t['index'],
                'name': t['name'],
                'note_count': t['note_on_count'],
                'has_tempo': t['has_tempo'],
                'bpm': t['tempo_bpm'],
            }
            for t in info['tracks']
            if t['note_on_count'] > 0
        ]

        jobs[job_id] = jobs.get(job_id, {})
        jobs[job_id].update({
            'midi_path': str(midi_path),
            'original_name': Path(file.filename).stem,
            'tracks': tracks,
            'ticks_per_beat': info['ticks_per_beat'],
        })

        response_data = {
            'job_id': job_id,
            'filename': file.filename,
            'tracks': tracks,
            'ticks_per_beat': info['ticks_per_beat'],
        }

        # Add conversion stats if audio was converted
        if 'midi_stats' in jobs[job_id]:
            stats = jobs[job_id]['midi_stats']
            response_data['midi_stats'] = {
                'notes': stats['notes'],
                'duration': round(stats['duration'], 1),
                'bpm': round(stats['bpm'], 1),
                'method': stats.get('method', 'unknown'),
                'stem_separated': stats.get('stem_separated', False),
                'stem_type': stats.get('stem_type'),
            }
            response_data['converted_from_audio'] = True

        return jsonify(response_data)
    except Exception as e:
        shutil.rmtree(job_folder, ignore_errors=True)
        return jsonify({'error': f'Failed to process file: {str(e)}'}), 400


@app.route('/api/youtube', methods=['POST'])
def download_youtube():
    """Download audio from YouTube URL."""
    cleanup_old_jobs()

    data = request.get_json()
    url = data.get('url', '').strip()
    stem_type = data.get('stem_type', 'other')
    use_stem_separation = bool(stem_type)  # Empty string means no separation

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    # Create job
    job_id = str(uuid.uuid4())[:8]
    job_folder = get_job_folder(job_id)

    try:
        import yt_dlp

        # Download audio (no ffmpeg required - download as-is)
        audio_path = job_folder / 'audio.%(ext)s'
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio',
            'outtmpl': str(audio_path),
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Unknown')
            artist = info.get('uploader', 'Unknown')

        # Find the downloaded file
        audio_file = None
        for f in job_folder.iterdir():
            if f.suffix in ['.mp3', '.m4a', '.webm', '.opus', '.wav', '.ogg']:
                audio_file = f
                break

        if not audio_file:
            return jsonify({'error': 'Audio download failed'}), 500

        # Convert audio to MIDI using AI pipeline
        midi_path = job_folder / 'converted.mid'
        try:
            midi_stats = convert_audio_to_midi(
                str(audio_file),
                str(midi_path),
                min_note_duration=0.08,  # 80ms minimum note
                use_stem_separation=use_stem_separation,
                stem_type=stem_type or 'other',
            )
        except Exception as e:
            return jsonify({'error': f'Audio to MIDI conversion failed: {str(e)}'}), 500

        # Inspect the generated MIDI
        info = inspect_midi(str(midi_path))
        tracks = [
            {
                'index': t['index'],
                'name': t['name'],
                'note_count': t['note_on_count'],
            }
            for t in info['tracks']
            if t['note_on_count'] > 0
        ]

        jobs[job_id] = {
            'audio_path': str(audio_file),
            'midi_path': str(midi_path),
            'original_name': title,
            'artist': artist,
            'source': 'youtube',
            'tracks': tracks,
            'midi_stats': midi_stats,
        }

        return jsonify({
            'job_id': job_id,
            'title': title,
            'artist': artist,
            'tracks': tracks,
            'midi_stats': {
                'notes': midi_stats['notes'],
                'duration': round(midi_stats['duration'], 1),
                'bpm': round(midi_stats['bpm'], 1),
                'method': midi_stats.get('method', 'unknown'),
                'stem_separated': midi_stats.get('stem_separated', False),
                'stem_type': midi_stats.get('stem_type'),
            },
            'message': 'Audio downloaded and converted to MIDI!',
        })
    except Exception as e:
        shutil.rmtree(job_folder, ignore_errors=True)
        return jsonify({'error': f'YouTube download failed: {str(e)}'}), 400


@app.route('/api/youtube/download', methods=['POST'])
def download_youtube_audio_only():
    """Download audio from YouTube URL without converting to MIDI."""
    cleanup_old_jobs()

    data = request.get_json()
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    # Create job
    job_id = str(uuid.uuid4())[:8]
    job_folder = get_job_folder(job_id)

    try:
        import yt_dlp

        # Download audio
        audio_path = job_folder / 'audio.%(ext)s'
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio',
            'outtmpl': str(audio_path),
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Unknown')
            artist = info.get('uploader', 'Unknown')

        # Find the downloaded file
        audio_file = None
        for f in job_folder.iterdir():
            if f.suffix in ['.mp3', '.m4a', '.webm', '.opus', '.wav', '.ogg']:
                audio_file = f
                break

        if not audio_file:
            return jsonify({'error': 'Audio download failed'}), 500

        jobs[job_id] = {
            'audio_path': str(audio_file),
            'original_name': title,
            'artist': artist,
            'source': 'youtube',
        }

        return jsonify({
            'job_id': job_id,
            'title': title,
            'artist': artist,
            'audio_url': url_for('get_audio', job_id=job_id),
            'message': 'Audio downloaded! Now you can preview stem separation.',
        })
    except Exception as e:
        shutil.rmtree(job_folder, ignore_errors=True)
        return jsonify({'error': f'YouTube download failed: {str(e)}'}), 400


@app.route('/api/separate-all', methods=['POST'])
def separate_all_stems():
    """
    Separate ALL stems from audio and convert each to MIDI.

    This endpoint:
    1. Downloads audio (YouTube URL) or uses uploaded file
    2. Separates all stems using Demucs 6-stem model
    3. Converts each stem to MIDI
    4. Returns all stems with note counts for user selection
    """
    cleanup_old_jobs()

    if not check_demucs_available():
        return jsonify({'error': 'Demucs not installed. Run: pip install demucs'}), 400

    if not check_basic_pitch_available():
        return jsonify({'error': 'Basic Pitch not installed. Run: pip install basic-pitch'}), 400

    data = request.get_json() or {}
    url = data.get('url', '').strip()
    job_id = data.get('job_id')  # If continuing from existing job

    # Create or get job
    if job_id and job_id in jobs:
        job = jobs[job_id]
        job_folder = get_job_folder(job_id)
        audio_file = Path(job['audio_path'])
        title = job.get('original_name', 'Unknown')
        artist = job.get('artist', 'Unknown')
    elif url:
        # Download from YouTube
        job_id = str(uuid.uuid4())[:8]
        job_folder = get_job_folder(job_id)

        try:
            import yt_dlp

            audio_path = job_folder / 'audio.%(ext)s'
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio',
                'outtmpl': str(audio_path),
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Unknown')
                artist = info.get('uploader', 'Unknown')

            # Find the downloaded file
            audio_file = None
            for f in job_folder.iterdir():
                if f.suffix in ['.mp3', '.m4a', '.webm', '.opus', '.wav', '.ogg']:
                    audio_file = f
                    break

            if not audio_file:
                return jsonify({'error': 'Audio download failed'}), 500

            jobs[job_id] = {
                'audio_path': str(audio_file),
                'original_name': title,
                'artist': artist,
                'source': 'youtube',
            }
            job = jobs[job_id]

        except Exception as e:
            shutil.rmtree(job_folder, ignore_errors=True)
            return jsonify({'error': f'YouTube download failed: {str(e)}'}), 400
    else:
        return jsonify({'error': 'No URL or job_id provided'}), 400

    # Separate ALL stems using 6-stem model via Python API
    all_stems = ['vocals', 'drums', 'bass', 'guitar', 'piano', 'other']
    stem_results = []

    try:
        # Use the new API-based separation that uses soundfile for saving
        stems_dir = job_folder / 'stems'
        stems_dir.mkdir(exist_ok=True)

        print(f"Running Demucs 6-stem separation on {audio_file}...")
        separated_stems = separate_stems_demucs_api(
            str(audio_file),
            str(stems_dir),
            stems=None,  # All stems
            model='htdemucs_6s',
        )

        if not separated_stems:
            return jsonify({'error': 'Stem separation failed - no stems produced'}), 500

        print(f"Separated stems: {list(separated_stems.keys())}")

        # Detect BPM from the original audio
        detected_bpm = 120  # Default fallback
        try:
            import librosa
            y, sr = librosa.load(str(audio_file), sr=22050, mono=True, duration=60)  # First 60 seconds
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            if hasattr(tempo, '__len__'):
                detected_bpm = float(tempo[0]) if len(tempo) > 0 else 120.0
            else:
                detected_bpm = float(tempo)
            print(f"Detected BPM: {detected_bpm:.1f}")
        except Exception as e:
            print(f"BPM detection failed: {e}, using default 120")

        # Store BPM in job
        job['detected_bpm'] = detected_bpm

        for stem in all_stems:
            stem_path = stems_dir / f'{stem}.wav'
            if not stem_path.exists():
                print(f"Stem not found: {stem_path}")
                continue

            # Convert stem to MIDI
            midi_path = job_folder / f'{stem}.mid'
            try:
                from basic_pitch.inference import predict
                import basic_pitch

                # Use ONNX model explicitly (TF saved model doesn't work with TF 2.20+)
                onnx_model_path = Path(basic_pitch.__file__).parent / 'saved_models' / 'icassp_2022' / 'nmp.onnx'

                # Higher thresholds = fewer notes detected (more conservative)
                model_output, midi_data, note_events = predict(
                    str(stem_path),
                    model_or_model_path=str(onnx_model_path),
                    onset_threshold=0.6,  # Higher = fewer note onsets (was 0.5)
                    frame_threshold=0.5,  # Higher = need stronger signal (was 0.3)
                    minimum_note_length=120,  # Longer minimum note (was 80ms)
                )

                # Reduce notes to make chart playable (max ~4-6 notes per second)
                midi_data = reduce_note_density(midi_data, max_notes_per_second=5)

                midi_data.write(str(midi_path))

                # Count notes
                note_count = sum(len(inst.notes) for inst in midi_data.instruments)

                # Get duration
                all_notes = []
                for inst in midi_data.instruments:
                    all_notes.extend(inst.notes)

                duration = max(n.end for n in all_notes) - min(n.start for n in all_notes) if all_notes else 0

                stem_results.append({
                    'stem': stem,
                    'stem_path': str(stem_path),
                    'midi_path': str(midi_path),
                    'note_count': note_count,
                    'duration': round(duration, 1),
                    'audio_url': url_for('get_stem_audio', job_id=job_id, stem=stem),
                })

                print(f"  {stem}: {note_count} notes")

            except Exception as e:
                print(f"Failed to convert {stem} to MIDI: {e}")
                stem_results.append({
                    'stem': stem,
                    'stem_path': str(stem_path),
                    'midi_path': None,
                    'note_count': 0,
                    'error': str(e),
                    'audio_url': url_for('get_stem_audio', job_id=job_id, stem=stem),
                })

        # Store results in job
        job['stems'] = {s['stem']: s for s in stem_results}
        job['separation_complete'] = True

        # Sort by note count (most notes first, excluding drums typically)
        stem_results.sort(key=lambda x: x['note_count'], reverse=True)

        return jsonify({
            'job_id': job_id,
            'title': title,
            'artist': artist,
            'stems': stem_results,
            'message': 'All stems separated and converted to MIDI!',
        })

    except Exception as e:
        return jsonify({'error': f'Separation failed: {str(e)}'}), 500


@app.route('/api/stem-audio/<job_id>/<stem>')
def get_stem_audio(job_id, stem):
    """Stream a specific separated stem audio for preview."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    if 'stems' not in job or stem not in job['stems']:
        return jsonify({'error': f'Stem {stem} not found'}), 404

    stem_info = job['stems'][stem]
    stem_path = Path(stem_info['stem_path'])

    if not stem_path.exists():
        return jsonify({'error': 'Stem file not found'}), 404

    return send_file(stem_path, mimetype='audio/wav')


@app.route('/api/select-stem/<job_id>', methods=['POST'])
def select_stem_for_chart(job_id):
    """Select which stem's MIDI to use for the chart."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    if 'stems' not in job:
        return jsonify({'error': 'No stems available - run separation first'}), 400

    data = request.get_json() or {}
    stem = data.get('stem')

    if not stem or stem not in job['stems']:
        return jsonify({'error': f'Invalid stem: {stem}'}), 400

    stem_info = job['stems'][stem]
    if not stem_info.get('midi_path'):
        return jsonify({'error': f'No MIDI available for {stem}'}), 400

    # Copy the selected stem's MIDI as the main MIDI
    midi_path = Path(stem_info['midi_path'])
    main_midi_path = get_job_folder(job_id) / 'converted.mid'
    shutil.copy(midi_path, main_midi_path)

    # Inspect the MIDI
    info = inspect_midi(str(main_midi_path))
    tracks = [
        {
            'index': t['index'],
            'name': t['name'],
            'note_count': t['note_on_count'],
        }
        for t in info['tracks']
        if t['note_on_count'] > 0
    ]

    # Update job
    detected_bpm = job.get('detected_bpm', 120)
    job['midi_path'] = str(main_midi_path)
    job['tracks'] = tracks
    job['selected_stem'] = stem
    job['bpm'] = detected_bpm  # Set bpm for chart-data endpoint
    job['midi_stats'] = {
        'notes': stem_info['note_count'],
        'duration': stem_info['duration'],
        'bpm': detected_bpm,
        'method': 'basic_pitch',
        'stem_separated': True,
        'stem_type': stem,
    }

    return jsonify({
        'job_id': job_id,
        'stem': stem,
        'tracks': tracks,
        'midi_stats': job['midi_stats'],
        'message': f'Selected {stem} stem for chart!',
    })


@app.route('/api/youtube/<job_id>/separate', methods=['POST'])
def separate_youtube_stem(job_id):
    """Separate a stem from downloaded YouTube audio for preview."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    if not check_demucs_available():
        return jsonify({'error': 'Demucs not installed. Run: pip install demucs'}), 400

    job = jobs[job_id]
    if 'audio_path' not in job:
        return jsonify({'error': 'No audio available'}), 400

    data = request.get_json() or {}
    stem_type = data.get('stem_type', 'other')

    if not stem_type:
        return jsonify({'error': 'No stem type specified'}), 400

    job_folder = get_job_folder(job_id)

    try:
        # Run stem separation
        stem_path = separate_stems_demucs(
            job['audio_path'],
            str(job_folder),
            stem=stem_type,
        )

        if not stem_path:
            return jsonify({'error': f'Stem separation failed for {stem_type}'}), 500

        # Update job info
        job['stem_path'] = stem_path
        job['stem_type'] = stem_type

        return jsonify({
            'job_id': job_id,
            'stem_type': stem_type,
            'stem_url': url_for('get_separated_stem', job_id=job_id),
            'original_url': url_for('get_audio', job_id=job_id),
            'message': f'Successfully separated {stem_type} stem!',
        })

    except Exception as e:
        return jsonify({'error': f'Stem separation failed: {str(e)}'}), 500


@app.route('/api/youtube/<job_id>/convert', methods=['POST'])
def convert_youtube_to_midi(job_id):
    """Convert YouTube audio (or separated stem) to MIDI."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    data = request.get_json() or {}
    use_stem = data.get('use_stem', False)
    stem_type = data.get('stem_type', 'other')

    job_folder = get_job_folder(job_id)

    try:
        # Decide which audio to use
        if use_stem and 'stem_path' in job:
            audio_to_convert = job['stem_path']
            # Don't run stem separation again
            use_stem_separation = False
        else:
            audio_to_convert = job['audio_path']
            # Run stem separation if requested
            use_stem_separation = bool(stem_type)

        midi_path = job_folder / 'converted.mid'
        midi_stats = convert_audio_to_midi(
            audio_to_convert,
            str(midi_path),
            min_note_duration=0.08,
            use_stem_separation=use_stem_separation,
            stem_type=stem_type or 'other',
        )

        # Inspect the generated MIDI
        info = inspect_midi(str(midi_path))
        tracks = [
            {
                'index': t['index'],
                'name': t['name'],
                'note_count': t['note_on_count'],
            }
            for t in info['tracks']
            if t['note_on_count'] > 0
        ]

        # Update job
        job['midi_path'] = str(midi_path)
        job['tracks'] = tracks
        job['midi_stats'] = midi_stats

        return jsonify({
            'job_id': job_id,
            'title': job.get('original_name', 'Unknown'),
            'artist': job.get('artist', 'Unknown'),
            'tracks': tracks,
            'midi_stats': {
                'notes': midi_stats['notes'],
                'duration': round(midi_stats['duration'], 1),
                'bpm': round(midi_stats['bpm'], 1),
                'method': midi_stats.get('method', 'unknown'),
                'stem_separated': midi_stats.get('stem_separated', False) or use_stem,
                'stem_type': job.get('stem_type') if use_stem else midi_stats.get('stem_type'),
            },
            'message': 'Audio converted to MIDI!',
        })

    except Exception as e:
        return jsonify({'error': f'Conversion failed: {str(e)}'}), 500


@app.route('/api/youtube/<job_id>/midi', methods=['POST'])
def upload_midi_for_youtube(job_id):
    """Upload MIDI for a YouTube job."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    ext = Path(file.filename).suffix.lower()
    if ext not in ['.mid', '.midi']:
        return jsonify({'error': 'File must be a MIDI file'}), 400

    job_folder = get_job_folder(job_id)
    midi_path = job_folder / 'input.mid'
    file.save(midi_path)

    try:
        info = inspect_midi(str(midi_path))
        tracks = [
            {
                'index': t['index'],
                'name': t['name'],
                'note_count': t['note_on_count'],
            }
            for t in info['tracks']
            if t['note_on_count'] > 0
        ]

        jobs[job_id]['midi_path'] = str(midi_path)
        jobs[job_id]['tracks'] = tracks

        return jsonify({
            'job_id': job_id,
            'tracks': tracks,
        })
    except Exception as e:
        return jsonify({'error': f'Failed to parse MIDI: {str(e)}'}), 400


@app.route('/api/convert/<job_id>', methods=['POST'])
def convert(job_id):
    """Convert MIDI to .chart."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    if 'midi_path' not in job:
        return jsonify({'error': 'No MIDI file uploaded'}), 400

    data = request.get_json() or {}
    track_index = data.get('track_index')
    song_name = data.get('name') or job.get('original_name', 'Unknown')
    artist = data.get('artist') or job.get('artist', 'Unknown')
    charter = data.get('charter', 'Clone Hero Converter')

    config = load_config()
    job_folder = get_job_folder(job_id)

    try:
        # Extract notes
        midi_data = extract_lead_notes(
            job['midi_path'],
            track_index=track_index,
            lead_patterns=config.get('lead_track_patterns'),
            default_bpm=config.get('default_bpm', 120.0),
        )

        if not midi_data.notes:
            return jsonify({'error': 'No notes found in selected track'}), 400

        # Map to lanes
        lanes = map_pitches_to_lanes(
            midi_data.notes,
            midi_data.ticks_per_beat,
            phrase_silence_beats=config.get('phrase_silence_beats', 1.0),
            max_lane_jump=config.get('max_lane_jump', 2),
            smoothing_passes=config.get('smoothing_passes', 1),
        )

        # QA detection
        mapped_notes = create_mapped_notes(midi_data.notes, lanes, include_qa=True)
        qa_summary = summarize_qa_issues(mapped_notes)

        # Generate preview
        preview = preview_lanes_ascii(midi_data.notes, lanes, midi_data.ticks_per_beat)

        # Write chart
        chart_path = job_folder / f'{song_name}.chart'
        metadata = ChartMetadata(
            name=song_name,
            artist=artist,
            charter=charter,
        )

        write_chart(
            str(chart_path),
            midi_data.notes,
            lanes,
            midi_data.ticks_per_beat,
            midi_data.bpm,
            metadata=metadata,
            mapped_notes=mapped_notes,
            include_qa_events=True,
        )

        # Calculate stats
        total_ticks = midi_data.notes[-1].end_tick - midi_data.notes[0].start_tick
        duration_beats = total_ticks / midi_data.ticks_per_beat
        duration_seconds = duration_beats * (60 / midi_data.bpm)

        job['chart_path'] = str(chart_path)
        job['chart_name'] = f'{song_name}.chart'

        # Store notes data for editor
        job['notes_data'] = [
            {
                'tick': note.start_tick,
                'lane': lanes[i],
                'duration': note.end_tick - note.start_tick,
            }
            for i, note in enumerate(midi_data.notes)
        ]
        job['bpm'] = midi_data.bpm
        job['ticks_per_beat'] = midi_data.ticks_per_beat

        return jsonify({
            'success': True,
            'job_id': job_id,
            'stats': {
                'notes': len(midi_data.notes),
                'track': midi_data.track_name,
                'bpm': midi_data.bpm,
                'duration_seconds': round(duration_seconds, 1),
                'qa_issues': qa_summary,
            },
            'preview': preview,
            'download_url': url_for('download_chart', job_id=job_id),
        })
    except Exception as e:
        return jsonify({'error': f'Conversion failed: {str(e)}'}), 500


@app.route('/api/download/<job_id>')
def download_chart(job_id):
    """Download the generated .chart file."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    if 'chart_path' not in job:
        return jsonify({'error': 'No chart generated'}), 400

    return send_file(
        job['chart_path'],
        as_attachment=True,
        download_name=job.get('chart_name', 'output.chart'),
    )


@app.route('/api/chart-data/<job_id>', methods=['GET'])
def get_chart_data(job_id):
    """Get chart note data for editor."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    if 'chart_path' not in job:
        return jsonify({'error': 'No chart generated'}), 400

    # Check if audio is available
    audio_url = None
    if 'audio_path' in job and Path(job['audio_path']).exists():
        audio_url = url_for('get_audio', job_id=job_id)

    # Return the stored note data
    # Fallback chain: bpm -> detected_bpm -> midi_stats.bpm -> 120
    bpm = job.get('bpm') or job.get('detected_bpm') or job.get('midi_stats', {}).get('bpm') or 120
    return jsonify({
        'notes': job.get('notes_data', []),
        'bpm': bpm,
        'ticks_per_beat': job.get('ticks_per_beat', 192),
        'audio_url': audio_url,
    })


@app.route('/api/audio/<job_id>')
def get_audio(job_id):
    """Stream audio file for editor playback."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    if 'audio_path' not in job:
        return jsonify({'error': 'No audio available'}), 404

    audio_path = Path(job['audio_path'])
    if not audio_path.exists():
        return jsonify({'error': 'Audio file not found'}), 404

    return send_file(
        audio_path,
        mimetype=f'audio/{audio_path.suffix[1:]}',
    )


@app.route('/api/waveform/<job_id>')
def get_waveform(job_id):
    """
    Get waveform data for the audio file.

    Returns an array of amplitude values (0-1) sampled at a fixed rate,
    suitable for rendering a waveform visualization in the editor.
    """
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    if 'audio_path' not in job:
        return jsonify({'error': 'No audio available'}), 404

    audio_path = Path(job['audio_path'])
    if not audio_path.exists():
        return jsonify({'error': 'Audio file not found'}), 404

    # Check if we have cached waveform data
    if 'waveform_data' in job:
        return jsonify({
            'waveform': job['waveform_data'],
            'sample_rate': job.get('waveform_sample_rate', 100),
            'duration': job.get('waveform_duration', 0),
        })

    try:
        import librosa
        import numpy as np

        # Load audio file
        y, sr = librosa.load(str(audio_path), sr=22050, mono=True)
        duration = len(y) / sr

        # Target sample rate for waveform (samples per second)
        waveform_sr = 100  # 100 samples per second = 10ms resolution

        # Calculate number of samples per waveform point
        samples_per_point = sr // waveform_sr

        # Calculate RMS amplitude for each point
        waveform = []
        for i in range(0, len(y), samples_per_point):
            chunk = y[i:i + samples_per_point]
            if len(chunk) > 0:
                # RMS amplitude
                rms = np.sqrt(np.mean(chunk ** 2))
                waveform.append(float(rms))

        # Normalize to 0-1 range
        if waveform:
            max_val = max(waveform)
            if max_val > 0:
                waveform = [v / max_val for v in waveform]

        # Cache the waveform data
        job['waveform_data'] = waveform
        job['waveform_sample_rate'] = waveform_sr
        job['waveform_duration'] = duration

        return jsonify({
            'waveform': waveform,
            'sample_rate': waveform_sr,
            'duration': duration,
        })

    except Exception as e:
        return jsonify({'error': f'Failed to generate waveform: {str(e)}'}), 500


@app.route('/api/chart-data/<job_id>', methods=['PUT'])
def update_chart_data(job_id):
    """Update chart with edited notes."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    data = request.get_json() or {}
    notes_data = data.get('notes', [])

    if not notes_data:
        return jsonify({'error': 'No notes provided'}), 400

    song_name = data.get('name') or job.get('original_name', 'Unknown')
    artist = data.get('artist') or job.get('artist', 'Unknown')
    charter = data.get('charter', 'Clone Hero Converter')

    job_folder = get_job_folder(job_id)
    bpm = job.get('bpm', 120)
    ticks_per_beat = job.get('ticks_per_beat', 192)

    try:
        # Convert editor notes to chart format and write
        chart_path = job_folder / f'{song_name}.chart'

        # Build chart content from editor notes
        chart_lines = []
        chart_lines.append('[Song]')
        chart_lines.append('{')
        chart_lines.append(f'  Name = "{song_name}"')
        chart_lines.append(f'  Artist = "{artist}"')
        chart_lines.append(f'  Charter = "{charter}"')
        chart_lines.append('  Resolution = 192')
        chart_lines.append('  Offset = 0')
        chart_lines.append('}')
        chart_lines.append('')
        chart_lines.append('[SyncTrack]')
        chart_lines.append('{')
        chart_lines.append(f'  0 = TS 4')
        chart_lines.append(f'  0 = B {int(bpm * 1000)}')
        chart_lines.append('}')
        chart_lines.append('')
        chart_lines.append('[Events]')
        chart_lines.append('{')
        chart_lines.append('}')
        chart_lines.append('')
        chart_lines.append('[ExpertSingle]')
        chart_lines.append('{')

        # Sort notes by tick
        sorted_notes = sorted(notes_data, key=lambda n: n['tick'])

        for note in sorted_notes:
            tick = note['tick']
            lane = note['lane']
            duration = note.get('duration', 0)
            chart_lines.append(f'  {tick} = N {lane} {duration}')

        chart_lines.append('}')

        with open(chart_path, 'w') as f:
            f.write('\n'.join(chart_lines))

        # Update job data
        job['chart_path'] = str(chart_path)
        job['chart_name'] = f'{song_name}.chart'
        job['notes_data'] = notes_data

        # Calculate stats
        if sorted_notes:
            total_ticks = sorted_notes[-1]['tick'] - sorted_notes[0]['tick']
            duration_beats = total_ticks / ticks_per_beat
            duration_seconds = duration_beats * (60 / bpm)
        else:
            duration_seconds = 0

        # Generate preview
        preview_lines = []
        preview_ticks = sorted_notes[:20] if len(sorted_notes) > 20 else sorted_notes
        for note in preview_ticks:
            lane_char = ['G', 'R', 'Y', 'B', 'O'][note['lane']]
            preview_lines.append(f"  {note['tick']:6d} | {'.' * note['lane']}{lane_char}{'.' * (4 - note['lane'])}")

        return jsonify({
            'success': True,
            'stats': {
                'notes': len(sorted_notes),
                'bpm': bpm,
                'duration_seconds': round(duration_seconds, 1),
            },
            'preview': '\n'.join(preview_lines),
        })

    except Exception as e:
        return jsonify({'error': f'Failed to save chart: {str(e)}'}), 500


@app.route('/api/separate', methods=['POST'])
def separate_stem():
    """Separate a stem from uploaded audio for preview."""
    cleanup_old_jobs()

    if not check_demucs_available():
        return jsonify({'error': 'Demucs not installed. Run: pip install demucs'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    ext = Path(file.filename).suffix.lower()
    audio_exts = ['.mp3', '.m4a', '.wav', '.ogg', '.flac', '.webm', '.opus']

    if ext not in audio_exts:
        return jsonify({'error': 'File must be audio (.mp3, .m4a, .wav, .ogg)'}), 400

    stem_type = request.form.get('stem_type', 'other')
    if not stem_type:
        return jsonify({'error': 'No stem type specified'}), 400

    # Create job
    job_id = str(uuid.uuid4())[:8]
    job_folder = get_job_folder(job_id)

    try:
        # Save uploaded audio
        audio_path = job_folder / f'audio{ext}'
        file.save(audio_path)

        # Run stem separation
        stem_path = separate_stems_demucs(
            str(audio_path),
            str(job_folder),
            stem=stem_type,
        )

        if not stem_path:
            return jsonify({'error': f'Stem separation failed for {stem_type}'}), 500

        # Store job info
        jobs[job_id] = {
            'audio_path': str(audio_path),
            'stem_path': stem_path,
            'stem_type': stem_type,
            'original_name': Path(file.filename).stem,
        }

        return jsonify({
            'job_id': job_id,
            'stem_type': stem_type,
            'stem_url': url_for('get_separated_stem', job_id=job_id),
            'original_url': url_for('get_audio', job_id=job_id),
            'message': f'Successfully separated {stem_type} stem!',
        })

    except Exception as e:
        shutil.rmtree(job_folder, ignore_errors=True)
        return jsonify({'error': f'Stem separation failed: {str(e)}'}), 500


@app.route('/api/stem/<job_id>')
def get_separated_stem(job_id):
    """Stream separated stem audio for preview."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    if 'stem_path' not in job:
        return jsonify({'error': 'No separated stem available'}), 404

    stem_path = Path(job['stem_path'])
    if not stem_path.exists():
        return jsonify({'error': 'Stem file not found'}), 404

    return send_file(
        stem_path,
        mimetype='audio/wav',
    )


@app.route('/api/download/<job_id>/bundle')
def download_bundle(job_id):
    """Download chart + audio as a zip bundle."""
    import zipfile

    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    if 'chart_path' not in job:
        return jsonify({'error': 'No chart generated'}), 400

    job_folder = get_job_folder(job_id)
    zip_path = job_folder / 'bundle.zip'

    with zipfile.ZipFile(zip_path, 'w') as zf:
        # Add chart
        zf.write(job['chart_path'], Path(job['chart_path']).name)

        # Add audio if present
        if 'audio_path' in job and Path(job['audio_path']).exists():
            audio_path = Path(job['audio_path'])
            # Rename to song.mp3/ogg for Clone Hero
            zf.write(audio_path, f'song{audio_path.suffix}')

    song_name = job.get('original_name', 'song')
    return send_file(
        zip_path,
        as_attachment=True,
        download_name=f'{song_name}_chart.zip',
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
