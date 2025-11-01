
# PyInstaller spec for Dental Force Monitor
# usage: pyinstaller --onefile --windowed pyinstaller.spec
block_cipher = None

a = Analysis(['main.py'],
             pathex=[],
             binaries=[],
             datas=[('ui/icons/*','ui/icons'),('ui/style.qss','ui')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='dental-force-monitor', debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=False)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=True, name='dental-force-monitor')
