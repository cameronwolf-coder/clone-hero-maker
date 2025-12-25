// Clone Hero Converter - Frontend Logic

// Helper to get human-readable conversion method label
function getMethodLabel(method, stemSeparated, stemType) {
    const methods = {
        'basic_pitch': 'AI Neural Network',
        'librosa_pyin': 'Pitch Detection',
    };
    let label = methods[method] || method || 'Unknown';
    if (stemSeparated && stemType) {
        label = `AI Stem Separation (${stemType}) + ${label}`;
    }
    return label;
}

// Check server capabilities on load
async function checkCapabilities() {
    try {
        const response = await fetch('/api/capabilities');
        const caps = await response.json();

        // Update stem options to show availability
        const stemSelects = document.querySelectorAll('#stem-select, #youtube-stem-select');
        stemSelects.forEach(select => {
            const parent = select.closest('.stem-options');
            if (parent) {
                const small = parent.querySelector('.small');
                if (caps.demucs_available) {
                    small.innerHTML = '✓ AI Stem Separation available - isolates the selected instrument';
                    small.style.color = 'var(--success)';
                } else {
                    small.innerHTML = '⚠ Stem separation unavailable (Demucs not installed) - will process full mix';
                    small.style.color = 'var(--warning)';
                    // Disable stem options since they won't work
                    select.disabled = true;
                    select.title = 'Install Demucs to enable stem separation: pip install demucs';
                }
            }
        });

        return caps;
    } catch (e) {
        console.error('Failed to check capabilities:', e);
        return null;
    }
}

const state = {
    jobId: null,
    selectedTrack: null,
    selectedStem: null,  // For audio workflow - which instrument stem to use
    hasAudio: false,
    chartData: null,
    editor: null,
};

// Stem separation state (Upload tab)
let separationState = {
    file: null,
    jobId: null,
    stemType: null,
};

// YouTube stem separation state
let youtubeSeparationState = {
    jobId: null,
    stemType: null,
    title: null,
    artist: null,
};

// DOM Elements
const elements = {
    tabs: document.querySelectorAll('.tab'),
    tabContents: document.querySelectorAll('.tab-content'),

    // Upload tab
    uploadZone: document.getElementById('upload-zone'),
    midiFile: document.getElementById('midi-file'),

    // YouTube tab
    youtubeUrl: document.getElementById('youtube-url'),
    youtubeBtn: document.getElementById('youtube-btn'),

    // Sections
    inputSection: document.getElementById('input-section'),
    trackSection: document.getElementById('track-section'),
    metadataSection: document.getElementById('metadata-section'),
    resultsSection: document.getElementById('results-section'),

    // Track selection
    trackList: document.getElementById('track-list'),

    // Metadata
    songName: document.getElementById('song-name'),
    artistName: document.getElementById('artist-name'),
    charterName: document.getElementById('charter-name'),
    convertBtn: document.getElementById('convert-btn'),

    // Results
    stats: document.getElementById('stats'),
    qaIssues: document.getElementById('qa-issues'),
    qaList: document.getElementById('qa-list'),
    previewContainer: document.getElementById('preview-container'),
    preview: document.getElementById('preview'),
    editChart: document.getElementById('edit-chart'),
    downloadChart: document.getElementById('download-chart'),
    downloadBundle: document.getElementById('download-bundle'),
    startOver: document.getElementById('start-over'),

    // Editor
    editorModal: document.getElementById('editor-modal'),
    editorContainer: document.getElementById('chart-editor-container'),
    closeEditor: document.getElementById('close-editor'),

    // Status
    status: document.getElementById('status'),
    loading: document.getElementById('loading'),
    loadingText: document.getElementById('loading-text'),
};

// Tab switching
elements.tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        elements.tabs.forEach(t => t.classList.remove('active'));
        elements.tabContents.forEach(c => c.classList.remove('active'));

        tab.classList.add('active');
        document.getElementById(`${tab.dataset.tab}-tab`).classList.add('active');
    });
});

// File upload handling
function setupUploadZone(zone, fileInput, handler) {
    zone.addEventListener('click', () => fileInput.click());

    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('dragover');
    });

    zone.addEventListener('dragleave', () => {
        zone.classList.remove('dragover');
    });

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file) handler(file);
    });

    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];
        if (file) handler(file);
    });
}

