
@echo off
REM Build executable (Windows) - requires pyinstaller installed in the active venv
python -m pip install pyinstaller
pyinstaller --onefile --windowed pyinstaller.spec
echo Build finished. See dist\ directory.
pause
