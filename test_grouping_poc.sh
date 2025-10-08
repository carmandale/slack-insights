#!/bin/bash
# Quick test of grouping POC

cd "/Users/dalecarman/Groove Jones Dropbox/Dale Carman/Projects/dev/slack-insights"
source .venv/bin/activate

# Test query
echo "What did Dan ask me to do for Orchestrator?" | python3 poc_chat_terminal.py
