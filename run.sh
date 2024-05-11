#!/bin/bash

# Start a new tmux session named '0' and start the first command
tmux new-session -d -s 0 -n Bot

# Send keys to tmux session for activating the virtual environment and starting the Discord bot
# Uncomment following line if run.sh is outside of directory
# tmux send-keys -t 0 'cd ephemeris-generator' C-m
tmux send-keys -t 0 'echo "Activating virtual environment..."' C-m
tmux send-keys -t 0 'source .venv/bin/activate' C-m
tmux send-keys -t 0 'echo "Starting the Discord bot..."' C-m
tmux send-keys -t 0 'python -m ephemeris' C-m

# Split the window horizontally and navigate to the webserver directory
tmux split-window -h -t 0
tmux send-keys -t 0.1 'source .venv/bin/activate' C-m
tmux send-keys -t 0.1 'cd ephemeris/UpdateWebServer' C-m
tmux send-keys -t 0.1 'echo "Starting http server with Waitress..."' C-m
tmux send-keys -t 0.1 'waitress-serve --listen=0.0.0.0:5000 --threads=1 varUpdateWS:app' C-m
tmux split-window -v -t 0

# Attach to the session
tmux attach-session -t 0
