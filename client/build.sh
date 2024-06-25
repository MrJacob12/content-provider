#!/bin/bash

# Build the client
pyinstaller --onefile --noconsole game_updater.py

# Build the updater
pyinstaller --onefile update.py

read -p "Press enter to continue"