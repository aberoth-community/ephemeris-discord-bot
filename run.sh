#!/bin/bash
# run this script to set start the bot and start the http server in a new pane

tmux new -s discordBot

# Navigate to launch directory
cd ephemeris-generator
echo "Activating virtual environment..."
source .venv/bin/activate

# Start the Discord bot
echo "Starting the Discord bot..."
python -m ephemeris & tmux split-window -h

# Navigate to webserver launch directory
cd ephemeris/UpdateWebServer
# Start http server using Waitress
echo "Starting http server with Waitress..."
waitress-serve --listen=0.0.0.0:5000 --threads=1 varUpdateWS:app & split-window -v