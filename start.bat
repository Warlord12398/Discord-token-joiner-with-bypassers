echo off
echo Installing dependencies...
pip install -r requirements.txt

echo Running token_joiner.py...
python token_joiner.py

pause
