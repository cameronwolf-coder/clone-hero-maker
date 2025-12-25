// Clone Hero Chart Editor
// Highway-style preview with interactive editing (Moonscraper-style features)

class ChartEditor {
    constructor(container) {
        this.container = container;
        this.canvas = null;
        this.ctx = null;
        this.notes = [];
        this.bpm = 120;
        this.ticksPerBeat = 192;
        this.zoom = 1;
        this.scrollPosition = 0;
        this.selectedNotes = []; // Multi-select support
        this.tool = 'select';
        this.isPlaying = false;
        this.playheadTime = 0;
        this.lastFrameTime = 0;

        // Highway visual settings - Top-down flat view (Moonscraper-style)
        this.laneColors = ['#22cc44', '#dd2222', '#ddcc22', '#2266dd', '#dd8822']; // G R Y B O
        this.laneGlowColors = ['#44ff66', '#ff4444', '#ffee44', '#4488ff', '#ffaa44'];

        // Top-down view settings (flat, no perspective)
        this.highwayWidth = 0.6; // Highway width (% of canvas)
        this.noteRadius = 18; // Uniform note size
        this.playheadY = 0.85; // Playhead/current time line at 85% down
        this.viewDurationMs = 8000; // 8 seconds visible (more visible in flat view)
        this.pixelsPerMs = 0.15; // Pixels per millisecond (adjusted by zoom)

        // Animation
        this.animationId = null;
        this.targetScroll = 0;
        this.scrollVelocity = 0;

        // Note hit animations
        this.hitAnimations = []; // Track active hit animations {lane, startTime, color}

        // History for undo/redo
        this.history = [];
        this.historyIndex = -1;

        // Audio
        this.audio = null;
        this.audioUrl = null;
        this.hasAudio = false;

        // Waveform data (from actual audio)
        this.waveformData = null; // Array of amplitude values 0-1
        this.waveformSampleRate = 100; // Samples per second
        this.waveformColor = 'rgba(0, 200, 255, 0.4)';
        this.showWaveform = true;

        // Moonscraper-style features
        this.clipboard = []; // For copy/paste
        this.snapDivision = 4; // 1/4 beat snapping (1=whole, 2=half, 4=quarter, 8=eighth, 16=sixteenth)
        this.gridSnap = true; // Toggle grid snapping
        this.heldLanes = new Set(); // Track which number keys are held for multi-lane placement

        // Box selection
        this.isBoxSelecting = false;
        this.boxSelectStart = null;
        this.boxSelectEnd = null;

        this.init();
    }

    init() {
        this.createDOM();
        this.setupEventListeners();
        this.startRenderLoop();
    }

