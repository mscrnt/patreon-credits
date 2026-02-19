"""Centralized path resolution for dev mode vs PyInstaller frozen mode.

When running from source (dev):
    bundle dir = project root (where this file lives)
    app dir    = project root

When frozen (PyInstaller --onefile):
    bundle dir = sys._MEIPASS  (temp extraction dir, read-only)
    app dir    = directory containing the .exe (writable)
"""

import os
import sys
import platform
import subprocess


def is_frozen():
    return getattr(sys, 'frozen', False)


def get_bundle_dir():
    """Read-only resources: fonts/, templates/, static/, .env.example"""
    if is_frozen():
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def get_app_dir():
    """Writable directory next to the executable (or project root in dev)."""
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


# ---- Read-only (bundled) paths ----

def get_fonts_dir():
    return os.path.join(get_bundle_dir(), 'fonts')


def get_templates_dir():
    return os.path.join(get_bundle_dir(), 'templates')


def get_static_dir():
    return os.path.join(get_bundle_dir(), 'static')


# ---- Writable paths (next to exe) ----

def get_output_dir():
    d = os.path.join(get_app_dir(), 'output')
    os.makedirs(d, exist_ok=True)
    return d


def get_env_path():
    return os.path.join(get_app_dir(), '.env')


def get_env_example_path():
    return os.path.join(get_bundle_dir(), '.env.example')


def get_cache_path():
    return os.path.join(get_app_dir(), 'patrons_cache.json')


# ---- FFmpeg resolution ----

def get_ffmpeg_dir():
    """Directory for a locally-installed FFmpeg binary (next to exe)."""
    d = os.path.join(get_app_dir(), 'ffmpeg_bin')
    os.makedirs(d, exist_ok=True)
    return d


def get_ffmpeg_path():
    """Return the path to an FFmpeg executable.

    Search order:
    1. ffmpeg_bin/ next to the exe (locally installed by the app)
    2. System PATH
    """
    ext = '.exe' if platform.system() == 'Windows' else ''
    local = os.path.join(get_ffmpeg_dir(), f'ffmpeg{ext}')
    if os.path.isfile(local):
        if platform.system() != 'Windows':
            os.chmod(local, 0o755)
        return local
    return f'ffmpeg{ext}' if ext else 'ffmpeg'


def _subprocess_kwargs():
    """Extra kwargs to hide the console window on Windows."""
    if platform.system() == 'Windows':
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return {'startupinfo': si}
    return {}


def check_ffmpeg():
    """Return True if FFmpeg is callable."""
    try:
        result = subprocess.run(
            [get_ffmpeg_path(), '-version'],
            capture_output=True, timeout=10,
            **_subprocess_kwargs(),
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_ffmpeg_download_url():
    """Return (url, filename) for the current platform's FFmpeg release."""
    system = platform.system()
    if system == 'Windows':
        return (
            'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip',
            'ffmpeg-master-latest-win64-gpl.zip',
        )
    elif system == 'Darwin':
        arch = platform.machine()
        if arch == 'arm64':
            return (
                'https://www.osxexperts.net/ffmpeg7arm.zip',
                'ffmpeg7arm.zip',
            )
        return (
            'https://www.osxexperts.net/ffmpeg7intel.zip',
            'ffmpeg7intel.zip',
        )
    else:
        return (
            'https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz',
            'ffmpeg-release-amd64-static.tar.xz',
        )
