"""
Clone Hero Chart Maker - ALL-IN-ONE LAUNCHER
Single UI with access to all features
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import subprocess
import sys
import os
import webbrowser

class AIOLauncher(tk.Tk):
    """All-in-One launcher with tabbed interface for all features."""

    def __init__(self):
        super().__init__()

        self.title("Clone Hero Chart Maker - All-In-One Suite")
        self.geometry("1200x800")

        # Configure style
        self.configure(bg='#1e1e1e')
        self.setup_styles()

        # State
        self.web_app_process = None
        self.visual_editor_process = None

        # Create UI
        self.create_header()
        self.create_main_tabs()
        self.create_status_bar()

    def setup_styles(self):
        """Setup dark theme styles."""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure colors
        bg_dark = '#1e1e1e'
        bg_medium = '#2d2d2d'
        bg_light = '#3d3d3d'
        fg_color = '#ffffff'
        accent = '#0e639c'

        style.configure('TFrame', background=bg_dark)
        style.configure('TLabelframe', background=bg_dark, foreground=fg_color)
        style.configure('TLabelframe.Label', background=bg_dark, foreground=fg_color)
        style.configure('TLabel', background=bg_dark, foreground=fg_color)
        style.configure('TButton', background=bg_medium, foreground=fg_color)
        style.map('TButton', background=[('active', accent)])
        style.configure('TNotebook', background=bg_dark, borderwidth=0)
        style.configure('TNotebook.Tab', background=bg_medium, foreground=fg_color, padding=[20, 10])
        style.map('TNotebook.Tab', background=[('selected', accent)], foreground=[('selected', fg_color)])

    def create_header(self):
        """Create header with title and quick actions."""
        header = tk.Frame(self, bg='#0e639c', height=80)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        # Title
        title = tk.Label(header,
                        text="🎸 CLONE HERO CHART MAKER",
                        font=('Arial', 24, 'bold'),
                        bg='#0e639c',
                        fg='white')
        title.pack(side=tk.LEFT, padx=20, pady=10)

        # Subtitle
        subtitle = tk.Label(header,
                          text="All-In-One Suite: AI Audio Conversion • Guitar Recording • Chart Library • Visual Editing",
                          font=('Arial', 10),
                          bg='#0e639c',
                          fg='white')
        subtitle.pack(side=tk.LEFT, padx=20)

        # Quick actions
        quick_frame = tk.Frame(header, bg='#0e639c')
        quick_frame.pack(side=tk.RIGHT, padx=20)

        tk.Button(quick_frame, text="📖 Help", command=self.show_help,
                 bg='#2d2d2d', fg='white', padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(quick_frame, text="⚙️ Settings", command=self.show_settings,
                 bg='#2d2d2d', fg='white', padx=15, pady=5).pack(side=tk.LEFT, padx=5)

    def create_main_tabs(self):
        """Create main tabbed interface."""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Tab 1: Dashboard / Home
        self.create_dashboard_tab()

        # Tab 2: AI Audio Conversion (Your GitHub features)
        self.create_ai_audio_tab()

        # Tab 3: MIDI Recording
        self.create_midi_tab()

        # Tab 4: Chart Library (Chorus)
        self.create_library_tab()

        # Tab 5: Tools & Editors
        self.create_tools_tab()

    def create_dashboard_tab(self):
        """Create dashboard/home tab with quick access."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🏠 Dashboard")

        # Main container
        container = tk.Frame(tab, bg='#1e1e1e')
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Welcome message
        welcome = tk.Label(container,
                          text="Welcome to Clone Hero Chart Maker",
                          font=('Arial', 20, 'bold'),
                          bg='#1e1e1e',
                          fg='white')
        welcome.pack(pady=(0, 10))

        subtitle = tk.Label(container,
                           text="Choose your workflow or explore features in the tabs above",
                           font=('Arial', 12),
                           bg='#1e1e1e',
                           fg='#cccccc')
        subtitle.pack(pady=(0, 30))

        # Quick action cards
        cards_frame = tk.Frame(container, bg='#1e1e1e')
        cards_frame.pack(fill=tk.BOTH, expand=True)

        # Row 1
        row1 = tk.Frame(cards_frame, bg='#1e1e1e')
        row1.pack(fill=tk.X, pady=10)

        self.create_card(row1,
                        "🤖 AI Audio Conversion",
                        "Convert any audio file or YouTube video to charts using AI",
                        "Web App (Recommended)",
                        self.launch_web_app).pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)

        self.create_card(row1,
                        "🎸 Guitar Recording",
                        "Record from Xbox 360 Xplorer, MIDI guitar, or keyboard",
                        "Guitar Creator",
                        lambda: self.notebook.select(2)).pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)

        # Row 2
        row2 = tk.Frame(cards_frame, bg='#1e1e1e')
        row2.pack(fill=tk.X, pady=10)

        self.create_card(row2,
                        "📚 Chart Library",
                        "Search and download from 100,000+ charts",
                        "Browse Chorus",
                        lambda: self.notebook.select(3)).pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)

        self.create_card(row2,
                        "🎮 Visual Editor",
                        "Edit charts with highway view and note placement",
                        "Launch Editor",
                        self.launch_visual_editor).pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)

        # Row 3
        row3 = tk.Frame(cards_frame, bg='#1e1e1e')
        row3.pack(fill=tk.X, pady=10)

        self.create_card(row3,
                        "📥 Batch Convert",
                        "Convert multiple MIDI files at once",
                        "CLI Tools",
                        lambda: self.notebook.select(4)).pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)

        self.create_card(row3,
                        "📖 Documentation",
                        "View guides, tutorials, and feature documentation",
                        "Open Docs",
                        self.show_documentation).pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)

        # System status
        status_frame = tk.LabelFrame(container, text="System Status", bg='#2d2d2d', fg='white', font=('Arial', 10, 'bold'))
        status_frame.pack(fill=tk.X, pady=(30, 0))

        self.status_text = scrolledtext.ScrolledText(status_frame, height=8, bg='#1e1e1e', fg='#00ff00', font=('Consolas', 9))
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Check system
        self.check_system_status()

    def create_card(self, parent, title, description, button_text, command):
        """Create a feature card."""
        card = tk.Frame(parent, bg='#2d2d2d', relief=tk.RAISED, borderwidth=2)

        tk.Label(card, text=title, font=('Arial', 14, 'bold'),
                bg='#2d2d2d', fg='white').pack(pady=(15, 5))

        tk.Label(card, text=description, font=('Arial', 10),
                bg='#2d2d2d', fg='#cccccc', wraplength=250).pack(pady=10, padx=15)

        tk.Button(card, text=button_text, command=command,
                 bg='#0e639c', fg='white', font=('Arial', 11, 'bold'),
                 padx=20, pady=10, cursor='hand2').pack(pady=(10, 15))

        return card

    def create_ai_audio_tab(self):
        """Create AI audio conversion tab (launches web app)."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🤖 AI Audio")

        container = tk.Frame(tab, bg='#1e1e1e')
        container.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        # Title
        tk.Label(container, text="AI-Powered Audio to Chart Conversion",
                font=('Arial', 18, 'bold'), bg='#1e1e1e', fg='white').pack(pady=(0, 20))

        # Features
        features_frame = tk.Frame(container, bg='#2d2d2d', relief=tk.RAISED, borderwidth=2)
        features_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        tk.Label(features_frame, text="✨ Features", font=('Arial', 14, 'bold'),
                bg='#2d2d2d', fg='white').pack(pady=10)

        features = [
            "🎵 AI Stem Separation - Demucs separates vocals, drums, bass, guitar, piano",
            "🎼 Neural Audio-to-MIDI - Spotify's Basic Pitch transcription",
            "📹 YouTube Integration - Paste URL, get chart",
            "🎹 Web-based Chart Editor - Edit in browser with playback",
            "📊 Waveform Visualization - See audio while editing",
            "🎯 Quality Assurance - Automatic issue detection"
        ]

        for feature in features:
            tk.Label(features_frame, text=feature, font=('Arial', 11),
                    bg='#2d2d2d', fg='#cccccc', anchor='w').pack(fill=tk.X, padx=30, pady=5)

        # Launch button
        button_frame = tk.Frame(container, bg='#1e1e1e')
        button_frame.pack(pady=30)

        self.web_app_btn = tk.Button(button_frame,
                                     text="🚀 Launch Web App (Port 5000)",
                                     command=self.launch_web_app,
                                     bg='#0e639c', fg='white',
                                     font=('Arial', 14, 'bold'),
                                     padx=30, pady=15, cursor='hand2')
        self.web_app_btn.pack()

        tk.Label(button_frame, text="Will open in your default browser",
                font=('Arial', 10), bg='#1e1e1e', fg='#888888').pack(pady=5)

        # Status
        self.web_app_status = tk.Label(container, text="Status: Not running",
                                       font=('Arial', 11), bg='#1e1e1e', fg='#cccccc')
        self.web_app_status.pack(pady=10)

    def create_midi_tab(self):
        """Create guitar recording tab (supports both MIDI and game controllers)."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🎸 Guitar Recording")

        container = tk.Frame(tab, bg='#1e1e1e')
        container.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        tk.Label(container, text="Guitar Performance Recording",
                font=('Arial', 18, 'bold'), bg='#1e1e1e', fg='white').pack(pady=(0, 20))

        info = tk.Label(container,
                       text="Record your guitar performance and convert to Clone Hero charts.\n\n"
                            "Supports:\n"
                            "• Game Controllers (Xbox 360 Xplorer, PS2 Guitar, etc.)\n"
                            "• MIDI Guitars and Keyboards\n"
                            "• Real-time capture with sustain detection\n"
                            "• Customizable button/note mapping",
                       font=('Arial', 11), bg='#1e1e1e', fg='#cccccc', justify=tk.LEFT)
        info.pack(pady=20)

        # Device detection
        device_frame = tk.Frame(container, bg='#2d2d2d', relief=tk.RAISED, borderwidth=2)
        device_frame.pack(fill=tk.BOTH, expand=True, pady=20)

        tk.Label(device_frame, text="🔍 Detected Devices", font=('Arial', 14, 'bold'),
                bg='#2d2d2d', fg='white').pack(pady=10)

        self.device_status_label = tk.Label(device_frame, text="Click 'Detect Devices' to scan...",
                                           font=('Arial', 10), bg='#2d2d2d', fg='#cccccc')
        self.device_status_label.pack(pady=10, padx=20)

        detect_btn = tk.Button(device_frame, text="🔄 Detect Devices",
                              command=self.detect_input_devices,
                              bg='#0e639c', fg='white', font=('Arial', 10, 'bold'),
                              padx=20, pady=8)
        detect_btn.pack(pady=10)

        # Launch buttons
        button_frame = tk.Frame(container, bg='#1e1e1e')
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="🎮 Launch Guitar Chart Maker",
                 command=self.launch_guitar_chart_maker,
                 bg='#0e639c', fg='white', font=('Arial', 12, 'bold'),
                 padx=30, pady=15).pack(pady=5)

    def create_library_tab(self):
        """Create chart library tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📚 Chart Library")

        container = tk.Frame(tab, bg='#1e1e1e')
        container.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        tk.Label(container, text="Chart Library - Search 100,000+ Charts",
                font=('Arial', 18, 'bold'), bg='#1e1e1e', fg='white').pack(pady=(0, 20))

        info = tk.Label(container,
                       text="Browse and download charts from the Chorus Encore database.\n\n"
                            "Features:\n"
                            "• Search by song, artist, charter\n"
                            "• Filter by instrument and difficulty\n"
                            "• Download queue with auto-retry\n"
                            "• Direct installation to Clone Hero",
                       font=('Arial', 11), bg='#1e1e1e', fg='#cccccc', justify=tk.LEFT)
        info.pack(pady=20)

        tk.Button(container, text="Launch Library Browser",
                 command=self.launch_library_browser,
                 bg='#0e639c', fg='white', font=('Arial', 12, 'bold'),
                 padx=30, pady=15).pack(pady=20)

    def create_tools_tab(self):
        """Create tools and utilities tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🔧 Tools")

        container = tk.Frame(tab, bg='#1e1e1e')
        container.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        tk.Label(container, text="Tools & Utilities",
                font=('Arial', 18, 'bold'), bg='#1e1e1e', fg='white').pack(pady=(0, 30))

        # Tool buttons
        tools = [
            ("🎮 Visual Chart Editor", "Edit charts with highway view", self.launch_visual_editor),
            ("⌨️ CLI Converter", "Batch convert MIDI files", self.launch_cli_help),
            ("📊 Chart Parser Test", "Test .chart file parsing", self.test_chart_parser),
            ("🔍 System Test", "Verify all components", self.run_system_test),
            ("📁 Open Project Folder", "Browse project files", self.open_project_folder),
        ]

        for title, description, command in tools:
            tool_frame = tk.Frame(container, bg='#2d2d2d', relief=tk.RAISED, borderwidth=1)
            tool_frame.pack(fill=tk.X, pady=10)

            tk.Label(tool_frame, text=title, font=('Arial', 12, 'bold'),
                    bg='#2d2d2d', fg='white', anchor='w').pack(fill=tk.X, padx=20, pady=(10, 0))

            tk.Label(tool_frame, text=description, font=('Arial', 10),
                    bg='#2d2d2d', fg='#cccccc', anchor='w').pack(fill=tk.X, padx=20, pady=(5, 10))

            tk.Button(tool_frame, text="Launch", command=command,
                     bg='#0e639c', fg='white', padx=20, pady=5).pack(anchor='e', padx=20, pady=(0, 10))

    def create_status_bar(self):
        """Create bottom status bar."""
        status_bar = tk.Frame(self, bg='#0e639c', height=30)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)

        self.status_label = tk.Label(status_bar, text="Ready",
                                     bg='#0e639c', fg='white', anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=10)

        # Version info
        tk.Label(status_bar, text="v1.0 - Complete Suite",
                bg='#0e639c', fg='white', anchor=tk.E).pack(side=tk.RIGHT, padx=10)

    # Action methods
    def launch_web_app(self):
        """Launch Flask web app."""
        if self.web_app_process and self.web_app_process.poll() is None:
            messagebox.showinfo("Already Running", "Web app is already running at http://localhost:8080")
            webbrowser.open('http://localhost:8080')
            return

        try:
            self.web_app_process = subprocess.Popen([sys.executable, 'app.py'])
            self.web_app_status.config(text="Status: Starting...", fg='#ffaa00')
            self.status_label.config(text="Launching web app on port 8080...")

            # Wait a bit then open browser
            def open_browser():
                import time
                time.sleep(2)
                webbrowser.open('http://localhost:8080')
                self.web_app_status.config(text="Status: Running on http://localhost:8080", fg='#00ff00')
                self.status_label.config(text="Web app running")

            threading.Thread(target=open_browser, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch web app: {e}")

    def launch_visual_editor(self):
        """Launch visual editor."""
        try:
            self.visual_editor_process = subprocess.Popen([sys.executable, 'visual_editor.py'])
            self.status_label.config(text="Visual editor launched")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch visual editor: {e}")

    def launch_midi_recorder(self):
        """Launch MIDI recorder with GUI."""
        try:
            subprocess.Popen([sys.executable, 'chart_maker_gui.py'])
            self.status_label.config(text="MIDI recorder GUI launched")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch MIDI recorder: {e}")

    def detect_input_devices(self):
        """Detect game controllers and MIDI devices."""
        try:
            import pygame
            from controller_capture import ControllerCapture
            from midi_capture import MIDICapture

            # Detect controllers
            capture = ControllerCapture()
            controllers = capture.list_controllers()
            capture.cleanup()

            # Detect MIDI
            midi_capture = MIDICapture()
            midi_devices = midi_capture.list_midi_devices()

            # Build status message
            status_text = ""

            if controllers:
                status_text += f"🎮 Game Controllers ({len(controllers)}):\n"
                for ctrl in controllers:
                    status_text += f"  • {ctrl}\n"
            else:
                status_text += "🎮 No game controllers detected\n"

            status_text += "\n"

            if midi_devices:
                status_text += f"🎹 MIDI Devices ({len(midi_devices)}):\n"
                for dev in midi_devices:
                    status_text += f"  • {dev}\n"
            else:
                status_text += "🎹 No MIDI devices detected\n"

            if not controllers and not midi_devices:
                status_text += "\n⚠️ Please connect a guitar controller or MIDI device"

            self.device_status_label.config(text=status_text, justify=tk.LEFT)
            self.status_label.config(text="Device scan complete")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to detect devices: {e}")

    def launch_guitar_chart_maker(self):
        """Launch the unified guitar chart maker (supports controllers and MIDI)."""
        try:
            subprocess.Popen([sys.executable, 'guitar_chart_maker.py'])
            self.status_label.config(text="Guitar chart maker launched")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch guitar chart maker: {e}")

    def launch_library_browser(self):
        """Launch library browser (desktop app)."""
        try:
            subprocess.Popen([sys.executable, 'main_app.py'])
            self.status_label.config(text="Library browser launched")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch library browser: {e}")

    def launch_cli_help(self):
        """Show CLI help."""
        help_text = """
CLI Converter Usage:

Basic conversion:
  python -m src.cli input.mid output.chart

With metadata:
  python -m src.cli song.mid song.chart --name "Song Name" --artist "Artist"

MIDI inspection:
  python -m src.cli --inspect song.mid

Preview mode:
  python -m src.cli --preview song.mid

Custom config:
  python -m src.cli input.mid output.chart --config custom.yaml
        """
        messagebox.showinfo("CLI Converter Help", help_text)

    def test_chart_parser(self):
        """Test chart parser."""
        try:
            from chart_parser import Chart, ChartParser
            chart = Chart(name="Test", artist="Test Artist")
            messagebox.showinfo("Success", f"Chart parser working!\n\nCreated: {chart.name} by {chart.artist}")
        except Exception as e:
            messagebox.showerror("Error", f"Chart parser test failed: {e}")

    def run_system_test(self):
        """Run system test."""
        try:
            subprocess.Popen([sys.executable, 'test_system.py'])
            self.status_label.config(text="Running system test...")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run system test: {e}")

    def open_project_folder(self):
        """Open project folder."""
        import platform
        path = os.getcwd()
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def show_help(self):
        """Show help documentation."""
        readme_path = os.path.join(os.getcwd(), "START_HERE.md")
        if os.path.exists(readme_path):
            if sys.platform == "win32":
                os.startfile(readme_path)
            else:
                webbrowser.open(f"file://{readme_path}")
        else:
            messagebox.showinfo("Help",
                              "Documentation:\n\n"
                              "• START_HERE.md - Quick start\n"
                              "• README_COMPLETE.md - Full docs\n"
                              "• FEATURES.md - Feature list")

    def show_settings(self):
        """Show settings dialog."""
        messagebox.showinfo("Settings", "Settings coming soon!\n\nFor now, edit config.yaml manually.")

    def show_documentation(self):
        """Show documentation."""
        self.show_help()

    def check_system_status(self):
        """Check system status and display."""
        def check():
            self.log_status("Checking system components...")

            # Check Python
            self.log_status(f"✓ Python {sys.version.split()[0]}")

            # Check core modules
            modules = [
                ('mido', 'MIDI I/O'),
                ('flask', 'Web Framework'),
                ('pygame', 'Visual Editor'),
                ('librosa', 'Audio Processing'),
                ('pretty_midi', 'MIDI Creation'),
            ]

            for module, name in modules:
                try:
                    __import__(module)
                    self.log_status(f"✓ {name}")
                except ImportError:
                    self.log_status(f"✗ {name} (not installed)")

            # Check optional AI
            try:
                __import__('demucs')
                self.log_status("✓ Demucs AI (stem separation)")
            except ImportError:
                self.log_status("○ Demucs AI (optional, not installed)")

            try:
                __import__('basic_pitch')
                self.log_status("✓ Basic Pitch AI (audio-to-MIDI)")
            except ImportError:
                self.log_status("○ Basic Pitch AI (optional, not installed)")

            self.log_status("\n✓ System check complete!")
            self.log_status("Choose a feature from the dashboard above to get started.")

        threading.Thread(target=check, daemon=True).start()

    def log_status(self, message):
        """Log message to status display."""
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)

    def on_closing(self):
        """Handle window close."""
        # Stop web app if running
        if self.web_app_process and self.web_app_process.poll() is None:
            if messagebox.askyesno("Quit", "Web app is running. Stop it and quit?"):
                self.web_app_process.terminate()
                self.destroy()
        else:
            self.destroy()


def main():
    """Launch AIO application."""
    app = AIOLauncher()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
