@echo off
@REM Build the client
pyinstaller --onefile --noconsole game_updater.py
@REM Build the updater
pyinstaller --onefile update.py
pause

