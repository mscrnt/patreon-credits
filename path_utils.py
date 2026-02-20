"""Centralized path resolution for dev mode vs PyInstaller frozen mode.

When running from source (dev):
    bundle dir = project root (where this file lives)
    app dir    = project root

When frozen (PyInstaller --onefile):
    bundle dir = sys._MEIPASS  (temp extraction dir, read-only)
    app dir    = user-chosen data directory (persisted in config.json):
        Windows default: ~/Documents/PatreonCredits
        macOS default:   ~/Documents/PatreonCredits
        Linux default:   ~/Documents/PatreonCredits

    A small config.json in a fixed platform location stores the user's choice:
        Windows: %LOCALAPPDATA%/PatreonCredits/config.json
        macOS:   ~/Library/Application Support/PatreonCredits/config.json
        Linux:   ~/.config/PatreonCredits/config.json
"""

import json
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


def _get_config_dir():
    """Fixed platform directory for config.json (small, always writable)."""
    system = platform.system()
    if system == 'Windows':
        base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
    elif system == 'Darwin':
        base = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
    else:
        base = os.environ.get('XDG_CONFIG_HOME', os.path.join(os.path.expanduser('~'), '.config'))
    d = os.path.join(base, 'PatreonCredits')
    os.makedirs(d, exist_ok=True)
    return d


def _get_config_file():
    return os.path.join(_get_config_dir(), 'config.json')


def _read_config():
    path = _get_config_file()
    if os.path.isfile(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _write_config(cfg):
    path = _get_config_file()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)


def _default_data_dir():
    """Default data directory per platform.

    Windows/macOS: ~/Documents/PatreonCredits
    Linux:         ~/PatreonCredits  (~/Documents may not exist)
    """
    home = os.path.expanduser('~')
    if platform.system() == 'Linux':
        return os.path.join(home, 'PatreonCredits')
    return os.path.join(home, 'Documents', 'PatreonCredits')


def get_data_dir():
    """Return the user's chosen data directory (read from config.json)."""
    cfg = _read_config()
    return cfg.get('data_dir', _default_data_dir())


def set_data_dir(path):
    """Save a new data directory to config.json."""
    cfg = _read_config()
    cfg['data_dir'] = os.path.abspath(path)
    _write_config(cfg)


def get_app_dir():
    """Writable data directory for .env, cache, output, and ffmpeg.

    When frozen, reads the user's chosen directory from config.json.
    Defaults to ~/Documents/PatreonCredits.
    """
    if is_frozen():
        d = get_data_dir()
        os.makedirs(d, exist_ok=True)
        return d
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
