"""
Guitar Chart Maker - Create Clone Hero charts from guitar controller OR MIDI input
Supports Xbox 360 Xplorer and other game controllers as well as MIDI devices
"""

import os
import sys
from typing import Optional, List, Dict

# Import both capture methods
from controller_capture import ControllerCapture
from midi_capture import MIDICapture
from chart_generator import ChartGenerator


class GuitarChartMaker:
    """Unified chart maker supporting both game controllers and MIDI"""

    def __init__(self):
        self.controller_capture = ControllerCapture()
        self.midi_capture = MIDICapture()
        self.chart_generator = ChartGenerator()

    def list_all_devices(self) -> tuple:
        """List both game controllers and MIDI devices"""
        controllers = self.controller_capture.list_controllers()
        midi_devices = self.midi_capture.list_midi_devices()

        return controllers, midi_devices

    def create_chart_from_controller(self,
                                     output_path: str,
                                     song_name: str,
                                     artist: str,
                                     bpm: float = 120.0,
                                     duration: Optional[float] = None,
                                     use_custom_mapping: bool = False) -> bool:
        """
        Create a chart from game controller input

        Args:
            output_path: Where to save the .chart file
            song_name: Name of the song
            artist: Artist name
            bpm: Tempo in beats per minute
            duration: Recording duration (None = until stopped)
            use_custom_mapping: Prompt user to map buttons

        Returns:
            True if successful
        """
        try:
            # Record performance
            print("\n" + "="*60)
            print(f"Creating chart: {song_name} by {artist}")
            print(f"BPM: {bpm}")
            print("="*60)

            notes = self.controller_capture.record_performance(duration, use_custom_mapping)

            if not notes:
                print("No notes recorded!")
                return False

            # Convert to chart format
            chart_notes = self.controller_capture.notes_to_chart_format(bpm)

            # Generate chart file
            print("\nGenerating chart file...")

            # Start chart
            self.chart_generator.start_chart(
                song_name=song_name,
                artist=artist,
                charter="GuitarChartMaker",
                tempo_bpm=bpm
            )

            # Add notes
            for note in chart_notes:
                self.chart_generator.add_note(
                    tick=note['tick'],
                    fret=note['fret'],
                    sustain=note['sustain']
                )

            # Write chart
            self.chart_generator.write_chart(output_path)

            print(f"\n✓ Chart saved to: {output_path}")
            print(f"  Total notes: {len(chart_notes)}")

            return True

        except Exception as e:
            print(f"\n✗ Error creating chart: {e}")
            import traceback
            traceback.print_exc()
            return False

    def create_chart_from_midi(self,
                               midi_device_id: int,
                               output_path: str,
                               song_name: str,
                               artist: str,
                               bpm: float = 120.0,
                               duration: Optional[float] = None) -> bool:
        """
        Create a chart from MIDI device input

        Args:
            midi_device_id: MIDI device index
            output_path: Where to save the .chart file
            song_name: Name of the song
            artist: Artist name
            bpm: Tempo in beats per minute
            duration: Recording duration (None = until stopped)

        Returns:
            True if successful
        """
        try:
            print("\n" + "="*60)
            print(f"Creating chart: {song_name} by {artist}")
            print(f"BPM: {bpm}")
            print("="*60)

            # Connect to MIDI device
            if not self.midi_capture.connect_device(midi_device_id):
                return False

            # Record MIDI
            notes = self.midi_capture.record_performance(duration)

            if not notes:
                print("No notes recorded!")
                return False

            # Generate chart
            print("\nGenerating chart file...")

            self.chart_generator.start_chart(
                song_name=song_name,
                artist=artist,
                charter="GuitarChartMaker",
                tempo_bpm=bpm
            )

            # Add notes from MIDI
            for note in notes:
                # Map MIDI note to fret (simple mapping)
                fret = note['note'] % 5  # Map to 0-4
                self.chart_generator.add_note(
                    tick=note['tick'],
                    fret=fret,
                    sustain=note.get('sustain', 0)
                )

            self.chart_generator.write_chart(output_path)

            print(f"\n✓ Chart saved to: {output_path}")
            return True

        except Exception as e:
            print(f"\n✗ Error creating chart: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            self.midi_capture.close_device()

    def cleanup(self):
        """Cleanup resources"""
        self.controller_capture.cleanup()
        self.midi_capture.close_device()


def main():
    """Interactive chart maker"""
    print("="*60)
    print("           CLONE HERO GUITAR CHART MAKER")
    print("       Create charts from guitar controller or MIDI")
    print("="*60)

    maker = GuitarChartMaker()

    try:
        # Detect devices
        controllers, midi_devices = maker.list_all_devices()

        print(f"\nFound {len(controllers)} game controller(s):")
        for i, ctrl in enumerate(controllers):
            print(f"  [{i}] {ctrl}")

        print(f"\nFound {len(midi_devices)} MIDI device(s):")
        for i, dev in enumerate(midi_devices):
            print(f"  [{i}] {dev}")

        if not controllers and not midi_devices:
            print("\n✗ No input devices found!")
            print("\nPlease connect:")
            print("  - Xbox 360 Xplorer or other guitar controller, OR")
            print("  - MIDI guitar/keyboard")
            return

        # Choose input method
        print("\n" + "="*60)
        print("Select input method:")
        if controllers:
            print("  [1] Game Controller (Xbox 360 Xplorer, etc.)")
        if midi_devices:
            print("  [2] MIDI Device")
        print("="*60)

        try:
            choice = input("\nChoice: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nExiting...")
            return

        # Get song info
        print("\n" + "="*60)
        print("Song Information")
        print("="*60)

        try:
            song_name = input("Song name: ").strip() or "Untitled"
            artist = input("Artist: ").strip() or "Unknown"
            bpm_input = input("BPM (default 120): ").strip()
            bpm = float(bpm_input) if bpm_input else 120.0
        except (EOFError, KeyboardInterrupt):
            print("\n\nExiting...")
            return
        except ValueError:
            print("Invalid BPM, using 120")
            bpm = 120.0

        # Output file
        safe_name = "".join(c for c in song_name if c.isalnum() or c in (' ', '-', '_'))
        output_path = f"{safe_name}.chart"

        # Create chart based on choice
        success = False

        if choice == "1" and controllers:
            # Game controller
            print("\nConnecting to game controller...")
            if maker.controller_capture.connect_controller(0):
                print("\nUse default button mapping for Xbox 360 Xplorer? (y/n): ", end="")
                try:
                    map_choice = input().strip().lower()
                    use_default = map_choice != 'n'
                except (EOFError, KeyboardInterrupt):
                    print("\n\nExiting...")
                    return

                success = maker.create_chart_from_controller(
                    output_path=output_path,
                    song_name=song_name,
                    artist=artist,
                    bpm=bpm,
                    use_custom_mapping=not use_default
                )

        elif choice == "2" and midi_devices:
            # MIDI device
            print("\nSelect MIDI device:")
            for i, dev in enumerate(midi_devices):
                print(f"  [{i}] {dev}")

            try:
                device_choice = int(input("\nDevice number: "))
                success = maker.create_chart_from_midi(
                    midi_device_id=device_choice,
                    output_path=output_path,
                    song_name=song_name,
                    artist=artist,
                    bpm=bpm
                )
            except (EOFError, KeyboardInterrupt):
                print("\n\nExiting...")
                return
            except ValueError:
                print("Invalid device number!")

        else:
            print("\n✗ Invalid choice!")

        if success:
            print("\n" + "="*60)
            print("SUCCESS! Chart created!")
            print("="*60)
            print(f"\nChart file: {output_path}")
            print("\nNext steps:")
            print("  1. Add this chart to Clone Hero's songs folder")
            print("  2. Add the song audio file (song.ogg)")
            print("  3. Create song.ini with metadata")
            print("  4. Play in Clone Hero!")
            print("\n" + "="*60)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")

    finally:
        maker.cleanup()


if __name__ == "__main__":
    main()
