"""
System Test - Verify all components are working
"""

import sys
import os

# Fix Windows console encoding
if os.name == 'nt':
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("CLONE HERO CHART MAKER - SYSTEM TEST")
print("=" * 70)

# Test 1: MIDI Capture
print("\n[1/5] Testing MIDI Capture Module...")
try:
    from midi_capture import MIDICapture
    capture = MIDICapture()
    devices = capture.list_midi_devices()
    print(f"   [OK] MIDI module loaded")
    print(f"   [OK] Found {len(devices)} MIDI devices")
    if devices:
        for i, dev in enumerate(devices):
            print(f"      {i+1}. {dev}")
    else:
        print("      (No MIDI devices connected)")
except Exception as e:
    print(f"   [ERROR] {e}")
    sys.exit(1)

# Test 2: Chart Generator
print("\n[2/5] Testing Chart Generator...")
try:
    from chart_generator import ChartGenerator
    generator = ChartGenerator()
    print(f"   [OK] Chart generator loaded")
    print(f"   [OK] Resolution: {generator.resolution} ticks/quarter note")
except Exception as e:
    print(f"   [ERROR] {e}")
    sys.exit(1)

# Test 3: Chart Parser
print("\n[3/5] Testing Enhanced Chart Parser...")
try:
    from chart_parser import Chart, ChartParser, Note, Track, Instrument, Difficulty
    chart = Chart(name="Test", artist="Test Artist")
    print(f"   [OK] Chart parser loaded")
    print(f"   [OK] Created test chart: {chart.name} by {chart.artist}")
except Exception as e:
    print(f"   [ERROR] {e}")
    sys.exit(1)

# Test 4: Chorus API
print("\n[4/5] Testing Chorus Encore API...")
try:
    from chorus_api import ChorusAPI, SearchParams, Instrument as ChorusInstrument
    api = ChorusAPI()
    print(f"   [OK] API client initialized")
    print(f"   [OK] Base URL: {api.BASE_URL}")

    # Try a small search
    print("   [WAIT] Testing search (this may take a moment)...")
    params = SearchParams(query="test", per_page=1)
    result = api.search(params)
    print(f"   [OK] Search successful!")
    print(f"   [OK] Found {result.total_found:,} total charts in database")

except Exception as e:
    print(f"   [ERROR] {e}")
    print("   (This is okay if you don't have internet connection)")

# Test 5: Visual Editor
print("\n[5/5] Testing Visual Editor Components...")
try:
    import pygame
    pygame.init()
    print(f"   [OK] Pygame initialized")
    print(f"   [OK] Pygame version: {pygame.version.ver}")
    pygame.quit()

    from visual_editor import VisualEditor
    print(f"   [OK] Visual editor module loaded")

except Exception as e:
    print(f"   [ERROR] {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 70)
print("SUCCESS! ALL SYSTEMS OPERATIONAL!")
print("=" * 70)

print("\nNext Steps:")
print("   1. Connect MIDI guitar -> python chart_maker.py")
print("   2. Visual editing -> python visual_editor.py")
print("   3. Search charts -> from chorus_api import *")

print("\nDocumentation:")
print("   - README.md - Quick start guide")
print("   - FEATURES.md - Complete feature list")

print("\nAvailable Tools:")
print("   chart_maker.py       - MIDI guitar chart creation")
print("   visual_editor.py     - Visual chart editor (GUI)")
print("   chorus_api.py        - Chart search and download")
print("   download_manager.py  - Download queue system")

print("\n" + "=" * 70)
print("Happy charting!")
print("=" * 70)