// Upload MIDI or audio file
async function uploadMidi(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    const isAudio = ['mp3', 'm4a', 'wav', 'ogg', 'flac', 'webm', 'opus'].includes(ext);
    const isMidi = ['mid', 'midi'].includes(ext);

    if (isAudio) {
        // For audio files, separate all stems and let user choose
        separationState.file = file;
        await separateAllStems(file);
        return;
    }

    // For MIDI files, use the original upload flow
    showLoading('Uploading MIDI...');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Upload failed');
        }

        state.jobId = data.job_id;
        state.hasAudio = false;

        elements.uploadZone.classList.add('success');
        elements.uploadZone.innerHTML = `
            <div class="upload-icon">
                <svg viewBox="0 0 24 24" width="48" height="48">
                    <path fill="currentColor" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                </svg>
            </div>
            <p>${file.name}</p>
        `;

        showTrackSelection(data.tracks, data.filename);
        hideLoading();

    } catch (error) {
        hideLoading();
        showError(error.message);
    }
}

// Separate ALL stems from audio and show instrument selection
async function separateAllStems(file) {
    showLoading('Separating all instruments (this takes a few minutes)...');

    // First upload the file
    const formData = new FormData();
    formData.append('file', file);

    try {
        // Upload to create a job
        const uploadResponse = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
        });

        const uploadData = await uploadResponse.json();
        if (!uploadResponse.ok) {
            throw new Error(uploadData.error || 'Upload failed');
        }

        // Now call separate-all with the job_id
        const response = await fetch('/api/separate-all', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ job_id: uploadData.job_id }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Separation failed');
        }

        state.jobId = data.job_id;
        state.hasAudio = true;
        separationState.jobId = data.job_id;

        // Update upload zone
        elements.uploadZone.classList.add('success');
        elements.uploadZone.innerHTML = `
            <div class="upload-icon">
                <svg viewBox="0 0 24 24" width="48" height="48">
                    <path fill="currentColor" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                </svg>
            </div>
            <p>${file.name}</p>
            <p class="small">All instruments separated!</p>
        `;

        // Show instrument selection
        showInstrumentSelection(data.stems, file.name);
        hideLoading();

    } catch (error) {
        hideLoading();
        showError(error.message);
    }
}

// Show instrument selection UI (replaces track selection for audio)
function showInstrumentSelection(stems, filename) {
    elements.trackSection.classList.remove('hidden');
    elements.trackSection.querySelector('h2').textContent = '2. Select Instrument';
    elements.trackList.innerHTML = '';

    // Filter out stems with no notes and sort by note count
    const validStems = stems.filter(s => s.note_count > 0);

    if (validStems.length === 0) {
        elements.trackList.innerHTML = '<p class="error">No instruments detected with notes. Try a different audio file.</p>';
        return;
    }

    // Create instrument cards with audio preview
    validStems.forEach((stem, index) => {
        const div = document.createElement('div');
        div.className = `track-option instrument-option${index === 0 ? ' selected' : ''}`;
        div.dataset.stem = stem.stem;

        const iconMap = {
            vocals: '🎤',
            guitar: '🎸',
            bass: '🎸',
            drums: '🥁',
            piano: '🎹',
            other: '🎵',
        };

        div.innerHTML = `
            <input type="radio" name="instrument" value="${stem.stem}" ${index === 0 ? 'checked' : ''}>
            <div class="track-info">
                <div class="track-name">
                    <span class="instrument-icon">${iconMap[stem.stem] || '🎵'}</span>
                    ${stem.stem.charAt(0).toUpperCase() + stem.stem.slice(1)}
                </div>
                <div class="track-notes">${stem.note_count} notes • ${stem.duration}s</div>
                <audio controls src="${stem.audio_url}" class="stem-audio-preview"></audio>
            </div>
        `;

        div.addEventListener('click', (e) => {
            // Don't trigger if clicking on audio controls
            if (e.target.tagName === 'AUDIO') return;

            document.querySelectorAll('.track-option').forEach(el => el.classList.remove('selected'));
            div.classList.add('selected');
            div.querySelector('input').checked = true;
            state.selectedStem = stem.stem;
        });

        elements.trackList.appendChild(div);
    });

    state.selectedStem = validStems[0].stem;

    // Set default song name from filename
    if (!elements.songName.value) {
        elements.songName.value = filename.replace(/\.[^.]+$/, '');
    }

    // Show metadata section
    elements.metadataSection.classList.remove('hidden');

    // Scroll to selection
    elements.trackSection.scrollIntoView({ behavior: 'smooth' });
}

