@echo off
title Discord Token Joiner
echo Installing dependencies...
pip install -r requirements.txt

echo Starting Token Joiner...
python token_joiner.py
pause
