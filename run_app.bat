@echo off
title AuraBudget - Desktop Budget & Meal Tracker
echo Starting AuraBudget Desktop Application...
py -3.13 app.py
if %ERRORLEVEL% NEQ 0 (
    echo Python 3.13 not found, trying default py launcher...
    py app.py
)
if %ERRORLEVEL% NEQ 0 (
    echo Trying python command...
    python app.py
)
pause