    createDOM() {
        this.container.innerHTML = `
            <div class="editor-container">
                <div class="editor-toolbar">
                    <div class="tool-group">
                        <button class="tool-btn active" data-tool="select" title="Select (V)">
                            <svg viewBox="0 0 24 24" width="20" height="20">
                                <path fill="currentColor" d="M7 2l12 11.5-5.5 1 3.5 7-2.5 1-3.5-7-4 4z"/>
                            </svg>
                        </button>
                        <button class="tool-btn" data-tool="add" title="Add Note (A)">
                            <svg viewBox="0 0 24 24" width="20" height="20">
                                <path fill="currentColor" d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                            </svg>
                        </button>
                        <button class="tool-btn" data-tool="delete" title="Delete (D)">
                            <svg viewBox="0 0 24 24" width="20" height="20">
                                <path fill="currentColor" d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                            </svg>
                        </button>
                    </div>
                    <div class="tool-group">
                        <button class="tool-btn" id="zoom-out" title="Zoom Out (-)">
                            <svg viewBox="0 0 24 24" width="20" height="20">
                                <path fill="currentColor" d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14zM7 9h5v1H7z"/>
                            </svg>
                        </button>
                        <span class="zoom-label" id="zoom-label">100%</span>
                        <button class="tool-btn" id="zoom-in" title="Zoom In (+)">
                            <svg viewBox="0 0 24 24" width="20" height="20">
                                <path fill="currentColor" d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14zm.5-7H9v2H7v1h2v2h1v-2h2V9h-2z"/>
                            </svg>
                        </button>
                    </div>
                    <div class="tool-group">
                        <button class="tool-btn" id="play-btn" title="Play/Pause (Space)">
                            <svg viewBox="0 0 24 24" width="20" height="20" id="play-icon">
                                <path fill="currentColor" d="M8 5v14l11-7z"/>
                            </svg>
                        </button>
                        <button class="tool-btn" id="stop-btn" title="Stop">
                            <svg viewBox="0 0 24 24" width="20" height="20">
                                <path fill="currentColor" d="M6 6h12v12H6z"/>
                            </svg>
                        </button>
                        <button class="tool-btn" id="mute-btn" title="Mute/Unmute (M)">
                            <svg viewBox="0 0 24 24" width="20" height="20" id="volume-icon">
                                <path fill="currentColor" d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
                            </svg>
                        </button>
                        <input type="range" id="volume-slider" min="0" max="100" value="80" title="Volume" style="width: 60px; height: 20px;">
                    </div>
                    <div class="tool-group">
                        <select id="snap-select" title="Grid Snap Division (Q/W to change)">
                            <option value="1">1/1</option>
                            <option value="2">1/2</option>
                            <option value="4" selected>1/4</option>
                            <option value="8">1/8</option>
                            <option value="12">1/12</option>
                            <option value="16">1/16</option>
                        </select>
                        <button class="tool-btn active" id="snap-toggle" title="Toggle Grid Snap (G)">
                            <svg viewBox="0 0 24 24" width="20" height="20">
                                <path fill="currentColor" d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 14H4V6h16v12zM6 10h2v2H6zm0 4h8v2H6zm10 0h2v2h-2zm-6-4h8v2h-8z"/>
                            </svg>
                        </button>
                        <button class="tool-btn active" id="waveform-toggle" title="Toggle Waveform (F)">
                            <svg viewBox="0 0 24 24" width="20" height="20">
                                <path fill="currentColor" d="M7 18h2V6H7v12zm4 4h2V2h-2v20zm-8-8h2v-4H3v4zm12 4h2V6h-2v12zm4-8v4h2v-4h-2z"/>
                            </svg>
                        </button>
                    </div>
                    <div class="tool-group" style="margin-left: auto;">
                        <span class="info-label">Notes: <span id="note-count">0</span></span>
                        <span class="info-label">BPM: <span id="bpm-display">120</span></span>
                        <span class="info-label">Time: <span id="time-display">0:00</span></span>
                    </div>
                </div>
                <div class="editor-main">
                    <div class="lane-labels">
                        <div class="lane-label" style="background: #f0883e">O</div>
                        <div class="lane-label" style="background: #58a6ff">B</div>
                        <div class="lane-label" style="background: #d29922">Y</div>
                        <div class="lane-label" style="background: #f85149">R</div>
                        <div class="lane-label" style="background: #3fb950">G</div>
                    </div>
                    <div class="canvas-container" id="canvas-container">
                        <canvas id="editor-canvas"></canvas>
                    </div>
                    <div class="scrollbar-container">
                        <input type="range" id="timeline-scroll" min="0" max="100" value="0">
                    </div>
                </div>
                <div class="editor-footer">
                    <div class="edit-hint">
                        <span>1-5: Add note</span>
                        <span>↑↓/Scroll: Navigate</span>
                        <span>Home/End: Jump</span>
                        <span>Space: Play</span>
                        <span>Del: Delete</span>
                        <span>F: Waveform</span>
                    </div>
                    <div class="editor-actions">
                        <button class="btn secondary" id="undo-btn">Undo</button>
                        <button class="btn primary" id="apply-btn">Apply Changes</button>
                    </div>
                </div>
            </div>
        `;

        this.canvas = document.getElementById('editor-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.canvasContainer = document.getElementById('canvas-container');

        this.resizeCanvas();
    }

    resizeCanvas() {
        const rect = this.canvasContainer.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;

        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        this.canvas.style.width = rect.width + 'px';
        this.canvas.style.height = rect.height + 'px';

        this.ctx.scale(dpr, dpr);
        this.displayWidth = rect.width;
        this.displayHeight = rect.height;
    }

    setupEventListeners() {
        // Tool buttons
        this.container.querySelectorAll('.tool-btn[data-tool]').forEach(btn => {
            btn.addEventListener('click', () => {
                this.container.querySelectorAll('.tool-btn[data-tool]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.tool = btn.dataset.tool;
                this.canvas.style.cursor = this.tool === 'add' ? 'crosshair' :
                                           this.tool === 'delete' ? 'not-allowed' : 'default';
            });
        });

        // Zoom
        document.getElementById('zoom-in')?.addEventListener('click', () => this.setZoom(this.zoom * 1.25));
        document.getElementById('zoom-out')?.addEventListener('click', () => this.setZoom(this.zoom / 1.25));

        // Playback
        document.getElementById('play-btn')?.addEventListener('click', () => this.togglePlay());
        document.getElementById('stop-btn')?.addEventListener('click', () => this.stop());
        document.getElementById('mute-btn')?.addEventListener('click', () => this.toggleMute());
        document.getElementById('volume-slider')?.addEventListener('input', (e) => this.setVolume(e.target.value / 100));

        // Snap controls
        document.getElementById('snap-select')?.addEventListener('change', (e) => {
            this.snapDivision = parseInt(e.target.value);
        });
        document.getElementById('snap-toggle')?.addEventListener('click', () => this.toggleGridSnap());

        // Waveform toggle
        document.getElementById('waveform-toggle')?.addEventListener('click', () => this.toggleWaveform());

        // Timeline scroll
        const scrollbar = document.getElementById('timeline-scroll');
        scrollbar?.addEventListener('input', (e) => {
            const maxScroll = this.getMaxScrollMs();
            this.targetScroll = (e.target.value / 100) * maxScroll;
            this.scrollPosition = this.targetScroll;
        });

        // Canvas interactions
        this.canvas.addEventListener('click', (e) => this.handleClick(e));
        this.canvas.addEventListener('dblclick', (e) => this.handleDoubleClick(e));
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        this.canvas.addEventListener('wheel', (e) => this.handleWheel(e), { passive: false });

        // Keyboard shortcuts (Moonscraper-style)
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
        document.addEventListener('keyup', (e) => this.handleKeyUp(e));

        // Resize
        window.addEventListener('resize', () => this.resizeCanvas());

        // Undo/Apply buttons
        document.getElementById('undo-btn')?.addEventListener('click', () => this.undo());
        document.getElementById('apply-btn')?.addEventListener('click', () => this.applyChanges());
    }

    handleKeyDown(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;

        const key = e.key.toLowerCase();
        const ctrl = e.ctrlKey || e.metaKey;
        const shift = e.shiftKey;

        // Number keys 1-5: Quick note placement in lane (Moonscraper-style)
        if (['1', '2', '3', '4', '5'].includes(e.key)) {
            const lane = parseInt(e.key) - 1;
            this.heldLanes.add(lane);
            this.addNoteAtCurrentPosition(lane);
            e.preventDefault();
            return;
        }

        switch(key) {
            // Tool shortcuts
            case 'v': this.setTool('select'); break;
            case 'a':
                if (!ctrl) this.setTool('add');
                break;
            case 'd':
                if (!ctrl) this.setTool('delete');
                break;

            // Playback
            case 'm': this.toggleMute(); break;
            case ' ':
                e.preventDefault();
                this.togglePlay();
                break;

            // Delete selected
            case 'delete':
            case 'backspace':
                if (this.selectedNotes.length > 0) {
                    e.preventDefault();
                    this.deleteSelectedNotes();
                }
                break;

            // Zoom
            case '=':
            case '+': this.setZoom(this.zoom * 1.25); break;
            case '-': this.setZoom(this.zoom / 1.25); break;

            // Snap division shortcuts (Q/W like Moonscraper)
            case 'q':
                this.decreaseSnapDivision();
                break;
            case 'w':
                if (!ctrl) this.increaseSnapDivision();
                break;

            // Toggle grid snap
            case 'g':
                this.toggleGridSnap();
                break;

            // Toggle waveform display
            case 'f':
                this.toggleWaveform();
                break;

            // Navigate by measure (PageUp/PageDown)
            case 'pageup':
                e.preventDefault();
                this.navigateMeasure(1);
                break;
            case 'pagedown':
                e.preventDefault();
                this.navigateMeasure(-1);
                break;

            // Arrow keys for scrolling
            case 'arrowup':
                e.preventDefault();
                this.scrollBy(-500); // Scroll back in time
                break;
            case 'arrowdown':
                e.preventDefault();
                this.scrollBy(500); // Scroll forward in time
                break;
            case 'arrowleft':
                e.preventDefault();
                this.scrollBy(-100); // Small scroll back
                break;
            case 'arrowright':
                e.preventDefault();
                this.scrollBy(100); // Small scroll forward
                break;

            // Home/End to jump to start/end
            case 'home':
                e.preventDefault();
                this.scrollToStart();
                break;
            case 'end':
                e.preventDefault();
                this.scrollToEnd();
                break;

            // Copy/Cut/Paste (Ctrl+C/X/V)
            case 'c':
                if (ctrl) {
                    e.preventDefault();
                    this.copySelectedNotes();
                }
                break;
            case 'x':
                if (ctrl) {
                    e.preventDefault();
                    this.cutSelectedNotes();
                }
                break;

            // Undo/Redo (Ctrl+Z / Ctrl+Shift+Z)
            case 'z':
                if (ctrl) {
                    e.preventDefault();
                    if (shift) {
                        this.redo();
                    } else {
                        this.undo();
                    }
                }
                break;
            case 'y':
                if (ctrl) {
                    e.preventDefault();
                    this.redo();
                }
                break;

            // Select all (Ctrl+A)
            // Note: 'a' without ctrl is handled above for tool switching
        }

        // Select all needs to check ctrl separately
        if (key === 'a' && ctrl) {
            e.preventDefault();
            this.selectAllNotes();
        }

        // Paste (Ctrl+V)
        if (key === 'v' && ctrl) {
            e.preventDefault();
            this.pasteNotes();
        }
    }

    handleKeyUp(e) {
        // Track released number keys
        if (['1', '2', '3', '4', '5'].includes(e.key)) {
            const lane = parseInt(e.key) - 1;
            this.heldLanes.delete(lane);
        }
    }

    setTool(tool) {
        this.tool = tool;
        this.container.querySelectorAll('.tool-btn[data-tool]').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tool === tool);
        });
        this.canvas.style.cursor = tool === 'add' ? 'crosshair' :
                                   tool === 'delete' ? 'not-allowed' : 'default';
    }

    setZoom(zoom) {
        this.zoom = Math.max(0.25, Math.min(4, zoom));
        document.getElementById('zoom-label').textContent = Math.round(this.zoom * 100) + '%';
    }

    loadNotes(notes, bpm, ticksPerBeat, audioUrl = null, jobId = null) {
        this.notes = notes.map((n, i) => ({
            id: i,
            tick: n.tick,
            lane: n.lane,
            duration: n.duration || 0,
            ms: this.tickToMs(n.tick, bpm, ticksPerBeat),
            durationMs: this.tickToMs(n.duration || 0, bpm, ticksPerBeat),
        }));
        this.bpm = bpm || 120;
        this.ticksPerBeat = ticksPerBeat || 192;
        this.jobId = jobId;

        // Reset selection and history
        this.selectedNotes = [];
        this.clipboard = [];
        this.history = [JSON.stringify(this.notes)];
        this.historyIndex = 0;

        document.getElementById('note-count').textContent = this.notes.length;
        document.getElementById('bpm-display').textContent = Math.round(this.bpm);

        this.scrollPosition = 0;
        this.targetScroll = 0;
        this.updateScrollbar();

        // Load audio if available
        if (audioUrl) {
            this.loadAudio(audioUrl);
        }

        // Load waveform data if we have a job ID
        if (jobId) {
            this.loadWaveform(jobId);
        }
    }

    async loadWaveform(jobId) {
        try {
            const response = await fetch(`/api/waveform/${jobId}`);
            if (!response.ok) {
                console.warn('Waveform not available');
                return;
            }

            const data = await response.json();
            this.waveformData = data.waveform;
            this.waveformSampleRate = data.sample_rate || 100;
            this.waveformDuration = data.duration || 0;
            console.log(`Waveform loaded: ${this.waveformData.length} samples, ${this.waveformDuration}s duration`);
        } catch (e) {
            console.warn('Failed to load waveform:', e);
        }
    }

    loadAudio(url) {
        this.audioUrl = url;

        // Clean up existing audio
        if (this.audio) {
            this.audio.pause();
            this.audio.src = '';
        }

        this.audio = new Audio(url);
        this.audio.volume = 0.8;
        this.hasAudio = true;

        // Update UI to show audio is available
        const muteBtn = document.getElementById('mute-btn');
        const volumeSlider = document.getElementById('volume-slider');
        if (muteBtn) muteBtn.style.opacity = '1';
        if (volumeSlider) volumeSlider.style.opacity = '1';

        // Sync audio with scroll when seeking
        this.audio.addEventListener('timeupdate', () => {
            if (!this.isPlaying && this.audio.paused) return;
        });

        this.audio.addEventListener('ended', () => {
            this.stop();
        });

        console.log('Audio loaded:', url);
    }

    tickToMs(tick, bpm = this.bpm, ticksPerBeat = this.ticksPerBeat) {
        const beats = tick / ticksPerBeat;
        return (beats / bpm) * 60000;
    }

    msToTick(ms) {
        const beats = (ms / 60000) * this.bpm;
        return Math.round(beats * this.ticksPerBeat);
    }

    getMaxScrollMs() {
        if (this.notes.length === 0) return 5000;
        const maxMs = Math.max(...this.notes.map(n => n.ms + n.durationMs));
        return Math.max(maxMs + 2000, 5000);
    }

    updateScrollbar() {
        const scrollbar = document.getElementById('timeline-scroll');
        const maxScroll = this.getMaxScrollMs();
        if (maxScroll > 0 && scrollbar) {
            scrollbar.value = (this.scrollPosition / maxScroll) * 100;
        }
    }

    // Convert time to Y position (flat top-down view)
    // Notes scroll from top to bottom, playhead is near the bottom
    timeToY(ms) {
        const relativeMs = ms - this.scrollPosition;
        const playheadY = this.displayHeight * this.playheadY;

        // Linear mapping: each ms = fixed pixels (adjusted by zoom)
        const pixelsPerMs = (this.displayHeight * 0.8) / (this.viewDurationMs / this.zoom);

        // Notes in the future are above playhead, past notes below
        return playheadY - (relativeMs * pixelsPerMs);
    }

    // Convert Y position to time (flat top-down view)
    yToTime(y) {
        const playheadY = this.displayHeight * this.playheadY;
        const pixelsPerMs = (this.displayHeight * 0.8) / (this.viewDurationMs / this.zoom);

        // Reverse the linear mapping
        const relativeMs = (playheadY - y) / pixelsPerMs;
        return relativeMs + this.scrollPosition;
    }

    // Get highway width (constant in flat view)
    getHighwayWidth() {
        return this.displayWidth * this.highwayWidth;
    }

    // Get note radius (constant in flat view)
    getNoteRadius() {
        return this.noteRadius * this.zoom;
    }

    // Convert lane to X position (flat view - no Y dependency)
    laneToX(lane, y = null) {
        const width = this.getHighwayWidth();
        const laneWidth = width / 5;
        const startX = (this.displayWidth - width) / 2;

        return startX + lane * laneWidth + laneWidth / 2;
    }

    // Convert X to lane
    xToLane(x) {
        const width = this.getHighwayWidth();
        const startX = (this.displayWidth - width) / 2;
        const laneWidth = width / 5;

        const lane = Math.floor((x - startX) / laneWidth);
        return Math.max(0, Math.min(4, lane));
    }

    startRenderLoop() {
        const render = (timestamp) => {
            const deltaTime = timestamp - this.lastFrameTime;
            this.lastFrameTime = timestamp;

            // Playback - sync with audio if available
            if (this.isPlaying) {
                const prevPosition = this.scrollPosition;

                if (this.audio && this.hasAudio && !this.audio.paused) {
                    // Sync scroll position with audio time
                    this.scrollPosition = this.audio.currentTime * 1000;
                    this.targetScroll = this.scrollPosition;
                } else {
                    // No audio - use deltaTime
                    this.scrollPosition += deltaTime;
                    this.targetScroll = this.scrollPosition;
                }

                // Check for notes that crossed the strike line
                this.checkNoteHits(prevPosition, this.scrollPosition);

                this.updateScrollbar();
                this.updateTimeDisplay();
            }

            // Smooth scrolling (when not playing)
            if (!this.isPlaying) {
                const prevPosition = this.scrollPosition;
                const scrollDiff = this.targetScroll - this.scrollPosition;
                if (Math.abs(scrollDiff) > 0.5) {
                    this.scrollPosition += scrollDiff * 0.15;
                    // Also check for note hits when scrolling manually
                    this.checkNoteHits(Math.min(prevPosition, this.scrollPosition), Math.max(prevPosition, this.scrollPosition));
                }
            }

            this.render();
            this.animationId = requestAnimationFrame(render);
        };

        this.animationId = requestAnimationFrame(render);
    }

    updateTimeDisplay() {
        const seconds = Math.floor(this.scrollPosition / 1000);
        const minutes = Math.floor(seconds / 60);
        const secs = seconds % 60;
        const display = document.getElementById('time-display');
        if (display) {
            display.textContent = `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    }

    // Check if any notes crossed the strike line between prev and current position
    checkNoteHits(prevMs, currentMs) {
        // Notes are "hit" when their time equals the scroll position (at strike line)
        // Check for notes in the range [prevMs, currentMs]
        this.notes.forEach(note => {
            if (note.ms > prevMs && note.ms <= currentMs) {
                // Note just crossed the strike line - trigger hit animation
                this.triggerHitAnimation(note.lane, this.laneColors[note.lane]);
            }
        });
    }

    // Trigger a hit animation on a lane
    triggerHitAnimation(lane, color) {
        this.hitAnimations.push({
            lane: lane,
            startTime: Date.now(),
            color: color,
            duration: 300, // Animation duration in ms
        });
    }

    // Update and clean up hit animations
    updateHitAnimations() {
        const now = Date.now();
        this.hitAnimations = this.hitAnimations.filter(anim => {
            return (now - anim.startTime) < anim.duration;
        });
    }

    togglePlay() {
        this.isPlaying = !this.isPlaying;
        const icon = document.getElementById('play-icon');
        if (icon) {
            icon.innerHTML = this.isPlaying
                ? '<path fill="currentColor" d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>'
                : '<path fill="currentColor" d="M8 5v14l11-7z"/>';
        }

        // Sync audio playback
        if (this.audio && this.hasAudio) {
            if (this.isPlaying) {
                // Set audio position to match scroll position
                this.audio.currentTime = this.scrollPosition / 1000;
                this.audio.play().catch(e => console.log('Audio play failed:', e));
            } else {
                this.audio.pause();
            }
        }
    }

    stop() {
        this.isPlaying = false;
        this.scrollPosition = 0;
        this.targetScroll = 0;
        this.updateScrollbar();
        this.updateTimeDisplay();
        const icon = document.getElementById('play-icon');
        if (icon) {
            icon.innerHTML = '<path fill="currentColor" d="M8 5v14l11-7z"/>';
        }

        // Stop and reset audio
        if (this.audio && this.hasAudio) {
            this.audio.pause();
            this.audio.currentTime = 0;
        }
    }

    toggleMute() {
        if (!this.audio) return;

        this.audio.muted = !this.audio.muted;
        const icon = document.getElementById('volume-icon');
        if (icon) {
            icon.innerHTML = this.audio.muted
                ? '<path fill="currentColor" d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>'
                : '<path fill="currentColor" d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>';
        }
    }

    setVolume(value) {
        if (!this.audio) return;
        this.audio.volume = Math.max(0, Math.min(1, value));
    }

    render() {
        const ctx = this.ctx;
        const w = this.displayWidth;
        const h = this.displayHeight;

        // Draw space background
        this.drawBackground(ctx, w, h);

        // Draw highway
        this.drawHighway(ctx, w, h);

        // Draw waveform on highway (before beat lines so it's under them)
        if (this.showWaveform && this.waveformData) {
            this.drawWaveform(ctx, w, h);
        }

        // Draw beat lines
        this.drawBeatLines(ctx, w, h);

        // Draw notes (before strike line so they go under it)
        this.drawNotes(ctx, w, h);

        // Draw strike line / fret board (on top)
        this.drawStrikeLine(ctx, w, h);
    }

    drawBackground(ctx, w, h) {
        // Simple dark background for flat view
        ctx.fillStyle = '#0a0e14';
        ctx.fillRect(0, 0, w, h);
    }

    drawHighway(ctx, w, h) {
        const highwayWidth = this.getHighwayWidth();
        const startX = (w - highwayWidth) / 2;
        const laneWidth = highwayWidth / 5;

        // Draw highway background (full height rectangle)
        ctx.fillStyle = '#101520';
        ctx.fillRect(startX, 0, highwayWidth, h);

        // Draw colored lane backgrounds (subtle vertical stripes)
        for (let lane = 0; lane < 5; lane++) {
            const color = this.laneColors[lane];
            const laneX = startX + lane * laneWidth;

            // Subtle lane glow
            const laneGrad = ctx.createLinearGradient(laneX, 0, laneX + laneWidth, 0);
            laneGrad.addColorStop(0, color + '08');
            laneGrad.addColorStop(0.5, color + '15');
            laneGrad.addColorStop(1, color + '08');

            ctx.fillStyle = laneGrad;
            ctx.fillRect(laneX, 0, laneWidth, h);
        }

        // Draw lane dividers (vertical lines)
        for (let i = 0; i <= 5; i++) {
            const x = startX + i * laneWidth;
            const isEdge = i === 0 || i === 5;

            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, h);
            ctx.strokeStyle = isEdge ? 'rgba(80, 90, 110, 0.9)' : 'rgba(50, 60, 80, 0.5)';
            ctx.lineWidth = isEdge ? 2 : 1;
            ctx.stroke();
        }
    }

    drawWaveform(ctx, w, h) {
        if (!this.waveformData || this.waveformData.length === 0) return;

        const highwayWidth = this.getHighwayWidth();
        const startX = (w - highwayWidth) / 2;
        const viewMs = this.viewDurationMs / this.zoom;

        ctx.save();

        // Clip to highway area
        ctx.beginPath();
        ctx.rect(startX, 0, highwayWidth, h);
        ctx.clip();

        // Calculate which samples to draw
        const startMs = this.scrollPosition - viewMs * 0.2; // Show some past
        const endMs = this.scrollPosition + viewMs;
        const msPerSample = 1000 / this.waveformSampleRate;

        const startSample = Math.max(0, Math.floor(startMs / msPerSample));
        const endSample = Math.min(this.waveformData.length - 1, Math.ceil(endMs / msPerSample));

        if (startSample >= endSample) {
            ctx.restore();
            return;
        }

        // Draw waveform as filled area from center
        const highwayCenterX = w / 2;
        const maxWidth = highwayWidth * 0.45; // Max 45% of highway width each side

        // Create gradient for waveform
        ctx.fillStyle = 'rgba(0, 200, 255, 0.35)';

        // Draw left side of waveform (mirrored)
        ctx.beginPath();
        ctx.moveTo(highwayCenterX, this.timeToY(startSample * msPerSample));

        for (let i = startSample; i <= endSample; i++) {
            const sampleMs = i * msPerSample;
            const y = this.timeToY(sampleMs);

            if (y < 0 || y > h) continue;

            const amplitude = this.waveformData[i] || 0;
            const waveWidth = amplitude * maxWidth;

            ctx.lineTo(highwayCenterX - waveWidth, y);
        }

        // Return along center
        ctx.lineTo(highwayCenterX, this.timeToY(endSample * msPerSample));
        ctx.closePath();
        ctx.fill();

        // Draw right side of waveform
        ctx.beginPath();
        ctx.moveTo(highwayCenterX, this.timeToY(startSample * msPerSample));

        for (let i = startSample; i <= endSample; i++) {
            const sampleMs = i * msPerSample;
            const y = this.timeToY(sampleMs);

            if (y < 0 || y > h) continue;

            const amplitude = this.waveformData[i] || 0;
            const waveWidth = amplitude * maxWidth;

            ctx.lineTo(highwayCenterX + waveWidth, y);
        }

        ctx.lineTo(highwayCenterX, this.timeToY(endSample * msPerSample));
        ctx.closePath();
        ctx.fill();

        // Draw center line
        ctx.strokeStyle = 'rgba(0, 255, 255, 0.2)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(highwayCenterX, 0);
        ctx.lineTo(highwayCenterX, h);
        ctx.stroke();

        ctx.restore();
    }

    drawBeatLines(ctx, w, h) {
        const highwayWidth = this.getHighwayWidth();
        const startX = (w - highwayWidth) / 2;
        const msPerBeat = 60000 / this.bpm;
        const viewMs = this.viewDurationMs / this.zoom;

        // Draw lines for visible time range
        const visibleStartMs = this.scrollPosition - viewMs * 0.2;
        const visibleEndMs = this.scrollPosition + viewMs;
        const startBeat = Math.floor(Math.max(0, visibleStartMs) / msPerBeat);
        const endBeat = Math.ceil(visibleEndMs / msPerBeat);

        for (let beat = startBeat; beat <= endBeat; beat++) {
            const ms = beat * msPerBeat;
            const y = this.timeToY(ms);

            // Only draw lines within visible area
            if (y < 0 || y > h) continue;

            const isMeasure = beat % 4 === 0;

            // Beat line (horizontal across highway)
            ctx.strokeStyle = isMeasure
                ? 'rgba(255, 255, 255, 0.4)'
                : 'rgba(255, 255, 255, 0.15)';
            ctx.lineWidth = isMeasure ? 2 : 1;
            ctx.beginPath();
            ctx.moveTo(startX, y);
            ctx.lineTo(startX + highwayWidth, y);
            ctx.stroke();

            // Measure number on left
            if (isMeasure && beat >= 0) {
                ctx.fillStyle = 'rgba(139, 148, 158, 0.8)';
                ctx.font = '12px system-ui, sans-serif';
                ctx.textAlign = 'right';
                ctx.fillText(`${beat / 4 + 1}`, startX - 8, y + 4);
            }
        }
    }

    drawStrikeLine(ctx, w, h) {
        const playheadY = h * this.playheadY;
        const highwayWidth = this.getHighwayWidth();
        const startX = (w - highwayWidth) / 2;

        // ========== PLAYHEAD LINE (current time indicator) ==========
        // Outer glow
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.lineWidth = 8;
        ctx.beginPath();
        ctx.moveTo(startX, playheadY);
        ctx.lineTo(startX + highwayWidth, playheadY);
        ctx.stroke();

        // Main white playhead line
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(startX, playheadY);
        ctx.lineTo(startX + highwayWidth, playheadY);
        ctx.stroke();

        // "NOW" label on the left side
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 12px system-ui, sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText('NOW', startX - 8, playheadY + 4);

        // Arrow pointing to the line
        ctx.beginPath();
        ctx.moveTo(startX - 4, playheadY);
        ctx.lineTo(startX - 1, playheadY - 5);
        ctx.lineTo(startX - 1, playheadY + 5);
        ctx.closePath();
        ctx.fill();

        // ========== LANE INDICATORS AT PLAYHEAD ==========
        const noteRadius = this.getNoteRadius();

        for (let lane = 0; lane < 5; lane++) {
            const x = this.laneToX(lane);
            const color = this.laneColors[lane];

            // Small colored circle at playhead position for each lane
            ctx.beginPath();
            ctx.arc(x, playheadY, noteRadius * 0.4, 0, Math.PI * 2);
            ctx.fillStyle = color + '40';
            ctx.fill();
            ctx.strokeStyle = color + '80';
            ctx.lineWidth = 2;
            ctx.stroke();
        }

        // Draw hit animations
        this.updateHitAnimations();
        const now = Date.now();

        this.hitAnimations.forEach(anim => {
            const elapsed = now - anim.startTime;
            const progress = elapsed / anim.duration;
            const x = this.laneToX(anim.lane);

            const easedProgress = 1 - Math.pow(1 - progress, 3);
            const ringRadius = noteRadius + easedProgress * 40;
            const ringAlpha = 1 - easedProgress;

            // Expanding ring
            ctx.beginPath();
            ctx.arc(x, playheadY, ringRadius, 0, Math.PI * 2);
            ctx.strokeStyle = anim.color + Math.floor(ringAlpha * 255).toString(16).padStart(2, '0');
            ctx.lineWidth = 3 * (1 - easedProgress) + 1;
            ctx.stroke();
        });

        // Time display in corner
        const seconds = Math.floor(this.scrollPosition / 1000);
        const minutes = Math.floor(seconds / 60);
        const secs = seconds % 60;
        const ms = Math.floor((this.scrollPosition % 1000) / 10);
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'right';
        ctx.fillText(`${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`, w - 15, 30);
    }

    drawNotes(ctx, w, h) {
        const noteRadius = this.getNoteRadius();

        // Sort notes by time - draw notes further from playhead first
        const sortedNotes = [...this.notes].sort((a, b) => b.ms - a.ms);

        sortedNotes.forEach((note) => {
            const y = this.timeToY(note.ms);

            // Skip notes outside visible area (with padding)
            if (y < -noteRadius || y > h + noteRadius) return;

            // Get X position (flat - no perspective)
            const x = this.laneToX(note.lane);

            const color = this.laneColors[note.lane];
            const noteIndex = this.notes.indexOf(note);
            const isSelected = this.selectedNotes.includes(noteIndex);

            // Draw sustain tail (vertical bar for flat view)
            if (note.durationMs > 0) {
                const endY = this.timeToY(note.ms + note.durationMs);
                if (endY < y) {
                    // Sustain as a rectangle
                    const sustainWidth = noteRadius * 0.5;
                    ctx.fillStyle = color + 'aa';
                    ctx.fillRect(x - sustainWidth / 2, endY, sustainWidth, y - endY);

                    // Sustain outline
                    ctx.strokeStyle = color;
                    ctx.lineWidth = 1;
                    ctx.strokeRect(x - sustainWidth / 2, endY, sustainWidth, y - endY);
                }
            }

            // ========== NOTE GEM ==========
            // Outer glow
            ctx.save();
            ctx.shadowColor = color;
            ctx.shadowBlur = 8;

            // Outer colored circle
            ctx.beginPath();
            ctx.arc(x, y, noteRadius, 0, Math.PI * 2);
            const outerGrad = ctx.createRadialGradient(x, y - noteRadius * 0.3, 0, x, y, noteRadius);
            outerGrad.addColorStop(0, this.lightenColor(color, 40));
            outerGrad.addColorStop(0.5, color);
            outerGrad.addColorStop(1, this.darkenColor(color, 20));
            ctx.fillStyle = outerGrad;
            ctx.fill();

            ctx.restore();

            // Inner dark circle
            const innerRadius = noteRadius * 0.5;
            ctx.beginPath();
            ctx.arc(x, y, innerRadius, 0, Math.PI * 2);
            ctx.fillStyle = '#1a1a1a';
            ctx.fill();

            // Inner ring
            ctx.beginPath();
            ctx.arc(x, y, innerRadius, 0, Math.PI * 2);
            ctx.strokeStyle = color + '60';
            ctx.lineWidth = 1;
            ctx.stroke();

            // Outer rim highlight
            ctx.beginPath();
            ctx.arc(x, y, noteRadius - 1, 0, Math.PI * 2);
            ctx.strokeStyle = this.lightenColor(color, 30) + '80';
            ctx.lineWidth = 2;
            ctx.stroke();

            // Selection indicator
            if (isSelected) {
                ctx.beginPath();
                ctx.arc(x, y, noteRadius + 5, 0, Math.PI * 2);
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
                ctx.lineWidth = 2;
                ctx.setLineDash([4, 4]);
                ctx.stroke();
                ctx.setLineDash([]);
            }

            // Specular highlight (3D effect)
            ctx.beginPath();
            ctx.arc(x - noteRadius * 0.25, y - noteRadius * 0.25, noteRadius * 0.35, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255, 255, 255, ${0.2 + distanceT * 0.2})`;
            ctx.fill();
        });

        // Draw box selection rectangle
        if (this.isBoxSelecting && this.boxSelectStart && this.boxSelectEnd) {
            const minX = Math.min(this.boxSelectStart.x, this.boxSelectEnd.x);
            const maxX = Math.max(this.boxSelectStart.x, this.boxSelectEnd.x);
            const minY = Math.min(this.boxSelectStart.y, this.boxSelectEnd.y);
            const maxY = Math.max(this.boxSelectStart.y, this.boxSelectEnd.y);

            ctx.fillStyle = 'rgba(88, 166, 255, 0.15)';
            ctx.fillRect(minX, minY, maxX - minX, maxY - minY);

            ctx.strokeStyle = 'rgba(88, 166, 255, 0.6)';
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            ctx.strokeRect(minX, minY, maxX - minX, maxY - minY);
            ctx.setLineDash([]);
        }
    }

    lightenColor(hex, percent) {
        const num = parseInt(hex.replace('#', ''), 16);
        const amt = Math.round(2.55 * percent);
        const R = Math.min(255, (num >> 16) + amt);
        const G = Math.min(255, ((num >> 8) & 0x00FF) + amt);
        const B = Math.min(255, (num & 0x0000FF) + amt);
        return `rgb(${R}, ${G}, ${B})`;
    }

    darkenColor(hex, percent) {
        const num = parseInt(hex.replace('#', ''), 16);
        const amt = Math.round(2.55 * percent);
        const R = Math.max(0, (num >> 16) - amt);
        const G = Math.max(0, ((num >> 8) & 0x00FF) - amt);
        const B = Math.max(0, (num & 0x0000FF) - amt);
        return `rgb(${R}, ${G}, ${B})`;
    }

    handleClick(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        if (this.tool === 'add') {
            this.addNote(x, y);
        } else if (this.tool === 'delete') {
            const noteIndex = this.findNoteAt(x, y);
            if (noteIndex !== null) {
                this.deleteNote(noteIndex);
            }
        } else {
            const noteIndex = this.findNoteAt(x, y);

            // Multi-select with shift key (Moonscraper-style)
            if (e.shiftKey && noteIndex !== null) {
                if (this.selectedNotes.includes(noteIndex)) {
                    // Deselect if already selected
                    this.selectedNotes = this.selectedNotes.filter(i => i !== noteIndex);
                } else {
                    // Add to selection
                    this.selectedNotes.push(noteIndex);
                }
            } else if (noteIndex !== null) {
                // Single select
                this.selectedNotes = [noteIndex];
            } else {
                // Click on empty space - clear selection
                this.selectedNotes = [];
            }
        }
    }

    handleDoubleClick(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const noteIndex = this.findNoteAt(x, y);
        if (noteIndex !== null) {
            this.deleteNote(noteIndex);
        }
    }

    handleMouseDown(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const noteIndex = this.findNoteAt(x, y);
        if (noteIndex !== null && this.tool === 'select') {
            this.dragging = true;
            this.dragNote = noteIndex;
            this.dragStartY = y;
            this.dragStartMs = this.notes[noteIndex].ms;

            // Add to selection if not already selected
            if (!this.selectedNotes.includes(noteIndex)) {
                if (e.shiftKey) {
                    this.selectedNotes.push(noteIndex);
                } else {
                    this.selectedNotes = [noteIndex];
                }
            }
        } else if (this.tool === 'select' && noteIndex === null) {
            // Start box selection
            this.isBoxSelecting = true;
            this.boxSelectStart = { x, y };
            this.boxSelectEnd = { x, y };
        }
    }

    handleMouseMove(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        if (this.dragging && this.dragNote !== null) {
            const startMs = this.yToTime(this.dragStartY);
            const currentMs = this.yToTime(y);
            const deltaMs = startMs - currentMs;

            // Snap to grid using current snap division
            let newMs = this.snapToGrid(this.dragStartMs + deltaMs);
            newMs = Math.max(0, newMs);

            this.notes[this.dragNote].ms = newMs;
            this.notes[this.dragNote].tick = this.msToTick(newMs);
        } else if (this.isBoxSelecting) {
            this.boxSelectEnd = { x, y };
        }
    }

    handleMouseUp(e) {
        if (this.dragging) {
            this.saveHistory();
        }

        // Complete box selection
        if (this.isBoxSelecting && this.boxSelectStart && this.boxSelectEnd) {
            this.completeBoxSelection(e.shiftKey);
        }

        this.dragging = false;
        this.dragNote = null;
        this.isBoxSelecting = false;
        this.boxSelectStart = null;
        this.boxSelectEnd = null;
    }

    completeBoxSelection(addToSelection) {
        if (!this.boxSelectStart || !this.boxSelectEnd) return;

        const minX = Math.min(this.boxSelectStart.x, this.boxSelectEnd.x);
        const maxX = Math.max(this.boxSelectStart.x, this.boxSelectEnd.x);
        const minY = Math.min(this.boxSelectStart.y, this.boxSelectEnd.y);
        const maxY = Math.max(this.boxSelectStart.y, this.boxSelectEnd.y);

        const notesInBox = [];
        this.notes.forEach((note, index) => {
            const noteY = this.timeToY(note.ms);
            const noteX = this.laneToX(note.lane, noteY);

            if (noteX >= minX && noteX <= maxX && noteY >= minY && noteY <= maxY) {
                notesInBox.push(index);
            }
        });

        if (addToSelection) {
            // Add to existing selection
            notesInBox.forEach(i => {
                if (!this.selectedNotes.includes(i)) {
                    this.selectedNotes.push(i);
                }
            });
        } else {
            // Replace selection
            this.selectedNotes = notesInBox;
        }
    }

    handleWheel(e) {
        e.preventDefault();

        if (e.ctrlKey || e.metaKey) {
            // Zoom
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            this.setZoom(this.zoom * delta);
        } else {
            // Scroll timeline (scroll down = forward in time, scroll up = back in time)
            // Increased sensitivity: deltaY * 8 for faster scrolling
            const scrollAmount = e.deltaY * 8;
            this.targetScroll = Math.max(0, Math.min(this.getMaxScrollMs(),
                this.targetScroll + scrollAmount));
            this.scrollPosition = this.targetScroll;
            this.updateScrollbar();
            this.updateTimeDisplay();

            // Sync audio if not playing
            if (this.audio && this.hasAudio && !this.isPlaying) {
                this.audio.currentTime = this.scrollPosition / 1000;
            }
        }
    }

    findNoteAt(x, y) {
        // Check notes from closest (bottom) to furthest (top) for better hit detection
        const sortedIndices = this.notes
            .map((note, i) => ({ i, y: this.timeToY(note.ms) }))
            .sort((a, b) => b.y - a.y) // Closest first
            .map(item => item.i);

        for (const i of sortedIndices) {
            const note = this.notes[i];
            const noteY = this.timeToY(note.ms);
            const noteX = this.laneToX(note.lane);
            const noteRadius = this.getNoteRadius();

            const dist = Math.sqrt((x - noteX) ** 2 + (y - noteY) ** 2);
            if (dist < noteRadius + 5) {
                return i;
            }
        }
        return null;
    }

    addNote(x, y) {
        const lane = this.xToLane(x);
        let ms = this.yToTime(y);

        // Snap to grid based on snap division setting
        ms = this.snapToGrid(ms);
        ms = Math.max(0, ms);

        this.notes.push({
            id: Date.now(),
            tick: this.msToTick(ms),
            lane: lane,
            duration: 0,
            ms: ms,
            durationMs: 0,
        });

        this.notes.sort((a, b) => a.ms - b.ms);
        this.saveHistory();
        document.getElementById('note-count').textContent = this.notes.length;
    }

    // Add note at current scroll position in specific lane (Moonscraper 1-5 keys)
    addNoteAtCurrentPosition(lane) {
        let ms = this.scrollPosition;

        // Snap to grid
        ms = this.snapToGrid(ms);
        ms = Math.max(0, ms);

        // Check if note already exists at this position and lane
        const exists = this.notes.some(n =>
            Math.abs(n.ms - ms) < 10 && n.lane === lane
        );
        if (exists) return;

        this.notes.push({
            id: Date.now(),
            tick: this.msToTick(ms),
            lane: lane,
            duration: 0,
            ms: ms,
            durationMs: 0,
        });

        this.notes.sort((a, b) => a.ms - b.ms);
        this.saveHistory();
        document.getElementById('note-count').textContent = this.notes.length;
    }

    deleteNote(index) {
        this.notes.splice(index, 1);
        this.selectedNotes = this.selectedNotes.filter(i => i !== index);
        // Re-index selected notes after deletion
        this.selectedNotes = this.selectedNotes.map(i => i > index ? i - 1 : i);
        this.saveHistory();
        document.getElementById('note-count').textContent = this.notes.length;
    }

    deleteSelectedNotes() {
        if (this.selectedNotes.length === 0) return;

        // Sort in reverse order so indices don't shift during deletion
        const toDelete = [...this.selectedNotes].sort((a, b) => b - a);
        toDelete.forEach(index => {
            this.notes.splice(index, 1);
        });

        this.selectedNotes = [];
        this.saveHistory();
        document.getElementById('note-count').textContent = this.notes.length;
    }

    // Snap time to grid based on current snap division
    snapToGrid(ms) {
        if (!this.gridSnap) return ms;

        const msPerBeat = 60000 / this.bpm;
        const snapMs = msPerBeat / this.snapDivision;
        return Math.round(ms / snapMs) * snapMs;
    }

    toggleGridSnap() {
        this.gridSnap = !this.gridSnap;
        const btn = document.getElementById('snap-toggle');
        if (btn) {
            btn.classList.toggle('active', this.gridSnap);
        }
    }

    toggleWaveform() {
        this.showWaveform = !this.showWaveform;
        const btn = document.getElementById('waveform-toggle');
        if (btn) {
            btn.classList.toggle('active', this.showWaveform);
        }
    }

    increaseSnapDivision() {
        const divisions = [1, 2, 4, 8, 12, 16];
        const currentIndex = divisions.indexOf(this.snapDivision);
        if (currentIndex < divisions.length - 1) {
            this.snapDivision = divisions[currentIndex + 1];
            const select = document.getElementById('snap-select');
            if (select) select.value = this.snapDivision;
        }
    }

    decreaseSnapDivision() {
        const divisions = [1, 2, 4, 8, 12, 16];
        const currentIndex = divisions.indexOf(this.snapDivision);
        if (currentIndex > 0) {
            this.snapDivision = divisions[currentIndex - 1];
            const select = document.getElementById('snap-select');
            if (select) select.value = this.snapDivision;
        }
    }

    // Navigate by measure (4 beats)
    navigateMeasure(direction) {
        const msPerMeasure = (60000 / this.bpm) * 4;
        this.targetScroll = Math.max(0, this.scrollPosition + (direction * msPerMeasure));
        this.scrollPosition = this.targetScroll;
        this.updateScrollbar();
        this.updateTimeDisplay();

        // Sync audio if available
        if (this.audio && this.hasAudio) {
            this.audio.currentTime = this.scrollPosition / 1000;
        }
    }

    // Scroll by a given amount in milliseconds
    scrollBy(deltaMs) {
        this.targetScroll = Math.max(0, Math.min(this.getMaxScrollMs(),
            this.scrollPosition + deltaMs));
        this.scrollPosition = this.targetScroll;
        this.updateScrollbar();
        this.updateTimeDisplay();

        // Sync audio if available and not playing
        if (this.audio && this.hasAudio && !this.isPlaying) {
            this.audio.currentTime = this.scrollPosition / 1000;
        }
    }

    // Jump to the start of the chart
    scrollToStart() {
        this.targetScroll = 0;
        this.scrollPosition = 0;
        this.updateScrollbar();
        this.updateTimeDisplay();

        if (this.audio && this.hasAudio) {
            this.audio.currentTime = 0;
        }
    }

    // Jump to the end of the chart
    scrollToEnd() {
        const maxMs = this.getMaxScrollMs();
        this.targetScroll = maxMs;
        this.scrollPosition = maxMs;
        this.updateScrollbar();
        this.updateTimeDisplay();

        if (this.audio && this.hasAudio) {
            this.audio.currentTime = maxMs / 1000;
        }
    }

    // Select all visible notes
    selectAllNotes() {
        this.selectedNotes = this.notes.map((_, i) => i);
    }

    // Copy selected notes to clipboard
    copySelectedNotes() {
        if (this.selectedNotes.length === 0) return;

        // Get the earliest note time as reference
        const selectedNoteObjs = this.selectedNotes.map(i => this.notes[i]);
        const minMs = Math.min(...selectedNoteObjs.map(n => n.ms));

        // Store notes with relative timing
        this.clipboard = selectedNoteObjs.map(n => ({
            lane: n.lane,
            relativeMs: n.ms - minMs,
            duration: n.duration,
            durationMs: n.durationMs,
        }));
    }

    // Cut selected notes
    cutSelectedNotes() {
        this.copySelectedNotes();
        this.deleteSelectedNotes();
    }

    // Paste notes at current scroll position
    pasteNotes() {
        if (this.clipboard.length === 0) return;

        const baseMs = this.snapToGrid(this.scrollPosition);

        this.clipboard.forEach(clipNote => {
            const ms = baseMs + clipNote.relativeMs;
            this.notes.push({
                id: Date.now() + Math.random(),
                tick: this.msToTick(ms),
                lane: clipNote.lane,
                duration: clipNote.duration,
                ms: ms,
                durationMs: clipNote.durationMs,
            });
        });

        this.notes.sort((a, b) => a.ms - b.ms);
        this.saveHistory();
        document.getElementById('note-count').textContent = this.notes.length;
    }

    saveHistory() {
        this.historyIndex++;
        this.history = this.history.slice(0, this.historyIndex);
        this.history.push(JSON.stringify(this.notes));
        if (this.history.length > 50) {
            this.history.shift();
            this.historyIndex--;
        }
    }

    undo() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            this.notes = JSON.parse(this.history[this.historyIndex]);
            this.selectedNotes = [];
            document.getElementById('note-count').textContent = this.notes.length;
        }
    }

    redo() {
        if (this.historyIndex < this.history.length - 1) {
            this.historyIndex++;
            this.notes = JSON.parse(this.history[this.historyIndex]);
            this.selectedNotes = [];
            document.getElementById('note-count').textContent = this.notes.length;
        }
    }

    applyChanges() {
        const event = new CustomEvent('chartEdited', {
            detail: {
                notes: this.notes.map(n => ({
                    tick: n.tick,
                    lane: n.lane,
                    duration: n.duration,
                })),
            }
        });
        this.container.dispatchEvent(event);
    }

    getNotes() {
        return this.notes.map(n => ({
            tick: n.tick,
            lane: n.lane,
            duration: n.duration,
        }));
    }

    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        if (this.audio) {
            this.audio.pause();
            this.audio.src = '';
            this.audio = null;
        }
    }
}

// Export for use
window.ChartEditor = ChartEditor;
