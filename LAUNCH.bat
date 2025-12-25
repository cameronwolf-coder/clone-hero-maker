@echo off
title Clone Hero Chart Maker - Launcher
color 0A
cls

echo.
echo ============================================================
echo       CLONE HERO CHART MAKER - COMPLETE SUITE
echo ============================================================
echo.
echo Choose your tool:
echo.
echo [1] WEB APP (Your GitHub Version - RECOMMENDED)
echo     - AI Audio-to-Chart conversion
echo     - YouTube downloads
echo     - Stem separation (vocals, drums, bass, etc.)
echo     - Web-based chart editor
echo     - Waveform visualization
echo.
echo [2] DESKTOP APP (Tkinter GUI)
echo     - MIDI Recording
echo     - Chart Library (Chorus search)
echo     - Download Manager
echo     - Spotify Search (planned)
echo.
echo [3] MIDI CHART CREATOR (CLI)
echo     - Record MIDI guitar
echo     - Generate charts from performance
echo.
echo [4] VISUAL EDITOR (Pygame)
echo     - Highway view editor
echo     - Interactive note placement
echo.
echo [5] CLI CONVERTER
echo     - Batch MIDI to chart conversion
echo.
echo [6] EXIT
echo.
set /p choice="Enter choice (1-6): "

if "%choice%"=="1" goto webapp
if "%choice%"=="2" goto desktop
if "%choice%"=="3" goto midi
if "%choice%"=="4" goto visual
if "%choice%"=="5" goto cli
if "%choice%"=="6" goto end

:webapp
cls
echo.
echo ============================================================
echo    LAUNCHING WEB APP (Port 8080)
echo ============================================================
echo.
echo Opening in your default browser...
echo Press Ctrl+C to stop the server
echo.
start http://localhost:8080
python app.py
goto end

:desktop
cls
echo.
echo ============================================================
echo    LAUNCHING DESKTOP APP
echo ============================================================
echo.
python main_app.py
goto end

:midi
cls
echo.
echo ============================================================
echo    MIDI CHART CREATOR
echo ============================================================
echo.
python chart_maker.py
goto end

:visual
cls
echo.
echo ============================================================
echo    VISUAL EDITOR
echo ============================================================
echo.
python visual_editor.py
goto end

:cli
cls
echo.
echo ============================================================
echo    CLI CONVERTER
echo ============================================================
echo.
echo Usage: python -m src.cli input.mid output.chart
echo.
echo Examples:
echo   python -m src.cli song.mid song.chart
echo   python -m src.cli --inspect song.mid
echo   python -m src.cli --preview song.mid
echo.
cmd /k
goto end

:end
pause