// YouTube download - now separates ALL stems automatically
async function downloadYoutube() {
    const url = elements.youtubeUrl.value.trim();
    if (!url) {
        showError('Please enter a YouTube URL');
        return;
    }

    showLoading('Processing YouTube video...');
    clearActivityLog();
    addLog('Starting YouTube download and separation', 'info');
    addLog(`URL: ${url}`, 'info');

    try {
        updateProgress(5);
        addLog('Downloading audio from YouTube...', 'info');

        // Use the new separate-all endpoint with YouTube URL
        const response = await fetch('/api/separate-all', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url }),
        });

        const data = await response.json();

        if (!response.ok) {
            // Show any logs from backend even on error
            if (data.log && data.log.length > 0) {
                data.log.forEach(logEntry => {
                    addLog(logEntry.message, logEntry.type || 'info');
                });
            }
            addLog(`Error: ${data.error || 'Download/separation failed'}`, 'error');
            throw new Error(data.error || 'Download/separation failed');
        }

        // Use real progress and logs from backend
        if (data.progress) {
            updateProgress(data.progress);
        }

        if (data.log && data.log.length > 0) {
            // Add all backend logs to activity log
            data.log.forEach(logEntry => {
                addLog(logEntry.message, logEntry.type || 'info');
            });
        }

        addLog(`Title: ${data.title || 'Unknown'}`, 'info');
        addLog(`Artist: ${data.artist || 'Unknown'}`, 'info');
        addLog(`Separation complete! ${data.stems ? data.stems.length : 0} stems ready`, 'success');
        updateProgress(100);

        state.jobId = data.job_id;
        state.hasAudio = true;
        youtubeSeparationState.jobId = data.job_id;
        youtubeSeparationState.title = data.title;
        youtubeSeparationState.artist = data.artist;

        // Pre-fill metadata
        elements.songName.value = data.title || '';
        elements.artistName.value = data.artist || '';

        // Show instrument selection with all stems
        showInstrumentSelection(data.stems, data.title || 'YouTube Audio');
        hideLoading();

        showSuccess(`All instruments separated! Select which one to use for your chart.`);

    } catch (error) {
        addLog(`Fatal error: ${error.message}`, 'error');
        hideLoading();
        showError(error.message);
    }
}

// Show track selection
function showTrackSelection(tracks, filename) {
    elements.trackSection.classList.remove('hidden');
    elements.trackList.innerHTML = '';

    // Auto-select first track or best candidate
    const defaultTrack = tracks.find(t =>
        t.name.toLowerCase().includes('lead') ||
        t.name.toLowerCase().includes('melody')
    ) || tracks[0];

    tracks.forEach(track => {
        const div = document.createElement('div');
        div.className = `track-option${track.index === defaultTrack.index ? ' selected' : ''}`;
        div.innerHTML = `
            <input type="radio" name="track" value="${track.index}"
                   ${track.index === defaultTrack.index ? 'checked' : ''}>
            <div class="track-info">
                <div class="track-name">${track.name}</div>
                <div class="track-notes">${track.note_count} notes${track.bpm ? ` • ${track.bpm} BPM` : ''}</div>
            </div>
        `;

        div.addEventListener('click', () => {
            document.querySelectorAll('.track-option').forEach(el => el.classList.remove('selected'));
            div.classList.add('selected');
            div.querySelector('input').checked = true;
            state.selectedTrack = track.index;
        });

        elements.trackList.appendChild(div);
    });

    state.selectedTrack = defaultTrack.index;

    // Set default song name from filename
    if (!elements.songName.value) {
        elements.songName.value = filename.replace(/\.(mid|midi)$/i, '');
    }

    // Show metadata section
    elements.metadataSection.classList.remove('hidden');

    // Scroll to track section
    elements.trackSection.scrollIntoView({ behavior: 'smooth' });
}

