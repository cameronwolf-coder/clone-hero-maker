"""
Controller Capture - Capture input from game controllers (Xbox 360 Xplorer, etc.)
For use with Clone Hero guitar controllers
"""

import pygame
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import IntEnum

class GuitarButton(IntEnum):
    """Guitar Hero/Clone Hero button mappings"""
    GREEN = 0
    RED = 1
    YELLOW = 2
    BLUE = 3
    ORANGE = 4

class ControllerCapture:
    """Capture input from game controllers like Xbox 360 Xplorer guitar"""

    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        self.controller: Optional[pygame.joystick.Joystick] = None
        self.recording = False
        self.start_time = 0
        self.notes: List[Tuple[int, int, float]] = []  # (fret, velocity, timestamp)

        # Button state tracking for note-on/note-off
        self.button_states = {i: False for i in range(5)}
        self.note_start_times = {i: 0 for i in range(5)}

    def list_controllers(self) -> List[str]:
        """List all available game controllers"""
        pygame.joystick.quit()
        pygame.joystick.init()

        controllers = []
        for i in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(i)
            controllers.append(f"{i}: {joy.get_name()}")

        return controllers

    def connect_controller(self, controller_id: int = 0) -> bool:
        """Connect to a specific controller"""
        try:
            if pygame.joystick.get_count() == 0:
                print("No controllers found!")
                return False

            self.controller = pygame.joystick.Joystick(controller_id)
            self.controller.init()
            print(f"Connected to: {self.controller.get_name()}")
            print(f"  Buttons: {self.controller.get_numbuttons()}")
            print(f"  Axes: {self.controller.get_numaxes()}")
            print(f"  Hats: {self.controller.get_numhats()}")
            return True

        except Exception as e:
            print(f"Failed to connect controller: {e}")
            return False

    def get_guitar_button_mapping(self) -> Dict[int, int]:
        """
        Get button mapping for Xbox 360 Xplorer guitar
        Maps controller buttons to Clone Hero frets (0-4)

        Common Xbox 360 Xplorer mapping:
        - Button 0 (A/Green) -> Fret 0 (Green)
        - Button 1 (B/Red) -> Fret 1 (Red)
        - Button 2 (X/Yellow) -> Fret 2 (Yellow)
        - Button 3 (Y/Blue) -> Fret 3 (Blue)
        - Button 4 (LB/Orange) -> Fret 4 (Orange)
        """
        # Default Xbox 360 Xplorer mapping
        return {
            0: GuitarButton.GREEN,    # A button
            1: GuitarButton.RED,      # B button
            2: GuitarButton.YELLOW,   # X button
            3: GuitarButton.BLUE,     # Y button
            4: GuitarButton.ORANGE,   # Left bumper
        }

    def detect_button_mapping(self) -> Dict[int, int]:
        """
        Interactive button mapping - have user press buttons to map them
        """
        if not self.controller:
            print("No controller connected!")
            return {}

        print("\n" + "="*60)
        print("GUITAR BUTTON MAPPING")
        print("="*60)
        print("\nPress each fret button when prompted...")
        print("(Press Ctrl+C to skip and use default mapping)\n")

        mapping = {}
        fret_names = ["GREEN", "RED", "YELLOW", "BLUE", "ORANGE"]

        try:
            for fret_id, fret_name in enumerate(fret_names):
                print(f"Press the {fret_name} fret button...", end=" ", flush=True)

                # Wait for button press
                waiting = True
                while waiting:
                    pygame.event.pump()
                    for button_id in range(self.controller.get_numbuttons()):
                        if self.controller.get_button(button_id):
                            mapping[button_id] = fret_id
                            print(f"✓ Mapped to button {button_id}")
                            waiting = False

                            # Wait for release
                            while self.controller.get_button(button_id):
                                pygame.event.pump()
                                time.sleep(0.01)

                            time.sleep(0.3)  # Debounce
                            break

                    time.sleep(0.01)

            print("\n" + "="*60)
            print("Mapping complete!")
            print("="*60)
            return mapping

        except KeyboardInterrupt:
            print("\n\nUsing default Xbox 360 Xplorer mapping...")
            return self.get_guitar_button_mapping()

    def start_recording(self, use_custom_mapping: bool = False):
        """Start recording controller input"""
        if not self.controller:
            print("No controller connected!")
            return

        # Get button mapping
        if use_custom_mapping:
            self.button_mapping = self.detect_button_mapping()
        else:
            self.button_mapping = self.get_guitar_button_mapping()

        self.recording = True
        self.start_time = time.time()
        self.notes = []
        self.button_states = {i: False for i in range(5)}
        self.note_start_times = {i: 0 for i in range(5)}

        print("\n" + "="*60)
        print("RECORDING STARTED")
        print("="*60)
        print("Play your guitar controller!")
        print("Press START button (or button 7) to stop recording")
        print("="*60 + "\n")

    def stop_recording(self):
        """Stop recording"""
        self.recording = False
        print("\n" + "="*60)
        print("RECORDING STOPPED")
        print("="*60)
        print(f"Recorded {len(self.notes)} note events")
        print("="*60 + "\n")

    def process_events(self) -> bool:
        """
        Process controller events during recording
        Returns False if recording should stop
        """
        if not self.recording:
            return False

        pygame.event.pump()

        # Check for START button to stop (button 7 on most controllers)
        if self.controller.get_numbuttons() > 7 and self.controller.get_button(7):
            return False

        current_time = time.time() - self.start_time

        # Process each mapped button
        for button_id, fret_id in self.button_mapping.items():
            if button_id >= self.controller.get_numbuttons():
                continue

            button_pressed = self.controller.get_button(button_id)

            # Note ON - button just pressed
            if button_pressed and not self.button_states[fret_id]:
                self.button_states[fret_id] = True
                self.note_start_times[fret_id] = current_time

                # Record note on with velocity (can use strumming later)
                self.notes.append((fret_id, 100, current_time, True))  # True = note on

                fret_names = ["GREEN", "RED", "YELLOW", "BLUE", "ORANGE"]
                print(f"[{current_time:6.2f}s] {fret_names[fret_id]:7s} ON")

            # Note OFF - button just released
            elif not button_pressed and self.button_states[fret_id]:
                self.button_states[fret_id] = False
                duration = current_time - self.note_start_times[fret_id]

                # Record note off
                self.notes.append((fret_id, 0, current_time, False))  # False = note off

                fret_names = ["GREEN", "RED", "YELLOW", "BLUE", "ORANGE"]
                print(f"[{current_time:6.2f}s] {fret_names[fret_id]:7s} OFF (held {duration:.2f}s)")

        return True

    def record_performance(self, duration: Optional[float] = None,
                          use_custom_mapping: bool = False) -> List[Tuple[int, int, float, bool]]:
        """
        Record a performance for a specified duration or until stopped

        Args:
            duration: Recording duration in seconds (None = record until START pressed)
            use_custom_mapping: If True, prompt user to map buttons

        Returns:
            List of note events: (fret, velocity, timestamp, is_note_on)
        """
        self.start_recording(use_custom_mapping)

        try:
            if duration:
                end_time = time.time() + duration
                while time.time() < end_time and self.process_events():
                    time.sleep(0.01)
            else:
                while self.process_events():
                    time.sleep(0.01)

        except KeyboardInterrupt:
            print("\n\nRecording interrupted by user")

        finally:
            self.stop_recording()

        return self.notes

    def notes_to_chart_format(self, bpm: float = 120.0, resolution: int = 192) -> List[Dict]:
        """
        Convert recorded notes to Clone Hero chart format

        Args:
            bpm: Beats per minute
            resolution: Ticks per quarter note

        Returns:
            List of chart notes with tick positions and sustains
        """
        if not self.notes:
            return []

        chart_notes = []
        active_notes = {}  # Track note-on events to calculate sustain

        # Convert time to ticks
        seconds_per_beat = 60.0 / bpm
        ticks_per_second = resolution / seconds_per_beat

        for fret, velocity, timestamp, is_note_on in self.notes:
            tick = int(timestamp * ticks_per_second)

            if is_note_on:
                # Store note-on event
                active_notes[fret] = (tick, velocity)
            else:
                # Note-off: create chart note with sustain
                if fret in active_notes:
                    start_tick, vel = active_notes[fret]
                    sustain = tick - start_tick

                    chart_notes.append({
                        'tick': start_tick,
                        'fret': fret,
                        'sustain': sustain,
                        'velocity': vel
                    })

                    del active_notes[fret]

        # Handle any notes that weren't released
        for fret, (start_tick, vel) in active_notes.items():
            chart_notes.append({
                'tick': start_tick,
                'fret': fret,
                'sustain': 0,
                'velocity': vel
            })

        # Sort by tick
        chart_notes.sort(key=lambda x: x['tick'])

        return chart_notes

    def cleanup(self):
        """Cleanup pygame resources"""
        if self.controller:
            self.controller.quit()
        pygame.joystick.quit()
        pygame.quit()


