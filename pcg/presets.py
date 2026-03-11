"""Preset/template management for Generate-tab configurations.

Presets are JSON files stored in get_presets_dir(). Each preset is a
full snapshot of all Generate form fields that can be saved and restored.
"""

import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


def list_presets(presets_dir):
    """Return a list of saved presets with metadata."""
    presets = []
    if not os.path.isdir(presets_dir):
        return presets
    for fname in sorted(os.listdir(presets_dir)):
        if not fname.endswith('.json'):
            continue
        path = os.path.join(presets_dir, fname)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            presets.append({
                'name': fname[:-5],  # strip .json
                'created': data.get('_created', ''),
                'resolution': data.get('resolution', ''),
                'duration': data.get('duration', ''),
            })
        except (json.JSONDecodeError, OSError):
            continue
    return presets


def save_preset(presets_dir, name, config):
    """Save a preset to disk. Adds a _created timestamp."""
    os.makedirs(presets_dir, exist_ok=True)
    safe = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
    if not safe:
        raise ValueError('Invalid preset name')
    config['_created'] = datetime.now().isoformat()
    path = os.path.join(presets_dir, f'{safe}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    return safe


def load_preset(presets_dir, name):
    """Load a preset by name. Returns the config dict."""
    path = os.path.join(presets_dir, f'{name}.json')
    if not os.path.isfile(path):
        raise FileNotFoundError(f'Preset not found: {name}')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def delete_preset(presets_dir, name):
    """Delete a preset by name."""
    path = os.path.join(presets_dir, f'{name}.json')
    if os.path.isfile(path):
        os.remove(path)
        return True
    return False
