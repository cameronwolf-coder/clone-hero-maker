"""
MIDI Guitar Input Capture Module
Captures MIDI input from a connected MIDI guitar in real-time.
"""

import mido
from typing import List, Tuple, Optional
import time


class MIDICapture:
    """Handles MIDI input capture from guitar."""

    def __init__(self):
        self.recording = False
        self.notes = []  # List of (timestamp, note_number, velocity, note_off_time)
        self.start_time = 0
        self.active_notes = {}  # note_number -> (start_timestamp, velocity)

    def list_midi_devices(self) -> List[str]:
        """List all available MIDI input devices."""
        return mido.get_input_names()

    def start_recording(self, device_name: Optional[str] = None):
        """
        Start recording MIDI input.

        Args:
            device_name: Name of MIDI device to use. If None, uses default.
        """
        self.recording = True
        self.notes = []
        self.active_notes = {}
        self.start_time = time.time()

        print(f"Recording started at {self.start_time}")

        try:
            if device_name:
                port = mido.open_input(device_name)
            else:
                port = mido.open_input()

            print(f"Listening on MIDI port: {port.name}")
            print("Play your guitar! Press Ctrl+C to stop recording.")

            for msg in port:
                if not self.recording:
                    break

                self._process_midi_message(msg)

        except KeyboardInterrupt:
            print("\nRecording stopped by user")
        finally:
            port.close()
            self._finalize_active_notes()

    def stop_recording(self):
        """Stop recording MIDI input."""
        self.recording = False
        self._finalize_active_notes()
        print(f"Recording stopped. Captured {len(self.notes)} notes.")

    def _process_midi_message(self, msg: mido.Message):
        """Process incoming MIDI message."""
        current_time = time.time() - self.start_time

        if msg.type == 'note_on' and msg.velocity > 0:
            # Note started
            self.active_notes[msg.note] = (current_time, msg.velocity)
            print(f"Note ON:  {msg.note} at {current_time:.3f}s (vel: {msg.velocity})")

        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            # Note ended
            if msg.note in self.active_notes:
                start_time, velocity = self.active_notes[msg.note]
                duration = current_time - start_time

                # Store: (start_time, note_number, velocity, duration)
                self.notes.append((start_time, msg.note, velocity, duration))
                print(f"Note OFF: {msg.note} at {current_time:.3f}s (duration: {duration:.3f}s)")

                del self.active_notes[msg.note]

    def _finalize_active_notes(self):
        """Finalize any notes that are still active when recording stops."""
        current_time = time.time() - self.start_time

        for note_number, (start_time, velocity) in self.active_notes.items():
            duration = current_time - start_time
            self.notes.append((start_time, note_number, velocity, duration))

        self.active_notes = {}

    def get_notes(self) -> List[Tuple[float, int, int, float]]:
        """
        Get captured notes.

        Returns:
            List of tuples: (start_time, note_number, velocity, duration)
        """
        return sorted(self.notes, key=lambda x: x[0])

    def get_recording_duration(self) -> float:
        """Get total recording duration in seconds."""
        if not self.notes:
            return 0.0
        last_note = max(self.notes, key=lambda x: x[0] + x[3])
        return last_note[0] + last_note[3]


if __name__ == "__main__":
    # Test the MIDI capture
    capture = MIDICapture()

    print("Available MIDI devices:")
    devices = capture.list_midi_devices()
    for i, device in enumerate(devices):
        print(f"{i}: {device}")

    if devices:
        print("\nStarting recording with default device...")
        print("Press Ctrl+C to stop\n")
        capture.start_recording()

        notes = capture.get_notes()
        print(f"\nCaptured {len(notes)} notes:")
        for note in notes[:10]:  # Show first 10
            print(f"  Time: {note[0]:.3f}s, Note: {note[1]}, Velocity: {note[2]}, Duration: {note[3]:.3f}s")
    else:
        print("\nNo MIDI devices found. Please connect a MIDI guitar.")
