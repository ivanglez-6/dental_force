
Packaging instructions
======================

To create a portable executable for Windows using PyInstaller:

1. Activate your project's virtual environment (the same you use to run the app).
2. Install PyInstaller:
   python -m pip install pyinstaller
3. From the project root run:
   pyinstaller --onefile --windowed pyinstaller.spec
   OR use the included build_exe.bat (on Windows) which will call PyInstaller.
4. The resulting executable will be in the `dist/` folder. Copy the `ui/` folder alongside the exe if needed (some resources such as style sheets or icons may be required).

Notes:
- Test the exe on a clean Windows machine to ensure all assets (QSS, icons) are loaded.
- If the exe fails with missing imports, run PyInstaller without --onefile to inspect collected files, and add hiddenimports to the spec.
