"""
Clone Hero Chart Maker - Main Application
Creates Clone Hero charts from real-time MIDI guitar input.
"""

import os
import sys
from midi_capture import MIDICapture
from chart_generator import ChartGenerator


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Print application header."""
    print("=" * 60)
    print(" " * 15 + "CLONE HERO CHART MAKER")
    print(" " * 10 + "Create charts from MIDI guitar input")
    print("=" * 60)
    print()


def select_midi_device(devices):
    """
    Let user select a MIDI device.

    Args:
        devices: List of available MIDI device names

    Returns:
        Selected device name or None for default
    """
    print("Available MIDI Input Devices:")
    print("0: Use default device")

    for i, device in enumerate(devices, 1):
        print(f"{i}: {device}")

    while True:
        try:
            choice = input("\nSelect device number (or press Enter for default): ").strip()

            if not choice or choice == "0":
                return None

            device_idx = int(choice) - 1
            if 0 <= device_idx < len(devices):
                return devices[device_idx]
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def get_song_metadata():
    """
    Get song metadata from user.

    Returns:
        Dictionary with song metadata
    """
    print("\n" + "-" * 60)
    print("SONG METADATA")
    print("-" * 60)

    metadata = {}
    metadata['name'] = input("Song name: ").strip() or "Untitled"
    metadata['artist'] = input("Artist name: ").strip() or "Unknown Artist"
    metadata['album'] = input("Album (optional): ").strip()
    metadata['genre'] = input("Genre (default: rock): ").strip() or "rock"
    metadata['year'] = input("Year (optional): ").strip()

    while True:
        try:
            bpm_input = input("BPM (default: 120): ").strip()
            metadata['bpm'] = float(bpm_input) if bpm_input else 120.0
            if metadata['bpm'] <= 0:
                print("BPM must be positive. Please try again.")
                continue
            break
        except ValueError:
            print("Invalid BPM. Please enter a number.")

    print("\nDifficulty levels:")
    print("  1. Easy (MIDI notes 60-64)")
    print("  2. Medium (MIDI notes 72-76)")
    print("  3. Hard (MIDI notes 84-88)")
    print("  4. Expert (MIDI notes 96-100) [Recommended]")

    while True:
        diff_choice = input("\nSelect difficulty (default: 4 - Expert): ").strip()
        if not diff_choice:
            diff_choice = "4"

        if diff_choice == "1":
            metadata['difficulty'] = "Easy"
            break
        elif diff_choice == "2":
            metadata['difficulty'] = "Medium"
            break
        elif diff_choice == "3":
            metadata['difficulty'] = "Hard"
            break
        elif diff_choice == "4":
            metadata['difficulty'] = "Expert"
            break
        else:
            print("Invalid selection. Please enter 1-4.")

    return metadata


def main():
    """Main application loop."""
    clear_screen()
    print_header()

    # Initialize components
    capture = MIDICapture()
    generator = ChartGenerator()

    # List MIDI devices
    devices = capture.list_midi_devices()

    if not devices:
        print("WARNING: No MIDI devices found!")
        print("Please connect a MIDI guitar and try again.")
        print("\nIf you have a MIDI device connected:")
        print("  - Make sure drivers are installed")
        print("  - Check if device is recognized by your system")
        print("  - Try reconnecting the device")
        input("\nPress Enter to exit...")
        return

    # Select MIDI device
    selected_device = select_midi_device(devices)

    if selected_device:
        print(f"\nSelected device: {selected_device}")
    else:
        print("\nUsing default MIDI device")

    # Get song metadata
    metadata = get_song_metadata()

    # Recording instructions
    print("\n" + "=" * 60)
    print("RECORDING INSTRUCTIONS")
    print("=" * 60)
    print("\nYour MIDI guitar should be mapped to these notes:")
    print(f"  Difficulty: {metadata['difficulty']}")

    if metadata['difficulty'] == "Expert":
        print("  Green  = MIDI Note 96")
        print("  Red    = MIDI Note 97")
        print("  Yellow = MIDI Note 98")
        print("  Blue   = MIDI Note 99")
        print("  Orange = MIDI Note 100")
    elif metadata['difficulty'] == "Hard":
        print("  Green  = MIDI Note 84")
        print("  Red    = MIDI Note 85")
        print("  Yellow = MIDI Note 86")
        print("  Blue   = MIDI Note 87")
        print("  Orange = MIDI Note 88")
    elif metadata['difficulty'] == "Medium":
        print("  Green  = MIDI Note 72")
        print("  Red    = MIDI Note 73")
        print("  Yellow = MIDI Note 74")
        print("  Blue   = MIDI Note 75")
        print("  Orange = MIDI Note 76")
    else:  # Easy
        print("  Green  = MIDI Note 60")
        print("  Red    = MIDI Note 61")
        print("  Yellow = MIDI Note 62")
        print("  Blue   = MIDI Note 63")
        print("  Orange = MIDI Note 64")

    print("\nWhen ready:")
    print("  - Start playing your guitar")
    print("  - Press Ctrl+C to stop recording")
    print("=" * 60)

    input("\nPress Enter to start recording...")

    # Start recording
    print("\n" + "=" * 60)
    print("RECORDING... (Press Ctrl+C to stop)")
    print("=" * 60 + "\n")

    try:
        capture.start_recording(selected_device)
    except Exception as e:
        print(f"\nError during recording: {e}")
        input("\nPress Enter to exit...")
        return

    # Get captured notes
    notes = capture.get_notes()

    if not notes:
        print("\nNo notes captured!")
        print("Please check:")
        print("  - MIDI guitar is properly connected")
        print("  - MIDI device is sending notes")
        print("  - You're using the correct note range for the difficulty")
        input("\nPress Enter to exit...")
        return

    # Display capture summary
    duration = capture.get_recording_duration()
    print("\n" + "=" * 60)
    print("RECORDING COMPLETE")
    print("=" * 60)
    print(f"Captured notes: {len(notes)}")
    print(f"Duration: {duration:.2f} seconds")
    print(f"BPM: {metadata['bpm']}")

    # Create output directory
    song_folder = metadata['name'].replace(' ', '_').replace('/', '_')
    output_dir = os.path.join(os.getcwd(), "output", song_folder)
    os.makedirs(output_dir, exist_ok=True)

    # Generate chart file
    print(f"\nGenerating chart in: {output_dir}")
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

        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print(f"\nChart created in: {output_dir}")
        print("\nTo use in Clone Hero:")
        print(f"  1. Copy the folder '{song_folder}' to your Clone Hero Songs directory")
        print("  2. Add your audio file (song.ogg or guitar.ogg)")
        print("  3. Rescan songs in Clone Hero")
        print("\nClone Hero Songs directory (Windows):")
        print("  C:\\Program Files\\Clone Hero\\Songs")
        print("  or check Settings > General in Clone Hero")

    except Exception as e:
        print(f"\nError generating chart: {e}")
        input("\nPress Enter to exit...")
        return

    print("\n" + "=" * 60)
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)
