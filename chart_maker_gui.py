"""
GUI wrapper for Chart Maker - creates charts from MIDI guitar or game controller input
Allows user to choose between starting new chart or editing existing one
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import subprocess


class ChartMakerLauncher:
    """GUI launcher for chart maker with new/edit options"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Clone Hero Chart Maker")
        self.root.geometry("600x400")
        self.root.configure(bg='#1e1e1e')

        # Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background='#1e1e1e', foreground='white')
        style.configure('TLabel', background='#1e1e1e', foreground='white', font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'))
        style.configure('TButton', background='#0e639c', foreground='white',
                       font=('Segoe UI', 10), borderwidth=0, padding=10)
        style.map('TButton', background=[('active', '#1177bb')])

        self.create_widgets()

    def create_widgets(self):
        """Create the GUI widgets"""
        # Header
        header = ttk.Label(
            self.root,
            text="🎸 Clone Hero Chart Maker",
            style='Title.TLabel'
        )
        header.pack(pady=20)

        subtitle = ttk.Label(
            self.root,
            text="Record charts from MIDI guitar or Xbox 360 Xplorer controller",
            font=('Segoe UI', 9)
        )
        subtitle.pack(pady=5)

        # Main frame
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(expand=True, fill='both', padx=40, pady=20)

        # Option 1: New Chart
        new_frame = tk.Frame(main_frame, bg='#2d2d2d', relief='raised', bd=1)
        new_frame.pack(fill='x', pady=10)

        new_icon = ttk.Label(new_frame, text="📝", font=('Segoe UI', 24))
        new_icon.pack(side='left', padx=20, pady=20)

        new_text_frame = tk.Frame(new_frame, bg='#2d2d2d')
        new_text_frame.pack(side='left', expand=True, fill='both', pady=20)

        new_title = ttk.Label(
            new_text_frame,
            text="Create New Chart",
            font=('Segoe UI', 12, 'bold')
        )
        new_title.pack(anchor='w')

        new_desc = ttk.Label(
            new_text_frame,
            text="Record a brand new chart from your guitar or controller",
            font=('Segoe UI', 9),
            foreground='#aaaaaa'
        )
        new_desc.pack(anchor='w', pady=2)

        new_btn = ttk.Button(
            new_frame,
            text="Start Recording",
            command=self.launch_new_chart
        )
        new_btn.pack(side='right', padx=20)

        # Option 2: Edit Existing (Coming soon - not implemented yet)
        edit_frame = tk.Frame(main_frame, bg='#2d2d2d', relief='raised', bd=1)
        edit_frame.pack(fill='x', pady=10)

        edit_icon = ttk.Label(edit_frame, text="✏️", font=('Segoe UI', 24))
        edit_icon.pack(side='left', padx=20, pady=20)

        edit_text_frame = tk.Frame(edit_frame, bg='#2d2d2d')
        edit_text_frame.pack(side='left', expand=True, fill='both', pady=20)

        edit_title = ttk.Label(
            edit_text_frame,
            text="Edit Existing Chart",
            font=('Segoe UI', 12, 'bold')
        )
        edit_title.pack(anchor='w')

        edit_desc = ttk.Label(
            edit_text_frame,
            text="Load and modify an existing .chart file with your controller",
            font=('Segoe UI', 9),
            foreground='#aaaaaa'
        )
        edit_desc.pack(anchor='w', pady=2)

        edit_btn = ttk.Button(
            edit_frame,
            text="Edit Chart",
            command=self.edit_existing_chart
        )
        edit_btn.pack(side='right', padx=20)

        # Device detection info
        info_frame = tk.Frame(main_frame, bg='#2d2d2d', relief='raised', bd=1)
        info_frame.pack(fill='x', pady=10)

        info_label = ttk.Label(
            info_frame,
            text="💡 Supported Devices: MIDI Guitars, Xbox 360 Xplorer, Game Controllers",
            font=('Segoe UI', 9),
            foreground='#ffaa00'
        )
        info_label.pack(pady=10)

        # Detect button
        detect_btn = ttk.Button(
            info_frame,
            text="Detect Devices",
            command=self.detect_devices
        )
        detect_btn.pack(pady=5)

    def launch_new_chart(self):
        """Launch chart_maker.py for new chart creation"""
        # Check if we should use MIDI or controller version
        choice = messagebox.askquestion(
            "Input Method",
            "Do you have a MIDI guitar connected?\n\n"
            "• Yes = Use MIDI input\n"
            "• No = Use game controller (Xbox 360 Xplorer, etc.)",
            icon='question'
        )

        if choice == 'yes':
            # Launch MIDI version (original chart_maker.py but non-interactive)
            self.launch_midi_version()
        else:
            # Launch controller version
            self.launch_controller_version()

    def launch_midi_version(self):
        """Launch MIDI chart maker"""
        try:
            # Import here to avoid circular dependencies
            from midi_capture import MIDICapture

            capture = MIDICapture()
            devices = capture.list_midi_devices()

            if not devices:
                messagebox.showerror(
                    "No MIDI Devices",
                    "No MIDI input devices found!\n\n"
                    "Please connect a MIDI guitar and try again."
                )
                return

            # Show MIDI device selection window
            self.show_midi_device_selection(devices)

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to initialize MIDI: {str(e)}"
            )

    def show_midi_device_selection(self, devices):
        """Show window to select MIDI device"""
        device_window = tk.Toplevel(self.root)
        device_window.title("Select MIDI Device")
        device_window.geometry("500x400")
        device_window.configure(bg='#1e1e1e')

        ttk.Label(
            device_window,
            text="Select MIDI Input Device:",
            font=('Segoe UI', 12, 'bold')
        ).pack(pady=20)

        # Listbox for devices
        listbox = tk.Listbox(
            device_window,
            bg='#2d2d2d',
            fg='white',
            font=('Segoe UI', 10),
            selectbackground='#0e639c',
            height=10
        )
        listbox.pack(padx=20, fill='both', expand=True)

        listbox.insert(0, "Default Device")
        for i, device in enumerate(devices, 1):
            listbox.insert(i, device)

        listbox.select_set(0)

        def on_select():
            selection = listbox.curselection()
            if selection:
                idx = selection[0]
                selected_device = None if idx == 0 else devices[idx - 1]
                device_window.destroy()
                self.show_metadata_form(selected_device, 'midi')

        ttk.Button(
            device_window,
            text="Continue",
            command=on_select
        ).pack(pady=20)

    def launch_controller_version(self):
        """Launch controller-based chart maker"""
        try:
            from controller_capture import ControllerCapture

            capture = ControllerCapture()
            controller = capture.detect_controller()

            if not controller:
                messagebox.showerror(
                    "No Controller Found",
                    "No game controller detected!\n\n"
                    "Please connect your controller and try again."
                )
                return

            messagebox.showinfo(
                "Controller Detected",
                f"Found: {controller['name']}\n"
                f"Buttons: {controller['buttons']}\n\n"
                "Controller will be used for input."
            )

            # Show metadata form
            self.show_metadata_form(None, 'controller')

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to initialize controller: {str(e)}"
            )

    def show_metadata_form(self, device, input_type):
        """Show form to enter song metadata"""
        meta_window = tk.Toplevel(self.root)
        meta_window.title("Song Information")
        meta_window.geometry("500x600")
        meta_window.configure(bg='#1e1e1e')

        ttk.Label(
            meta_window,
            text="📝 Song Information",
            font=('Segoe UI', 14, 'bold')
        ).pack(pady=20)

        # Form frame
        form_frame = tk.Frame(meta_window, bg='#1e1e1e')
        form_frame.pack(padx=30, fill='both', expand=True)

        fields = {}

        # Song name
        ttk.Label(form_frame, text="Song Name:").grid(row=0, column=0, sticky='w', pady=5)
        fields['name'] = ttk.Entry(form_frame, width=40)
        fields['name'].grid(row=0, column=1, pady=5, padx=10)
        fields['name'].insert(0, "Untitled")

        # Artist
        ttk.Label(form_frame, text="Artist:").grid(row=1, column=0, sticky='w', pady=5)
        fields['artist'] = ttk.Entry(form_frame, width=40)
        fields['artist'].grid(row=1, column=1, pady=5, padx=10)
        fields['artist'].insert(0, "Unknown Artist")

        # Album
        ttk.Label(form_frame, text="Album (optional):").grid(row=2, column=0, sticky='w', pady=5)
        fields['album'] = ttk.Entry(form_frame, width=40)
        fields['album'].grid(row=2, column=1, pady=5, padx=10)

        # Genre
        ttk.Label(form_frame, text="Genre:").grid(row=3, column=0, sticky='w', pady=5)
        fields['genre'] = ttk.Entry(form_frame, width=40)
        fields['genre'].grid(row=3, column=1, pady=5, padx=10)
        fields['genre'].insert(0, "rock")

        # Year
        ttk.Label(form_frame, text="Year (optional):").grid(row=4, column=0, sticky='w', pady=5)
        fields['year'] = ttk.Entry(form_frame, width=40)
        fields['year'].grid(row=4, column=1, pady=5, padx=10)

        # BPM
        ttk.Label(form_frame, text="BPM:").grid(row=5, column=0, sticky='w', pady=5)
        fields['bpm'] = ttk.Entry(form_frame, width=40)
        fields['bpm'].grid(row=5, column=1, pady=5, padx=10)
        fields['bpm'].insert(0, "120")

        # Difficulty
        ttk.Label(form_frame, text="Difficulty:").grid(row=6, column=0, sticky='w', pady=5)
        difficulty_var = tk.StringVar(value="Expert")
        difficulties = ["Easy", "Medium", "Hard", "Expert"]
        difficulty_combo = ttk.Combobox(
            form_frame,
            textvariable=difficulty_var,
            values=difficulties,
            state='readonly',
            width=37
        )
        difficulty_combo.grid(row=6, column=1, pady=5, padx=10)

        def on_start():
            # Validate BPM
            try:
                bpm = float(fields['bpm'].get())
                if bpm <= 0:
                    raise ValueError()
            except:
                messagebox.showerror("Invalid BPM", "Please enter a valid BPM value")
                return

            metadata = {
                'name': fields['name'].get().strip() or "Untitled",
                'artist': fields['artist'].get().strip() or "Unknown Artist",
                'album': fields['album'].get().strip(),
                'genre': fields['genre'].get().strip() or "rock",
                'year': fields['year'].get().strip(),
                'bpm': bpm,
                'difficulty': difficulty_var.get()
            }

            meta_window.destroy()
            self.start_recording(device, input_type, metadata)

        ttk.Button(
            meta_window,
            text="Start Recording",
            command=on_start
        ).pack(pady=20)

    def start_recording(self, device, input_type, metadata):
        """Start the actual recording process"""
        if input_type == 'midi':
            self.record_midi(device, metadata)
        else:
            self.record_controller(metadata)

    def record_midi(self, device, metadata):
        """Record from MIDI device"""
        from midi_capture import MIDICapture
        from chart_generator import ChartGenerator

        capture = MIDICapture()
        generator = ChartGenerator()

        # Show recording window
        rec_window = tk.Toplevel(self.root)
        rec_window.title("Recording...")
        rec_window.geometry("600x400")
        rec_window.configure(bg='#1e1e1e')

        ttk.Label(
            rec_window,
            text="🎸 Recording in Progress",
            font=('Segoe UI', 16, 'bold')
        ).pack(pady=30)

        ttk.Label(
            rec_window,
            text=f"Song: {metadata['name']}",
            font=('Segoe UI', 12)
        ).pack(pady=5)

        ttk.Label(
            rec_window,
            text=f"Difficulty: {metadata['difficulty']}",
            font=('Segoe UI', 12)
        ).pack(pady=5)

        info_label = ttk.Label(
            rec_window,
            text="Play your guitar now!\nPress 'Stop Recording' when finished.",
            font=('Segoe UI', 10),
            foreground='#ffaa00'
        )
        info_label.pack(pady=30)

        def stop_recording():
            capture.stop_recording()
            notes = capture.get_notes()
            rec_window.destroy()

            if not notes:
                messagebox.showwarning(
                    "No Notes",
                    "No notes were captured. Please try again."
                )
                return

            self.save_chart(notes, metadata, generator)

        ttk.Button(
            rec_window,
            text="Stop Recording",
            command=stop_recording
        ).pack(pady=20)

        # Start recording
        try:
            capture.start_recording(device)
        except Exception as e:
            rec_window.destroy()
            messagebox.showerror("Recording Error", f"Error: {str(e)}")

    def record_controller(self, metadata):
        """Record from game controller"""
        from guitar_chart_maker import GuitarChartMaker

        maker = GuitarChartMaker()

        # Show recording window
        rec_window = tk.Toplevel(self.root)
        rec_window.title("Recording...")
        rec_window.geometry("600x400")
        rec_window.configure(bg='#1e1e1e')

        ttk.Label(
            rec_window,
            text="🎮 Recording in Progress",
            font=('Segoe UI', 16, 'bold')
        ).pack(pady=30)

        ttk.Label(
            rec_window,
            text=f"Song: {metadata['name']}",
            font=('Segoe UI', 12)
        ).pack(pady=5)

        info_label = ttk.Label(
            rec_window,
            text="Play on your controller now!\nPress 'Stop Recording' when finished.",
            font=('Segoe UI', 10),
            foreground='#ffaa00'
        )
        info_label.pack(pady=30)

        def stop_and_save():
            chart_path = maker.stop_and_save(
                metadata['name'],
                metadata['artist'],
                metadata['bpm']
            )
            rec_window.destroy()

            if chart_path:
                messagebox.showinfo(
                    "Success!",
                    f"Chart saved to:\n{chart_path}\n\n"
                    f"Add to Clone Hero Songs folder to play!"
                )
            else:
                messagebox.showwarning(
                    "No Notes",
                    "No notes were captured. Please try again."
                )

        ttk.Button(
            rec_window,
            text="Stop Recording",
            command=stop_and_save
        ).pack(pady=20)

        # Start recording
        maker.start_recording_controller()

    def save_chart(self, notes, metadata, generator):
        """Save the chart file"""
        song_folder = metadata['name'].replace(' ', '_').replace('/', '_')
        output_dir = os.path.join(os.getcwd(), "output", song_folder)
        os.makedirs(output_dir, exist_ok=True)

        chart_path = os.path.join(output_dir, "notes.chart")
        ini_path = os.path.join(output_dir, "song.ini")

        try:
            generator.generate_chart_file(
                midi_notes=notes,
                output_path=chart_path,
                song_name=metadata['name'],
                artist=metadata['artist'],
                bpm=metadata['bpm'],
                difficulty=metadata['difficulty']
            )

            generator.generate_song_ini(
                output_path=ini_path,
                song_name=metadata['name'],
                artist=metadata['artist'],
                album=metadata['album'],
                genre=metadata['genre'],
                year=metadata['year']
            )

            messagebox.showinfo(
                "Success!",
                f"Chart created successfully!\n\n"
                f"Location: {output_dir}\n\n"
                f"Next steps:\n"
                f"1. Add audio file (song.ogg or guitar.ogg)\n"
                f"2. Copy folder to Clone Hero Songs directory\n"
                f"3. Rescan songs in Clone Hero"
            )

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to save chart: {str(e)}"
            )

    def edit_existing_chart(self):
        """Launch controller-based chart editor for existing chart"""
        from tkinter import filedialog
        import subprocess

        # Ask user to select chart file
        chart_path = filedialog.askopenfilename(
            title="Select Chart File to Edit",
            filetypes=[
                ("Chart files", "*.chart"),
                ("All files", "*.*")
            ],
            initialdir=os.path.join(os.getcwd(), "output")
        )

        if not chart_path:
            return  # User cancelled

        # Check if controller is connected
        try:
            from controller_capture import ControllerCapture
            capture = ControllerCapture()
            controller = capture.detect_controller()

            if not controller:
                messagebox.showwarning(
                    "No Controller",
                    "No game controller detected!\n\n"
                    "Please connect your controller and try again."
                )
                return
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check controller: {str(e)}")
            return

        # Launch controller chart editor
        try:
            subprocess.Popen([sys.executable, 'controller_chart_editor.py', chart_path])
            messagebox.showinfo(
                "Editor Launched",
                f"Controller chart editor launched!\n\n"
                f"Editing: {os.path.basename(chart_path)}\n\n"
                f"Controls:\n"
                f"• D-PAD: Scroll time\n"
                f"• Fret Buttons: Add/remove notes\n"
                f"• H: Hide/show help\n"
                f"• ESC: Save and exit"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch editor: {str(e)}")

    def edit_chart_not_implemented(self):
        """Old placeholder - now redirects to new feature"""
        self.edit_existing_chart()

    def detect_devices(self):
        """Detect available input devices"""
        info_text = "🎸 Device Detection\n\n"

        # Check MIDI
        try:
            from midi_capture import MIDICapture
            capture = MIDICapture()
            devices = capture.list_midi_devices()

            if devices:
                info_text += f"✅ MIDI Devices ({len(devices)}):\n"
                for device in devices:
                    info_text += f"   • {device}\n"
            else:
                info_text += "❌ No MIDI devices found\n"
        except Exception as e:
            info_text += f"❌ MIDI Error: {str(e)}\n"

        info_text += "\n"

        # Check Controllers
        try:
            from controller_capture import ControllerCapture
            capture = ControllerCapture()
            controller = capture.detect_controller()

            if controller:
                info_text += f"✅ Game Controller:\n"
                info_text += f"   • {controller['name']}\n"
                info_text += f"   • {controller['buttons']} buttons\n"
            else:
                info_text += "❌ No game controllers found\n"
        except Exception as e:
            info_text += f"❌ Controller Error: {str(e)}\n"

        messagebox.showinfo("Device Detection", info_text)

    def run(self):
        """Run the GUI"""
        self.root.mainloop()


if __name__ == "__main__":
    launcher = ChartMakerLauncher()
    launcher.run()
