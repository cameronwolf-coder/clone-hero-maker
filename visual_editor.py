"""
Visual Chart Editor
GUI-based chart editor with highway view and note placement.
"""

import pygame
import sys
from typing import Optional, List, Tuple
from chart_parser import Chart, ChartParser, Note, Track, Instrument, Difficulty, NoteFlag, BPMChange, StarPowerPhrase
from midi_capture import MIDICapture
import os


# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)

# Note colors (Clone Hero standard)
GREEN = (34, 177, 76)
RED = (237, 28, 36)
YELLOW = (255, 242, 0)
BLUE = (0, 162, 232)
ORANGE = (255, 127, 39)
PURPLE = (163, 73, 164)  # For open notes

# UI colors
STAR_POWER_COLOR = (100, 200, 255)
SUSTAIN_COLOR = (150, 150, 150)
BPM_LINE_COLOR = (255, 100, 100)
BEAT_LINE_COLOR = (80, 80, 80)
MEASURE_LINE_COLOR = (120, 120, 120)


class Tool:
    """Editor tools."""
    CURSOR = "cursor"
    NOTE = "note"
    ERASER = "eraser"
    STAR_POWER = "star_power"
    BPM = "bpm"


class VisualEditor:
    """Visual chart editor with highway display."""

    def __init__(self, width=1280, height=720):
        """Initialize the visual editor."""
        pygame.init()

        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Clone Hero Chart Maker - Visual Editor")

        self.clock = pygame.time.Clock()
        self.running = True

        # Chart data
        self.chart = Chart()
        self.current_instrument = Instrument.GUITAR
        self.current_difficulty = Difficulty.EXPERT
        self.current_track = Track()
        self.chart.set_track(self.current_instrument, self.current_difficulty, self.current_track)

        # Initialize with default BPM
        if not self.chart.bpm_changes:
            self.chart.bpm_changes.append(BPMChange(0, 120.0))

        # Editor state
        self.current_tool = Tool.NOTE
        self.current_tick = 0
        self.scroll_position = 0  # Vertical scroll in ticks
        self.zoom = 1.0  # Zoom level
        self.snap = 192 // 4  # Snap to 1/4 notes
        self.selected_notes = []

        # Highway dimensions
        self.highway_x = 400
        self.highway_width = 400
        self.highway_y = 100
        self.highway_height = height - 200

        # Note dimensions
        self.note_width = (self.highway_width - 40) // 5
        self.note_height = 20

        # UI elements
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

        # MIDI capture
        self.midi_capture = None
        self.is_recording = False

        # Modified flag
        self.modified = False
        self.current_file = None

    def run(self):
        """Main editor loop."""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

        pygame.quit()

    def handle_events(self):
        """Handle user input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                self.handle_keypress(event.key, event.mod)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_click(event.button, event.pos)

            elif event.type == pygame.MOUSEWHEEL:
                # Scroll with mouse wheel
                self.scroll_position -= event.y * 100
                self.scroll_position = max(0, self.scroll_position)

    def handle_keypress(self, key, mod):
        """Handle keyboard input."""
        # Tool selection
        if key == pygame.K_1:
            self.current_tool = Tool.CURSOR
        elif key == pygame.K_2:
            self.current_tool = Tool.NOTE
        elif key == pygame.K_3:
            self.current_tool = Tool.ERASER
        elif key == pygame.K_4:
            self.current_tool = Tool.STAR_POWER
        elif key == pygame.K_5:
            self.current_tool = Tool.BPM

        # Difficulty selection
        elif key == pygame.K_F1:
            self.switch_difficulty(Difficulty.EASY)
        elif key == pygame.K_F2:
            self.switch_difficulty(Difficulty.MEDIUM)
        elif key == pygame.K_F3:
            self.switch_difficulty(Difficulty.HARD)
        elif key == pygame.K_F4:
            self.switch_difficulty(Difficulty.EXPERT)

        # Snap control
        elif key == pygame.K_LEFT and mod & pygame.KMOD_CTRL:
            self.decrease_snap()
        elif key == pygame.K_RIGHT and mod & pygame.KMOD_CTRL:
            self.increase_snap()

        # File operations
        elif key == pygame.K_s and mod & pygame.KMOD_CTRL:
            self.save_chart()
        elif key == pygame.K_o and mod & pygame.KMOD_CTRL:
            self.open_chart()
        elif key == pygame.K_n and mod & pygame.KMOD_CTRL:
            self.new_chart()

        # MIDI recording
        elif key == pygame.K_r and mod & pygame.KMOD_CTRL:
            self.toggle_midi_recording()

        # Scroll
        elif key == pygame.K_UP:
            self.scroll_position -= 192
            self.scroll_position = max(0, self.scroll_position)
        elif key == pygame.K_DOWN:
            self.scroll_position += 192
        elif key == pygame.K_PAGEUP:
            self.scroll_position -= 192 * 4
            self.scroll_position = max(0, self.scroll_position)
        elif key == pygame.K_PAGEDOWN:
            self.scroll_position += 192 * 4
        elif key == pygame.K_HOME:
            self.scroll_position = 0

        # Delete selected
        elif key == pygame.K_DELETE:
            self.delete_selected_notes()

    def handle_mouse_click(self, button, pos):
        """Handle mouse clicks."""
        x, y = pos

        # Check if click is in highway
        if self.is_in_highway(x, y):
            if button == 1:  # Left click
                if self.current_tool == Tool.NOTE:
                    self.place_note_at_position(x, y)
                elif self.current_tool == Tool.ERASER:
                    self.erase_note_at_position(x, y)
                elif self.current_tool == Tool.CURSOR:
                    self.select_note_at_position(x, y)

    def is_in_highway(self, x, y):
        """Check if coordinates are inside the highway."""
        return (self.highway_x <= x <= self.highway_x + self.highway_width and
                self.highway_y <= y <= self.highway_y + self.highway_height)

    def position_to_fret(self, x):
        """Convert X position to fret number (0-4)."""
        relative_x = x - self.highway_x - 20
        fret = int(relative_x / self.note_width)
        return max(0, min(4, fret))

    def position_to_tick(self, y):
        """Convert Y position to tick number."""
        relative_y = y - self.highway_y
        # Convert y position to tick (accounting for scroll)
        tick_offset = int((relative_y / self.highway_height) * 192 * 8)  # 8 measures visible
        tick = self.scroll_position + tick_offset

        # Snap to grid
        tick = (tick // self.snap) * self.snap
        return tick

    def place_note_at_position(self, x, y):
        """Place a note at the clicked position."""
        fret = self.position_to_fret(x)
        tick = self.position_to_tick(y)

        # Check if note already exists
        existing = [n for n in self.current_track.notes if n.tick == tick and n.fret == fret]
        if existing:
            return  # Don't place duplicate

        # Create new note
        note = Note(tick, fret, 0)
        self.current_track.add_note(note)
        self.modified = True

    def erase_note_at_position(self, x, y):
        """Erase note at the clicked position."""
        fret = self.position_to_fret(x)
        tick = self.position_to_tick(y)

        # Find and remove notes at this position
        to_remove = [n for n in self.current_track.notes if n.tick == tick and n.fret == fret]
        for note in to_remove:
            self.current_track.notes.remove(note)
            self.modified = True

    def select_note_at_position(self, x, y):
        """Select note at the clicked position."""
        fret = self.position_to_fret(x)
        tick = self.position_to_tick(y)

        # Find notes at this position
        notes = [n for n in self.current_track.notes if n.tick == tick and n.fret == fret]
        if notes:
            self.selected_notes = notes

    def delete_selected_notes(self):
        """Delete all selected notes."""
        for note in self.selected_notes:
            if note in self.current_track.notes:
                self.current_track.notes.remove(note)
                self.modified = True
        self.selected_notes = []

    def switch_difficulty(self, difficulty: Difficulty):
        """Switch to a different difficulty."""
        self.current_difficulty = difficulty
        track = self.chart.get_track(self.current_instrument, difficulty)
        if not track:
            track = Track()
            self.chart.set_track(self.current_instrument, difficulty, track)
        self.current_track = track

    def increase_snap(self):
        """Increase snap resolution."""
        snap_values = [192, 96, 48, 24, 12, 6]
        current_idx = snap_values.index(self.snap) if self.snap in snap_values else 0
        if current_idx > 0:
            self.snap = snap_values[current_idx - 1]

    def decrease_snap(self):
        """Decrease snap resolution."""
        snap_values = [192, 96, 48, 24, 12, 6]
        current_idx = snap_values.index(self.snap) if self.snap in snap_values else len(snap_values) - 1
        if current_idx < len(snap_values) - 1:
            self.snap = snap_values[current_idx + 1]

    def toggle_midi_recording(self):
        """Toggle MIDI recording."""
        if not self.is_recording:
            # Start recording
            if not self.midi_capture:
                self.midi_capture = MIDICapture()

            devices = self.midi_capture.list_midi_devices()
            if devices:
                print("Starting MIDI recording...")
                self.is_recording = True
                # TODO: Start recording in a separate thread
            else:
                print("No MIDI devices found!")
        else:
            # Stop recording
            if self.midi_capture:
                self.midi_capture.stop_recording()
                notes = self.midi_capture.get_notes()

                # Convert MIDI notes to chart notes
                from chart_generator import ChartGenerator
                generator = ChartGenerator()
                bpm = self.chart.get_initial_bpm()

                chart_notes = generator.midi_notes_to_chart_notes(
                    notes, bpm, self.current_difficulty.value
                )

                # Add to current track
                for tick, fret, sustain in chart_notes:
                    note = Note(tick, fret, sustain)
                    self.current_track.add_note(note)

                self.modified = True
                print(f"Added {len(chart_notes)} notes from MIDI recording")

            self.is_recording = False

    def save_chart(self):
        """Save the current chart."""
        if not self.current_file:
            # TODO: Show file dialog
            self.current_file = "output/my_chart/notes.chart"

        os.makedirs(os.path.dirname(self.current_file), exist_ok=True)
        ChartParser.write_file(self.chart, self.current_file)
        self.modified = False
        print(f"Chart saved to {self.current_file}")

    def open_chart(self):
        """Open an existing chart."""
        # TODO: Show file dialog
        pass

    def new_chart(self):
        """Create a new chart."""
        if self.modified:
            # TODO: Ask to save
            pass

        self.chart = Chart()
        self.current_track = Track()
        self.chart.set_track(self.current_instrument, self.current_difficulty, self.current_track)
        self.chart.bpm_changes.append(BPMChange(0, 120.0))
        self.modified = False

    def update(self):
        """Update editor state."""
        pass

    def draw(self):
        """Draw the editor interface."""
        self.screen.fill(BLACK)

        # Draw highway
        self.draw_highway()

        # Draw notes
        self.draw_notes()

        # Draw UI
        self.draw_ui()

        # Draw toolbar
        self.draw_toolbar()

        # Draw status bar
        self.draw_status_bar()

        pygame.display.flip()

    def draw_highway(self):
        """Draw the note highway."""
        # Highway background
        pygame.draw.rect(self.screen, DARK_GRAY,
                        (self.highway_x, self.highway_y,
                         self.highway_width, self.highway_height))

        # Fret lanes
        for i in range(5):
            x = self.highway_x + 20 + i * self.note_width
            # Lane background (alternating colors for visibility)
            color = (40, 40, 40) if i % 2 == 0 else (50, 50, 50)
            pygame.draw.rect(self.screen, color,
                           (x, self.highway_y, self.note_width, self.highway_height))

            # Lane separator
            pygame.draw.line(self.screen, GRAY,
                           (x, self.highway_y),
                           (x, self.highway_y + self.highway_height), 1)

        # Draw beat lines
        self.draw_beat_lines()

    def draw_beat_lines(self):
        """Draw beat and measure lines."""
        # Calculate ticks per pixel
        visible_ticks = 192 * 8  # 8 measures
        pixels_per_tick = self.highway_height / visible_ticks

        # Draw measure lines (every 4 beats at 192 resolution)
        measure_ticks = 192 * 4
        start_measure = (self.scroll_position // measure_ticks) * measure_ticks

        for tick in range(start_measure, self.scroll_position + visible_ticks, measure_ticks):
            if tick >= self.scroll_position:
                y = self.highway_y + int((tick - self.scroll_position) * pixels_per_tick)
                if self.highway_y <= y <= self.highway_y + self.highway_height:
                    pygame.draw.line(self.screen, MEASURE_LINE_COLOR,
                                   (self.highway_x + 20, y),
                                   (self.highway_x + self.highway_width - 20, y), 2)

        # Draw beat lines (every beat)
        beat_ticks = 192
        for tick in range(start_measure, self.scroll_position + visible_ticks, beat_ticks):
            if tick >= self.scroll_position and tick % measure_ticks != 0:
                y = self.highway_y + int((tick - self.scroll_position) * pixels_per_tick)
                if self.highway_y <= y <= self.highway_y + self.highway_height:
                    pygame.draw.line(self.screen, BEAT_LINE_COLOR,
                                   (self.highway_x + 20, y),
                                   (self.highway_x + self.highway_width - 20, y), 1)

    def draw_notes(self):
        """Draw all notes in the current track."""
        visible_ticks = 192 * 8
        pixels_per_tick = self.highway_height / visible_ticks

        note_colors = [GREEN, RED, YELLOW, BLUE, ORANGE]

        for note in self.current_track.notes:
            # Only draw if visible
            if note.tick < self.scroll_position - note.sustain:
                continue
            if note.tick > self.scroll_position + visible_ticks:
                continue

            # Calculate position
            y = self.highway_y + int((note.tick - self.scroll_position) * pixels_per_tick)
            x = self.highway_x + 20 + note.fret * self.note_width

            # Draw sustain tail
            if note.sustain > 0:
                sustain_height = int(note.sustain * pixels_per_tick)
                pygame.draw.rect(self.screen, SUSTAIN_COLOR,
                               (x + self.note_width // 4, y,
                                self.note_width // 2, sustain_height))

            # Draw note
            color = note_colors[note.fret] if note.fret < len(note_colors) else WHITE

            # Modify color based on flags
            if note.is_tap:
                # Draw tap notes with border
                pygame.draw.rect(self.screen, WHITE,
                               (x + 5, y - self.note_height // 2,
                                self.note_width - 10, self.note_height), 2)

            pygame.draw.rect(self.screen, color,
                           (x + 5, y - self.note_height // 2,
                            self.note_width - 10, self.note_height))

            # Draw forced indicator
            if note.is_forced:
                pygame.draw.circle(self.screen, WHITE,
                                 (x + self.note_width // 2, y), 5)

            # Highlight selected notes
            if note in self.selected_notes:
                pygame.draw.rect(self.screen, WHITE,
                               (x + 5, y - self.note_height // 2,
                                self.note_width - 10, self.note_height), 2)

    def draw_ui(self):
        """Draw UI elements."""
        # Title
        title = self.font.render(f"{self.chart.name} - {self.chart.artist}", True, WHITE)
        self.screen.blit(title, (20, 20))

        # Difficulty indicator
        diff_text = self.font.render(f"Difficulty: {self.current_difficulty.value}", True, WHITE)
        self.screen.blit(diff_text, (20, 50))

        # Note count
        count_text = self.small_font.render(f"Notes: {len(self.current_track.notes)}", True, WHITE)
        self.screen.blit(count_text, (self.highway_x + self.highway_width + 20, 100))

    def draw_toolbar(self):
        """Draw the toolbar with tool selection."""
        toolbar_y = self.height - 80
        toolbar_x = 20

        tools = [
            (Tool.CURSOR, "1: Cursor"),
            (Tool.NOTE, "2: Note"),
            (Tool.ERASER, "3: Eraser"),
            (Tool.STAR_POWER, "4: Star Power"),
            (Tool.BPM, "5: BPM"),
        ]

        for tool, label in tools:
            color = WHITE if tool == self.current_tool else GRAY
            text = self.small_font.render(label, True, color)
            self.screen.blit(text, (toolbar_x, toolbar_y))
            toolbar_x += 120

    def draw_status_bar(self):
        """Draw the status bar."""
        status_y = self.height - 40

        # Snap setting
        snap_text = self.small_font.render(f"Snap: 1/{192 // self.snap}", True, WHITE)
        self.screen.blit(snap_text, (20, status_y))

        # BPM
        bpm = self.chart.get_initial_bpm()
        bpm_text = self.small_font.render(f"BPM: {bpm}", True, WHITE)
        self.screen.blit(bpm_text, (120, status_y))

        # Recording indicator
        if self.is_recording:
            rec_text = self.small_font.render("● RECORDING", True, RED)
            self.screen.blit(rec_text, (220, status_y))

        # Modified indicator
        if self.modified:
            mod_text = self.small_font.render("*", True, YELLOW)
            self.screen.blit(mod_text, (self.width - 40, status_y))

        # Help text
        help_text = self.small_font.render("Ctrl+S: Save | Ctrl+R: Record MIDI | F1-F4: Difficulty", True, GRAY)
        self.screen.blit(help_text, (400, status_y))


def main():
    """Main entry point for visual editor."""
    editor = VisualEditor()

    # Set initial chart metadata
    editor.chart.name = "New Chart"
    editor.chart.artist = "Unknown Artist"

    editor.run()


if __name__ == "__main__":
    main()