def main():
    """Test/demo the controller capture"""
    print("="*60)
    print("CLONE HERO CONTROLLER CAPTURE")
    print("="*60)

    capture = ControllerCapture()

    # List controllers
    controllers = capture.list_controllers()
    print(f"\nFound {len(controllers)} controller(s):")
    for ctrl in controllers:
        print(f"  {ctrl}")

    if not controllers:
        print("\nNo controllers found!")
        print("Please connect your Xbox 360 Xplorer or other guitar controller.")
        return

    # Connect to first controller
    print("\nConnecting to first controller...")
    if not capture.connect_controller(0):
        return

    # Ask if user wants custom mapping
    print("\nUse default Xbox 360 Xplorer button mapping? (y/n): ", end="", flush=True)
    import sys
    try:
        response = input().strip().lower()
        use_custom = response == 'n'
    except:
        use_custom = False

    # Record performance
    print("\nPress Enter to start recording (or Ctrl+C to exit)...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nExiting...")
        capture.cleanup()
        return

    notes = capture.record_performance(use_custom_mapping=use_custom)

    if notes:
        print(f"\n\nRecorded {len(notes)} note events")

        # Convert to chart format
        chart_notes = capture.notes_to_chart_format(bpm=120.0)
        print(f"Generated {len(chart_notes)} chart notes")

        # Show sample
        print("\nSample chart notes:")
        for i, note in enumerate(chart_notes[:10]):
            fret_names = ["GREEN", "RED", "YELLOW", "BLUE", "ORANGE"]
            print(f"  Tick {note['tick']:5d}: {fret_names[note['fret']]:7s} "
                  f"(sustain: {note['sustain']} ticks)")

        if len(chart_notes) > 10:
            print(f"  ... and {len(chart_notes) - 10} more notes")

    capture.cleanup()
    print("\nDone!")


if __name__ == "__main__":
    main()
