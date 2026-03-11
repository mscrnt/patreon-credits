"""Centralized logging configuration with rotation."""
import json
import logging
import os
from logging.handlers import RotatingFileHandler

DEFAULT_LOG_LEVEL = 'INFO'
DEFAULT_MAX_BYTES = 5 * 1024 * 1024   # 5 MB
DEFAULT_BACKUP_COUNT = 3
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def get_log_dir():
    from .path_utils import get_data_dir
    d = os.path.join(get_data_dir(), 'logs')
    os.makedirs(d, exist_ok=True)
    return d


def setup_logging(level=None, max_bytes=None, backup_count=None):
    """Configure root logger with console + rotating file handlers."""
    level = (level or DEFAULT_LOG_LEVEL).upper()
    max_bytes = max_bytes or DEFAULT_MAX_BYTES
    backup_count = backup_count if backup_count is not None else DEFAULT_BACKUP_COUNT

    root = logging.getLogger()
    root.setLevel(getattr(logging, level, logging.INFO))

    # Remove existing handlers (safe for re-init)
    root.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Console handler
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    # Rotating file handler
    log_file = os.path.join(get_log_dir(), 'app.log')
    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # Suppress noisy libraries
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    return root


def load_log_settings():
    """Load logging settings from generate_settings.json."""
    from .path_utils import get_generate_settings_path
    try:
        with open(get_generate_settings_path()) as f:
            settings = json.load(f)
        result = {}
        if 'logLevel' in settings:
            result['level'] = settings['logLevel']
        if 'logMaxSize' in settings:
            result['max_bytes'] = int(settings['logMaxSize'])
        if 'logBackupCount' in settings:
            result['backup_count'] = int(settings['logBackupCount'])
        return result
    except Exception:
        return {}
