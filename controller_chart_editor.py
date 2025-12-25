"""
Controller-Based Chart Editor
Edit Clone Hero charts using your guitar controller!
"""

import pygame
import sys
import time
from pathlib import Path
from typing import List
from chart_parser import ChartParser, ChartNote
from controller_capture import ControllerCapture


class ControllerChartEditor:
    """Visual chart editor controlled by guitar controller"""

    WINDOW_WIDTH = 1280
    WINDOW_HEIGHT = 720
    HIGHWAY_WIDTH = 500
    HIGHWAY_X = (WINDOW_WIDTH - HIGHWAY_WIDTH) // 2
    HIGHWAY_TOP = 100
    HIGHWAY_BOTTOM = WINDOW_HEIGHT - 100
    RECEPTOR_Y = HIGHWAY_BOTTOM - 100

    BG_COLOR = (20, 20, 20)
    HIGHWAY_COLOR = (40, 40, 40)
    NOTE_COLORS = {
        0: (50, 205, 50),    # Green
        1: (220, 20, 60),    # Red
        2: (255, 215, 0),    # Yellow
        3: (30, 144, 255),   # Blue
        4: (255, 140, 0)     # Orange
    }
    PIXELS_PER_SECOND = 200

    def __init__(self, chart_path):
        self.chart_path = Path(chart_path)
        pygame.init()
        self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        pygame.display.set_caption(f"Chart Editor - {self.chart_path.stem}")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        self.parser = ChartParser()
        self.chart = self.parser.parse_file(str(self.chart_path))
        self.bpm = self.chart.get('Song', {}).get('Resolution', 120)
        self.resolution = self.chart.get('Song', {}).get('Resolution', 192)

        self.notes: List[ChartNote] = []
        self.load_notes()
        self.notes.sort(key=lambda n: n.position)

        self.playing = False
        self.current_time = 0.0
        self.edit_mode = True
        self.snap_division = 16
        self.last_button_states = [False] * 5
        self.modified = False
        self.show_help = True

        self.controller = ControllerCapture()
        if not self.controller.detect_controller():
            print("Warning: No controller detected!")

    def load_notes(self):
        for track_name in ['ExpertSingle', 'HardSingle', 'MediumSingle', 'EasySingle']:
            track = self.chart.get(track_name, {})
            notes = track.get('notes', [])
            if notes:
                self.notes = notes
                self.current_difficulty = track_name
                return
        self.notes = []
        self.current_difficulty = 'ExpertSingle'

    def position_to_time(self, position: int) -> float:
        beats = position / self.resolution
        return (beats / self.bpm) * 60.0

    def time_to_position(self, time: float) -> int:
        beats = (time * self.bpm) / 60.0
        return int(beats * self.resolution)

    def snap_position(self, position: int) -> int:
        snap_ticks = self.resolution // self.snap_division
        return round(position / snap_ticks) * snap_ticks

    def position_to_y(self, position: int) -> float:
        note_time = self.position_to_time(position)
        time_diff = note_time - self.current_time
        pixels_from_receptor = time_diff * self.PIXELS_PER_SECOND
        return self.RECEPTOR_Y - pixels_from_receptor

    def draw_highway(self):
        highway_rect = pygame.Rect(self.HIGHWAY_X, self.HIGHWAY_TOP,
                                   self.HIGHWAY_WIDTH, self.HIGHWAY_BOTTOM - self.HIGHWAY_TOP)
        pygame.draw.rect(self.screen, self.HIGHWAY_COLOR, highway_rect)

        lane_width = self.HIGHWAY_WIDTH // 5
        for i in range(1, 5):
            x = self.HIGHWAY_X + (i * lane_width)
            pygame.draw.line(self.screen, (60, 60, 60), (x, self.HIGHWAY_TOP), (x, self.HIGHWAY_BOTTOM), 2)

        pygame.draw.line(self.screen, (255, 255, 255),
                        (self.HIGHWAY_X, self.RECEPTOR_Y),
                        (self.HIGHWAY_X + self.HIGHWAY_WIDTH, self.RECEPTOR_Y), 3)

    def draw_receptors(self, button_states):
        lane_width = self.HIGHWAY_WIDTH // 5
        receptor_size = 60

        for lane in range(5):
            x = self.HIGHWAY_X + (lane * lane_width) + (lane_width // 2)
            y = self.RECEPTOR_Y

            if button_states[lane]:
                color = self.NOTE_COLORS[lane]
                size = receptor_size + 10
            else:
                color = tuple(int(c * 0.6) for c in self.NOTE_COLORS[lane])
                size = receptor_size

            pygame.draw.circle(self.screen, color, (x, y), size // 2)
            pygame.draw.circle(self.screen, (255, 255, 255), (x, y), size // 2, 3)

    def draw_notes(self):
        lane_width = self.HIGHWAY_WIDTH // 5
        note_size = 50

        for note in self.notes:
            y = self.position_to_y(note.position)
            if y < self.HIGHWAY_TOP - 100 or y > self.HIGHWAY_BOTTOM + 100:
                continue

            lane = note.fret
            x = self.HIGHWAY_X + (lane * lane_width) + (lane_width // 2)

            if note.sustain > 0:
                sustain_end_y = self.position_to_y(note.position + note.sustain)
                sustain_end_y = max(sustain_end_y, self.HIGHWAY_TOP)
                if sustain_end_y < y:
                    tail_rect = pygame.Rect(x - 15, sustain_end_y, 30, y - sustain_end_y)
                    pygame.draw.rect(self.screen, self.NOTE_COLORS[lane], tail_rect)
                    pygame.draw.rect(self.screen, (255, 255, 255), tail_rect, 2)

            pygame.draw.circle(self.screen, self.NOTE_COLORS[lane], (int(x), int(y)), note_size // 2)
            pygame.draw.circle(self.screen, (255, 255, 255), (int(x), int(y)), note_size // 2, 3)

    def draw_ui(self):
        texts = [
            (f"Time: {self.current_time:.2f}s", (10, 10)),
            (f"BPM: {self.bpm}", (10, 40)),
            (f"Notes: {len(self.notes)}", (10, 70))
        ]
        for text, pos in texts:
            surface = self.small_font.render(text, True, (255, 255, 255))
            self.screen.blit(surface, pos)

        if self.modified:
            mod_text = self.small_font.render("* MODIFIED *", True, (255, 100, 100))
            self.screen.blit(mod_text, (10, 100))

        mode_text = self.font.render("EDIT MODE" if self.edit_mode else "PLAYTHROUGH", True,
                                     (100, 255, 100) if self.edit_mode else (100, 100, 255))
        mode_rect = mode_text.get_rect()
        mode_rect.topright = (self.WINDOW_WIDTH - 10, 10)
        self.screen.blit(mode_text, mode_rect)

        if self.show_help:
            self.draw_help()

    def draw_help(self):
        overlay = pygame.Surface((600, 300))
        overlay.set_alpha(230)
        overlay.fill((30, 30, 30))
        overlay_rect = overlay.get_rect()
        overlay_rect.center = (self.WINDOW_WIDTH // 2, self.WINDOW_HEIGHT // 2)
        self.screen.blit(overlay, overlay_rect)

        help_lines = [
            "CONTROLLER CHART EDITOR", "",
            "D-PAD UP/DOWN: Scroll time",
            "FRET BUTTONS: Add/remove notes",
            "ARROW KEYS: Fine scroll", "",
            "H: Hide help | ESC: Save & exit"
        ]

        y = overlay_rect.top + 30
        for line in help_lines:
            text = self.small_font.render(line, True, (255, 255, 255))
            text_rect = text.get_rect()
            text_rect.centerx = self.WINDOW_WIDTH // 2
            text_rect.top = y
            self.screen.blit(text, text_rect)
            y += 35

    def toggle_note(self, lane: int):
        position = self.time_to_position(self.current_time)
        position = self.snap_position(position)
        snap_tolerance = self.resolution // (self.snap_division * 2)

        for i, note in enumerate(self.notes):
            if note.fret == lane and abs(note.position - position) <= snap_tolerance:
                self.notes.pop(i)
                self.modified = True
                return

        new_note = ChartNote(position=position, fret=lane, sustain=0)
        self.notes.append(new_note)
        self.notes.sort(key=lambda n: n.position)
        self.modified = True

    def handle_controller_input(self):
        if not self.controller.controller:
            return [False] * 5

        controller = self.controller.controller
        button_mapping = self.controller.get_guitar_button_mapping()
        current_button_states = [False] * 5

        for btn_idx, lane in button_mapping.items():
            if btn_idx < controller.get_numbuttons():
                current_button_states[lane] = controller.get_button(btn_idx)

        if self.edit_mode:
            for lane in range(5):
                if current_button_states[lane] and not self.last_button_states[lane]:
                    self.toggle_note(lane)

        self.last_button_states = current_button_states

        if controller.get_numhats() > 0:
            hat = controller.get_hat(0)
            if hat[1] > 0:
                self.current_time = max(0, self.current_time - 0.1)
            elif hat[1] < 0:
                self.current_time += 0.1

        return current_button_states

    def save_chart(self):
        self.chart[self.current_difficulty] = self.chart.get(self.current_difficulty, {})
        self.chart[self.current_difficulty]['notes'] = self.notes
        self.parser.write_file(str(self.chart_path), self.chart)
        self.modified = False
        print(f"Chart saved to {self.chart_path}")

    def run(self):
        running = True
        last_time = time.time()

        while running:
            dt = time.time() - last_time
            last_time = time.time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.modified:
                        self.save_chart()
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_h:
                        self.show_help = not self.show_help
                    elif event.key == pygame.K_ESCAPE:
                        if self.modified:
                            self.save_chart()
                        running = False
                    elif event.key == pygame.K_LEFT:
                        self.current_time = max(0, self.current_time - 1.0)
                    elif event.key == pygame.K_RIGHT:
                        self.current_time += 1.0

            button_states = self.handle_controller_input()

            if self.playing:
                self.current_time += dt

            self.screen.fill(self.BG_COLOR)
            self.draw_highway()
            self.draw_notes()
            self.draw_receptors(button_states)
            self.draw_ui()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        ControllerChartEditor(sys.argv[1]).run()
    else:
        print('Usage: python controller_chart_editor.py <chart_file>')
        print('Example: python controller_chart_editor.py output/song/notes.chart')