// Convert to chart
async function convertToChart() {
    if (!state.jobId) {
        showError('Please upload a file first');
        return;
    }

    // Check if we need to select a stem first (audio workflow)
    if (state.selectedStem) {
        showLoading('Selecting instrument and converting to .chart...');

        try {
            // First select the stem to use
            const selectResponse = await fetch(`/api/select-stem/${state.jobId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ stem: state.selectedStem }),
            });

            const selectData = await selectResponse.json();

            if (!selectResponse.ok) {
                throw new Error(selectData.error || 'Stem selection failed');
            }

            // Update state with the track info
            if (selectData.tracks && selectData.tracks.length > 0) {
                state.selectedTrack = selectData.tracks[0].index;
            }
        } catch (error) {
            hideLoading();
            showError(error.message);
            return;
        }
    }

    showLoading('Converting to .chart...');

    try {
        const response = await fetch(`/api/convert/${state.jobId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                track_index: state.selectedTrack,
                name: elements.songName.value || 'Unknown',
                artist: elements.artistName.value || 'Unknown',
                charter: elements.charterName.value || 'Clone Hero Converter',
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Conversion failed');
        }

        showResults(data);
        hideLoading();

    } catch (error) {
        hideLoading();
        showError(error.message);
    }
}

// Show results
function showResults(data) {
    elements.resultsSection.classList.remove('hidden');

    // Stats
    elements.stats.innerHTML = `
        <div class="stat">
            <div class="stat-value">${data.stats.notes}</div>
            <div class="stat-label">Notes</div>
        </div>
        <div class="stat">
            <div class="stat-value">${data.stats.bpm.toFixed(0)}</div>
            <div class="stat-label">BPM</div>
        </div>
        <div class="stat">
            <div class="stat-value">${data.stats.duration_seconds}s</div>
            <div class="stat-label">Duration</div>
        </div>
    `;

    // QA Issues
    if (data.stats.qa_issues && Object.keys(data.stats.qa_issues).length > 0) {
        elements.qaIssues.classList.remove('hidden');
        elements.qaList.innerHTML = Object.entries(data.stats.qa_issues)
            .map(([issue, count]) => `
                <div class="qa-item">
                    <span class="label">${issue}</span>
                    <span>${count}</span>
                </div>
            `).join('');
    } else {
        elements.qaIssues.classList.add('hidden');
    }

    // Preview
    if (data.preview) {
        elements.previewContainer.classList.remove('hidden');
        elements.preview.textContent = data.preview;
    }

    // Download links
    elements.downloadChart.href = data.download_url;

    if (state.hasAudio) {
        elements.downloadBundle.classList.remove('hidden');
        elements.downloadBundle.href = `/api/download/${state.jobId}/bundle`;
    }

    // Scroll to results
    elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Start over
function startOver() {
    state.jobId = null;
    state.selectedTrack = null;
    state.selectedStem = null;
    state.hasAudio = false;

    // Reset separation state
    separationState = { file: null, jobId: null, stemType: null };
    youtubeSeparationState = { jobId: null, stemType: null, title: null, artist: null };

    // Reset UI
    elements.uploadZone.classList.remove('success');
    elements.uploadZone.innerHTML = `
        <div class="upload-icon">
            <svg viewBox="0 0 24 24" width="48" height="48">
                <path fill="currentColor" d="M9 16h6v-6h4l-7-7-7 7h4v6zm-4 2h14v2H5v-2z"/>
            </svg>
        </div>
        <p>Drop file here or <span class="link">browse</span></p>
        <p class="small">MIDI (.mid) or Audio (.mp3, .m4a, .wav, .ogg)</p>
    `;

    // Reset YouTube tab
    elements.youtubeUrl.value = '';

    elements.songName.value = '';
    elements.artistName.value = '';
    elements.charterName.value = 'Clone Hero Converter';

    elements.trackSection.classList.add('hidden');
    elements.metadataSection.classList.add('hidden');
    elements.resultsSection.classList.add('hidden');
    elements.qaIssues.classList.add('hidden');
    elements.previewContainer.classList.add('hidden');
    elements.downloadBundle.classList.add('hidden');

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// UI Helpers
function showLoading(text) {
    elements.loadingText.textContent = text;
    elements.loading.classList.remove('hidden');

    // Reset progress
    updateProgress(0);
    clearActivityLog();
}

function hideLoading() {
    elements.loading.classList.add('hidden');
}

function updateProgress(percent) {
    const progressFill = document.getElementById('progress-fill');
    const progressPercent = document.getElementById('progress-percent');
    if (progressFill && progressPercent) {
        progressFill.style.width = `${percent}%`;
        progressPercent.textContent = `${Math.round(percent)}%`;
    }
}

function addLog(message, type = 'info') {
    const logContainer = document.getElementById('activity-log');
    if (!logContainer) return;

    const timestamp = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.innerHTML = `<span class="log-timestamp">${timestamp}</span>${message}`;

    logContainer.appendChild(entry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

function clearActivityLog() {
    const logContainer = document.getElementById('activity-log');
    if (logContainer) {
        logContainer.innerHTML = '';
    }
}

function showError(message) {
    elements.status.textContent = message;
    elements.status.className = 'status error';
    elements.status.classList.remove('hidden');
    setTimeout(() => elements.status.classList.add('hidden'), 5000);
}

function showSuccess(message) {
    elements.status.textContent = message;
    elements.status.className = 'status success';
    elements.status.classList.remove('hidden');
    setTimeout(() => elements.status.classList.add('hidden'), 3000);
}

// Event Listeners
setupUploadZone(elements.uploadZone, elements.midiFile, uploadMidi);

elements.youtubeBtn.addEventListener('click', downloadYoutube);
elements.youtubeUrl.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') downloadYoutube();
});

elements.convertBtn.addEventListener('click', convertToChart);
elements.startOver.addEventListener('click', startOver);
elements.editChart.addEventListener('click', openEditor);
elements.closeEditor.addEventListener('click', closeEditor);

// Check capabilities on load
checkCapabilities();

// Close editor on escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !elements.editorModal.classList.contains('hidden')) {
        closeEditor();
    }
});

// Close editor on backdrop click
elements.editorModal.addEventListener('click', (e) => {
    if (e.target === elements.editorModal) {
        closeEditor();
    }
});

// Editor functions
async function openEditor() {
    if (!state.jobId) {
        showError('No chart to edit');
        return;
    }

    showLoading('Loading chart data...');

    try {
        const response = await fetch(`/api/chart-data/${state.jobId}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to load chart data');
        }

        state.chartData = data;

        // Show modal
        elements.editorModal.classList.remove('hidden');

        // Initialize editor
        if (!state.editor) {
            state.editor = new ChartEditor(elements.editorContainer);

            // Listen for chart edits
            elements.editorContainer.addEventListener('chartEdited', async (e) => {
                await saveChartEdits(e.detail.notes);
            });
        }

        // Load notes into editor (with audio and waveform if available)
        state.editor.loadNotes(data.notes, data.bpm, data.ticks_per_beat, data.audio_url, state.jobId);

        // Resize after modal is visible
        setTimeout(() => {
            state.editor.resizeCanvas();
        }, 100);

        hideLoading();

    } catch (error) {
        hideLoading();
        showError(error.message);
    }
}

function closeEditor() {
    elements.editorModal.classList.add('hidden');
}

async function saveChartEdits(notes) {
    if (!state.jobId) return;

    showLoading('Saving changes...');

    try {
        const response = await fetch(`/api/chart-data/${state.jobId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                notes: notes,
                name: elements.songName.value || 'Unknown',
                artist: elements.artistName.value || 'Unknown',
                charter: elements.charterName.value || 'Clone Hero Converter',
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to save changes');
        }

        // Update stats display
        elements.stats.innerHTML = `
            <div class="stat">
                <div class="stat-value">${data.stats.notes}</div>
                <div class="stat-label">Notes</div>
            </div>
            <div class="stat">
                <div class="stat-value">${data.stats.bpm.toFixed(0)}</div>
                <div class="stat-label">BPM</div>
            </div>
            <div class="stat">
                <div class="stat-value">${data.stats.duration_seconds}s</div>
                <div class="stat-label">Duration</div>
            </div>
        `;

        // Update preview
        if (data.preview) {
            elements.preview.textContent = data.preview;
        }

        hideLoading();
        showSuccess('Chart saved!');
        closeEditor();

    } catch (error) {
        hideLoading();
        showError(error.message);
    }
}
