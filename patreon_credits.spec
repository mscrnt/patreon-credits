# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Patreon Credits Generator.

Windows/Linux: single-file exe (--onefile style)
macOS: .app bundle via COLLECT + BUNDLE

Build with:
    pyinstaller patreon_credits.spec
"""

import sys
import os

SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))
block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('fonts', 'fonts'),
        ('templates', 'templates'),
        ('static', 'static'),
        ('assets/icon.png', 'assets'),
        ('assets/icon.ico', 'assets'),
        ('.env.example', '.'),
    ],
    hiddenimports=[
        'flask',
        'jinja2',
        'requests',
        'dotenv',
        'PIL',
        'fontTools',
        'fontTools.ttLib',
        'webview',
        'pcg',
        'pcg.app',
        'pcg.launcher',
        'pcg.patreon',
        'pcg.ffmpeg_renderer',
        'pcg.path_utils',
        'pcg.integrations',
        'pcg.presets',
        'pcg.logging_config',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'test'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if sys.platform == 'darwin':
    # macOS: one-folder mode so BUNDLE can wrap it into a .app
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='PatreonCredits',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=os.path.join(SPEC_DIR, 'assets', 'icon.icns') if os.path.exists(os.path.join(SPEC_DIR, 'assets', 'icon.icns')) else None,
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,
        name='PatreonCredits',
    )

    app = BUNDLE(
        coll,
        name='Patreon Credits Generator.app',
        icon=os.path.join(SPEC_DIR, 'assets', 'icon.icns') if os.path.exists(os.path.join(SPEC_DIR, 'assets', 'icon.icns')) else None,
        bundle_identifier='com.mscrnt.patreoncredits',
        info_plist={
            'NSHighResolutionCapable': True,
            'CFBundleShortVersionString': '2.0.0',
        },
    )
else:
    # Windows / Linux: single-file exe
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='PatreonCredits',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,         # GUI app — no terminal
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=os.path.join(SPEC_DIR, 'assets', 'icon.ico') if os.path.exists(os.path.join(SPEC_DIR, 'assets', 'icon.ico')) else None,
    )
