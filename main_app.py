"""
Clone Hero Chart Maker - Main Application
Unified interface for all features: MIDI recording, chart editing, library management, and Spotify search
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from typing import Optional, List
import os

from midi_capture import MIDICapture
from chart_generator import ChartGenerator
from chart_parser import Chart, ChartParser, Difficulty, Instrument
from chorus_api import ChorusAPI, SearchParams, Chart as ChorusChart
from download_manager import DownloadManager


class CloneHeroChartMaker(tk.Tk):
    """Main application window with all features."""

    def __init__(self):
        super().__init__()

        self.title("Clone Hero Chart Maker - Complete Suite")
        self.geometry("1400x900")

        # Initialize components
        self.midi_capture = MIDICapture()
        self.chart_generator = ChartGenerator()
        self.chorus_api = ChorusAPI()
        self.download_manager = None

        # State
        self.current_chart: Optional[Chart] = None
        self.is_recording = False
        self.search_results: List[ChorusChart] = []

        # Setup UI
        self.create_menu()
        self.create_main_interface()

        # Load settings
        self.load_settings()

    def create_menu(self):
        """Create menu bar."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Chart", command=self.new_chart)
        file_menu.add_command(label="Open Chart...", command=self.open_chart)
        file_menu.add_command(label="Save Chart", command=self.save_chart)
        file_menu.add_command(label="Save As...", command=self.save_chart_as)
        file_menu.add_separator()
        file_menu.add_command(label="Settings", command=self.show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="MIDI Recording", command=lambda: self.notebook.select(0))
        tools_menu.add_command(label="Chart Library", command=lambda: self.notebook.select(1))
        tools_menu.add_command(label="Spotify Search", command=lambda: self.notebook.select(2))
        tools_menu.add_separator()
        tools_menu.add_command(label="Visual Editor", command=self.launch_visual_editor)

        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)

    def create_main_interface(self):
        """Create tabbed interface."""
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: MIDI Recording
        self.create_midi_tab()

        # Tab 2: Chart Library (Bridge)
        self.create_library_tab()

        # Tab 3: Spotify Search
        self.create_spotify_tab()

        # Tab 4: Download Manager
        self.create_downloads_tab()

        # Status bar
        self.create_status_bar()

    def create_midi_tab(self):
        """Create MIDI recording tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🎸 MIDI Recording")

        # Main container
        container = ttk.Frame(tab)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Device & Settings
        left_panel = ttk.LabelFrame(container, text="MIDI Settings", padding=10)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        # MIDI Device Selection
        ttk.Label(left_panel, text="MIDI Device:").pack(anchor=tk.W, pady=(0, 5))
        self.midi_device_combo = ttk.Combobox(left_panel, state="readonly", width=40)
        self.midi_device_combo.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(left_panel, text="Refresh Devices",
                  command=self.refresh_midi_devices).pack(fill=tk.X, pady=(0, 20))

        # Song Metadata
        ttk.Label(left_panel, text="Song Metadata",
                 font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))

        ttk.Label(left_panel, text="Song Name:").pack(anchor=tk.W)
        self.song_name_entry = ttk.Entry(left_panel, width=40)
        self.song_name_entry.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(left_panel, text="Artist:").pack(anchor=tk.W)
        self.artist_entry = ttk.Entry(left_panel, width=40)
        self.artist_entry.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(left_panel, text="BPM:").pack(anchor=tk.W)
        self.bpm_entry = ttk.Entry(left_panel, width=40)
        self.bpm_entry.insert(0, "120")
        self.bpm_entry.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(left_panel, text="Difficulty:").pack(anchor=tk.W)
        self.difficulty_combo = ttk.Combobox(left_panel, values=["Easy", "Medium", "Hard", "Expert"],
                                            state="readonly", width=38)
        self.difficulty_combo.set("Expert")
        self.difficulty_combo.pack(fill=tk.X, pady=(0, 20))

        # Recording Controls
        ttk.Label(left_panel, text="Recording",
                 font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))

        self.record_btn = ttk.Button(left_panel, text="🔴 Start Recording",
                                     command=self.toggle_recording)
        self.record_btn.pack(fill=tk.X, pady=(0, 5))

        self.save_midi_chart_btn = ttk.Button(left_panel, text="💾 Generate Chart",
                                              command=self.generate_chart_from_midi,
                                              state=tk.DISABLED)
        self.save_midi_chart_btn.pack(fill=tk.X)

        # Right panel - Recording Log
        right_panel = ttk.LabelFrame(container, text="Recording Log", padding=10)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        self.midi_log = scrolledtext.ScrolledText(right_panel, height=30, width=60)
        self.midi_log.pack(fill=tk.BOTH, expand=True)

        # Configure grid weights
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=2)
        container.rowconfigure(0, weight=1)

        # Initialize
        self.refresh_midi_devices()

    def create_library_tab(self):
        """Create chart library browser tab (Bridge features)."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📚 Chart Library")

        # Main container
        container = ttk.Frame(tab)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Search panel
        search_panel = ttk.LabelFrame(container, text="Search Chorus Encore Database", padding=10)
        search_panel.pack(fill=tk.X, pady=(0, 10))

        # Search bar
        search_frame = ttk.Frame(search_panel)
        search_frame.pack(fill=tk.X)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.library_search_entry = ttk.Entry(search_frame, width=50)
        self.library_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.library_search_entry.bind("<Return>", lambda e: self.search_library())

        ttk.Button(search_frame, text="🔍 Search",
                  command=self.search_library).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(search_frame, text="Advanced",
                  command=self.show_advanced_search).pack(side=tk.LEFT)

        # Filters
        filter_frame = ttk.Frame(search_panel)
        filter_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(filter_frame, text="Instrument:").pack(side=tk.LEFT, padx=(0, 5))
        self.instrument_filter = ttk.Combobox(filter_frame,
                                             values=["All", "Guitar", "Bass", "Drums", "Keys"],
                                             state="readonly", width=15)
        self.instrument_filter.set("All")
        self.instrument_filter.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(filter_frame, text="Difficulty:").pack(side=tk.LEFT, padx=(0, 5))
        self.diff_filter = ttk.Combobox(filter_frame,
                                       values=["All", "Easy", "Medium", "Hard", "Expert"],
                                       state="readonly", width=15)
        self.diff_filter.set("All")
        self.diff_filter.pack(side=tk.LEFT)

        # Results
        results_panel = ttk.LabelFrame(container, text="Search Results", padding=10)
        results_panel.pack(fill=tk.BOTH, expand=True)

        # Results table
        columns = ("name", "artist", "charter", "difficulty", "length")
        self.library_tree = ttk.Treeview(results_panel, columns=columns, show="tree headings", height=20)

        self.library_tree.heading("#0", text="")
        self.library_tree.heading("name", text="Song")
        self.library_tree.heading("artist", text="Artist")
        self.library_tree.heading("charter", text="Charter")
        self.library_tree.heading("difficulty", text="Difficulty")
        self.library_tree.heading("length", text="Length")

        self.library_tree.column("#0", width=50)
        self.library_tree.column("name", width=250)
        self.library_tree.column("artist", width=200)
        self.library_tree.column("charter", width=150)
        self.library_tree.column("difficulty", width=100)
        self.library_tree.column("length", width=80)

        # Scrollbar
        scrollbar = ttk.Scrollbar(results_panel, orient=tk.VERTICAL, command=self.library_tree.yview)
        self.library_tree.configure(yscrollcommand=scrollbar.set)

        self.library_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons
        button_frame = ttk.Frame(results_panel)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="📥 Download Selected",
                  command=self.download_selected_charts).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="📥 Download All Results",
                  command=self.download_all_results).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="ℹ️ View Details",
                  command=self.view_chart_details).pack(side=tk.LEFT)

    def create_spotify_tab(self):
        """Create Spotify integration tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🎵 Spotify Search")

        # Main container
        container = ttk.Frame(tab)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Info message
        info_frame = ttk.Frame(container)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        info_label = ttk.Label(info_frame,
                              text="🚧 Spotify Integration - Coming Soon!\n\n" +
                                   "This feature will allow you to:\n" +
                                   "• Search your Spotify playlists\n" +
                                   "• Find matching Clone Hero charts\n" +
                                   "• Auto-download charts for your favorite songs\n" +
                                   "• Analyze listening history for chart recommendations",
                              justify=tk.LEFT,
                              font=("Arial", 10))
        info_label.pack(padx=20, pady=20)

        # Placeholder search
        search_frame = ttk.LabelFrame(container, text="Manual Song Search", padding=10)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="Song Name:").pack(anchor=tk.W)
        self.spotify_song_entry = ttk.Entry(search_frame, width=60)
        self.spotify_song_entry.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="Artist:").pack(anchor=tk.W)
        self.spotify_artist_entry = ttk.Entry(search_frame, width=60)
        self.spotify_artist_entry.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(search_frame, text="🔍 Find Charts",
                  command=self.search_spotify_manual).pack()

        # Results
        results_frame = ttk.LabelFrame(container, text="Matching Charts", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)

        self.spotify_results_text = scrolledtext.ScrolledText(results_frame, height=20)
        self.spotify_results_text.pack(fill=tk.BOTH, expand=True)

    def create_downloads_tab(self):
        """Create download manager tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📥 Downloads")

        container = ttk.Frame(tab)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Settings
        settings_frame = ttk.LabelFrame(container, text="Download Settings", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(settings_frame, text="Clone Hero Songs Folder:").pack(anchor=tk.W)

        path_frame = ttk.Frame(settings_frame)
        path_frame.pack(fill=tk.X, pady=(5, 10))

        self.ch_path_entry = ttk.Entry(path_frame, width=70)
        self.ch_path_entry.insert(0, r"C:\Program Files\Clone Hero\Songs")
        self.ch_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(path_frame, text="Browse...",
                  command=self.browse_ch_folder).pack(side=tk.LEFT)

        ttk.Checkbutton(settings_frame, text="Include video backgrounds",
                       variable=tk.BooleanVar(value=False)).pack(anchor=tk.W)

        # Queue
        queue_frame = ttk.LabelFrame(container, text="Download Queue", padding=10)
        queue_frame.pack(fill=tk.BOTH, expand=True)

        # Queue list
        columns = ("song", "artist", "status", "progress")
        self.queue_tree = ttk.Treeview(queue_frame, columns=columns, show="headings", height=15)

        self.queue_tree.heading("song", text="Song")
        self.queue_tree.heading("artist", text="Artist")
        self.queue_tree.heading("status", text="Status")
        self.queue_tree.heading("progress", text="Progress")

        self.queue_tree.column("song", width=300)
        self.queue_tree.column("artist", width=200)
        self.queue_tree.column("status", width=100)
        self.queue_tree.column("progress", width=100)

        scrollbar = ttk.Scrollbar(queue_frame, orient=tk.VERTICAL, command=self.queue_tree.yview)
        self.queue_tree.configure(yscrollcommand=scrollbar.set)

        self.queue_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons
        button_frame = ttk.Frame(queue_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="⏸️ Pause", command=self.pause_downloads).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="▶️ Resume", command=self.resume_downloads).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="🗑️ Clear Completed", command=self.clear_completed).pack(side=tk.LEFT)

    def create_status_bar(self):
        """Create status bar at bottom."""
        self.status_bar = ttk.Label(self, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # MIDI Recording Functions
    def refresh_midi_devices(self):
        """Refresh MIDI device list."""
        devices = self.midi_capture.list_midi_devices()
        self.midi_device_combo['values'] = devices if devices else ["No devices found"]
        if devices:
            self.midi_device_combo.current(0)
        self.log_midi(f"Found {len(devices)} MIDI device(s)")

    def toggle_recording(self):
        """Start/stop MIDI recording."""
        if not self.is_recording:
            # Start recording
            device_name = self.midi_device_combo.get()
            if "No devices" in device_name:
                messagebox.showerror("Error", "No MIDI devices available!")
                return

            self.is_recording = True
            self.record_btn.config(text="⏹️ Stop Recording")
            self.log_midi("Starting recording...")

            # Start recording in background thread
            thread = threading.Thread(target=self._record_midi, args=(device_name,))
            thread.daemon = True
            thread.start()

        else:
            # Stop recording
            self.is_recording = False
            self.midi_capture.stop_recording()
            self.record_btn.config(text="🔴 Start Recording")
            self.save_midi_chart_btn.config(state=tk.NORMAL)

            notes = self.midi_capture.get_notes()
            self.log_midi(f"Recording stopped. Captured {len(notes)} notes")

    def _record_midi(self, device_name):
        """Background MIDI recording."""
        try:
            self.midi_capture.start_recording(device_name if device_name != "Use default" else None)
        except Exception as e:
            self.log_midi(f"Error: {e}")
            self.is_recording = False

    def generate_chart_from_midi(self):
        """Generate chart from recorded MIDI notes."""
        notes = self.midi_capture.get_notes()
        if not notes:
            messagebox.showwarning("Warning", "No notes recorded!")
            return

        song_name = self.song_name_entry.get() or "Untitled"
        artist = self.artist_entry.get() or "Unknown"
        try:
            bpm = float(self.bpm_entry.get())
        except:
            bpm = 120.0

        difficulty = self.difficulty_combo.get()

        # Generate chart
        output_dir = os.path.join(os.getcwd(), "output", song_name.replace(" ", "_"))
        os.makedirs(output_dir, exist_ok=True)

        chart_path = os.path.join(output_dir, "notes.chart")
        ini_path = os.path.join(output_dir, "song.ini")

        self.chart_generator.generate_chart_file(
            midi_notes=notes,
            output_path=chart_path,
            song_name=song_name,
            artist=artist,
            bpm=bpm,
            difficulty=difficulty
        )

        self.chart_generator.generate_song_ini(
            output_path=ini_path,
            song_name=song_name,
            artist=artist
        )

        self.log_midi(f"\nChart generated successfully!")
        self.log_midi(f"Location: {output_dir}")

        messagebox.showinfo("Success", f"Chart created!\n\nLocation: {output_dir}\n\nAdd audio file (song.ogg) and copy to Clone Hero.")

    def log_midi(self, message):
        """Log message to MIDI tab."""
        self.midi_log.insert(tk.END, message + "\n")
        self.midi_log.see(tk.END)

    # Library Functions
    def search_library(self):
        """Search Chorus library."""
        query = self.library_search_entry.get()
        if not query:
            messagebox.showwarning("Warning", "Please enter a search term")
            return

        self.status_bar.config(text="Searching...")
        self.update()

        try:
            params = SearchParams(query=query, per_page=50)
            result = self.chorus_api.search(params)

            # Clear previous results
            for item in self.library_tree.get_children():
                self.library_tree.delete(item)

            # Add results
            self.search_results = result.charts
            for i, chart in enumerate(result.charts):
                length_str = f"{chart.song_length // 60}:{chart.song_length % 60:02d}"
                diff_str = f"G:{chart.diff_guitar} D:{chart.diff_drums}"

                self.library_tree.insert("", tk.END, iid=str(i),
                                        values=(chart.name, chart.artist, chart.charter,
                                               diff_str, length_str))

            self.status_bar.config(text=f"Found {result.total_found:,} charts ({result.search_time:.2f}s)")

        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {e}")
            self.status_bar.config(text="Search failed")

    def download_selected_charts(self):
        """Download selected charts from library."""
        selection = self.library_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select charts to download")
            return

        charts = [self.search_results[int(item)] for item in selection]
        self._download_charts(charts)

    def download_all_results(self):
        """Download all search results."""
        if not self.search_results:
            messagebox.showwarning("Warning", "No search results to download")
            return

        if len(self.search_results) > 10:
            if not messagebox.askyesno("Confirm", f"Download {len(self.search_results)} charts?"):
                return

        self._download_charts(self.search_results)

    def _download_charts(self, charts):
        """Start downloading charts."""
        ch_path = self.ch_path_entry.get()
        if not os.path.isdir(ch_path):
            messagebox.showerror("Error", "Invalid Clone Hero path")
            return

        if not self.download_manager:
            self.download_manager = DownloadManager(ch_path)

        for chart in charts:
            task = self.download_manager.add_download(chart, include_video=False)

            # Add to queue display
            self.queue_tree.insert("", tk.END,
                                  values=(chart.name, chart.artist, "Queued", "0%"))

        self.notebook.select(3)  # Switch to downloads tab
        messagebox.showinfo("Success", f"Added {len(charts)} chart(s) to download queue")

    # Spotify Functions
    def search_spotify_manual(self):
        """Manual song search (placeholder for Spotify)."""
        song = self.spotify_song_entry.get()
        artist = self.spotify_artist_entry.get()

        if not song:
            messagebox.showwarning("Warning", "Please enter a song name")
            return

        # Search using Chorus API
        query = f"{song} {artist}".strip()
        try:
            params = SearchParams(query=query, per_page=10)
            result = self.chorus_api.search(params)

            self.spotify_results_text.delete(1.0, tk.END)
            self.spotify_results_text.insert(tk.END, f"Found {result.total_found} charts for '{query}':\n\n")

            for chart in result.charts[:10]:
                self.spotify_results_text.insert(tk.END,
                    f"🎸 {chart.name} - {chart.artist}\n" +
                    f"   Charter: {chart.charter}\n" +
                    f"   Difficulty: Guitar:{chart.diff_guitar} Bass:{chart.diff_bass} Drums:{chart.diff_drums}\n\n")

        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {e}")

    # Helper Functions
    def browse_ch_folder(self):
        """Browse for Clone Hero folder."""
        folder = filedialog.askdirectory(title="Select Clone Hero Songs Folder")
        if folder:
            self.ch_path_entry.delete(0, tk.END)
            self.ch_path_entry.insert(0, folder)

    def show_advanced_search(self):
        """Show advanced search dialog."""
        messagebox.showinfo("Advanced Search", "Advanced search coming soon!\n\nFeatures:\n• Filter by difficulty\n• Filter by features (HOPO, tap, etc.)\n• Date ranges\n• And more...")

    def view_chart_details(self):
        """View selected chart details."""
        selection = self.library_tree.selection()
        if not selection:
            return

        chart = self.search_results[int(selection[0])]
        details = (
            f"Song: {chart.name}\n"
            f"Artist: {chart.artist}\n"
            f"Album: {chart.album}\n"
            f"Genre: {chart.genre}\n"
            f"Year: {chart.year}\n"
            f"Charter: {chart.charter}\n\n"
            f"Difficulties:\n"
            f"  Guitar: {chart.diff_guitar}\n"
            f"  Bass: {chart.diff_bass}\n"
            f"  Drums: {chart.diff_drums}\n"
            f"  Keys: {chart.diff_keys}\n\n"
            f"Features:\n"
            f"  Solo Sections: {'Yes' if chart.hasSoloSections else 'No'}\n"
            f"  Tap Notes: {'Yes' if chart.hasTapNotes else 'No'}\n"
            f"  Open Notes: {'Yes' if chart.hasOpenNotes else 'No'}\n"
            f"  Video: {'Yes' if chart.hasVideoBackground else 'No'}\n"
        )
        messagebox.showinfo("Chart Details", details)

    # Menu Functions
    def new_chart(self):
        """Create new chart."""
        self.current_chart = Chart()
        messagebox.showinfo("New Chart", "New chart created")

    def open_chart(self):
        """Open existing chart."""
        filename = filedialog.askopenfilename(
            title="Open Chart",
            filetypes=[("Chart files", "*.chart"), ("All files", "*.*")]
        )
        if filename:
            try:
                self.current_chart = ChartParser.parse_file(filename)
                messagebox.showinfo("Success", f"Loaded: {self.current_chart.name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load chart: {e}")

    def save_chart(self):
        """Save current chart."""
        if not self.current_chart:
            messagebox.showwarning("Warning", "No chart to save")
            return

        # Implement save logic
        messagebox.showinfo("Save", "Save functionality coming soon")

    def save_chart_as(self):
        """Save chart as new file."""
        filename = filedialog.asksaveasfilename(
            title="Save Chart As",
            defaultextension=".chart",
            filetypes=[("Chart files", "*.chart"), ("All files", "*.*")]
        )
        if filename:
            # Implement save logic
            messagebox.showinfo("Save As", f"Will save to: {filename}")

    def show_settings(self):
        """Show settings dialog."""
        messagebox.showinfo("Settings", "Settings dialog coming soon")

    def launch_visual_editor(self):
        """Launch visual editor."""
        import subprocess
        import sys
        subprocess.Popen([sys.executable, "visual_editor.py"])

    def show_documentation(self):
        """Show documentation."""
        import webbrowser
        readme_path = os.path.join(os.getcwd(), "README.md")
        if os.path.exists(readme_path):
            webbrowser.open(readme_path)
        else:
            messagebox.showinfo("Documentation", "See README.md and FEATURES.md")

    def show_about(self):
        """Show about dialog."""
        about_text = (
            "Clone Hero Chart Maker\n"
            "Complete Suite v1.0\n\n"
            "Features:\n"
            "• MIDI Guitar Recording\n"
            "• Visual Chart Editor\n"
            "• Chart Library Browser (100,000+ charts)\n"
            "• Spotify Integration (Coming Soon)\n\n"
            "Integrates features from:\n"
            "• Moonscraper Chart Editor\n"
            "• Bridge\n"
            "• spotify-clonehero\n"
        )
        messagebox.showinfo("About", about_text)

    def load_settings(self):
        """Load saved settings."""
        # Implement settings loading
        pass

    def pause_downloads(self):
        """Pause download manager."""
        if self.download_manager:
            self.download_manager.stop()

    def resume_downloads(self):
        """Resume downloads."""
        if self.download_manager:
            self.download_manager.start()

    def clear_completed(self):
        """Clear completed downloads."""
        if self.download_manager:
            self.download_manager.clear_completed()


def main():
    """Launch main application."""
    app = CloneHeroChartMaker()
    app.mainloop()


if __name__ == "__main__":
    main()
