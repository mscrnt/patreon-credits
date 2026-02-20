from flask import Flask, render_template, request, jsonify, send_file, redirect
import hashlib
import os
import platform
import shutil
import subprocess
import tempfile
import zipfile
import tarfile
from datetime import datetime
import requests as http_requests
from patreon import PatreonAPI
from ffmpeg_renderer import VideoRenderer
from dotenv import load_dotenv
from path_utils import (
    get_env_path, get_env_example_path, get_output_dir,
    get_templates_dir, get_static_dir, get_ffmpeg_dir,
    get_ffmpeg_download_url, get_ffmpeg_path,
    check_ffmpeg as check_ffmpeg_util,
    get_data_dir, set_data_dir, _subprocess_kwargs,
)

load_dotenv(get_env_path())

# Copy .env.example -> .env on first run
if not os.path.exists(get_env_path()) and os.path.exists(get_env_example_path()):
    shutil.copy2(get_env_example_path(), get_env_path())
    load_dotenv(get_env_path(), override=True)

app = Flask(
    __name__,
    template_folder=get_templates_dir(),
    static_folder=get_static_dir(),
)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize services
patreon_api = PatreonAPI()
video_renderer = VideoRenderer()


def _is_first_run():
    """True when no credentials are configured (env vars or .env file)."""
    token = os.getenv('PATREON_TOKEN', '')
    dummy = os.getenv('USE_DUMMY_DATA', 'false').lower() == 'true'
    if dummy:
        return False
    if token and token != 'your_creator_access_token_here':
        return False
    return not os.path.exists(get_env_path())


def _write_env(token='', campaign_id='', use_dummy='false'):
    """Write values to the .env file (falls back to os.environ if read-only)."""
    lines = [
        '# Patreon API Configuration',
        f'PATREON_TOKEN={token}',
        f'PATREON_CAMPAIGN_ID={campaign_id}',
        f'USE_DUMMY_DATA={use_dummy}',
        '',
    ]
    try:
        with open(get_env_path(), 'w') as f:
            f.write('\n'.join(lines))
    except OSError:
        os.environ['PATREON_TOKEN'] = token
        os.environ['PATREON_CAMPAIGN_ID'] = campaign_id
        os.environ['USE_DUMMY_DATA'] = use_dummy

@app.route('/')
def index():
    """Main page — redirects to /setup on first run."""
    if _is_first_run():
        return redirect('/setup')
    return render_template('index.html')


@app.route('/setup')
def setup_page():
    """First-run setup wizard."""
    return render_template('setup.html')


@app.route('/health')
def health():
    """Health check endpoint for Docker/orchestration."""
    return jsonify({'status': 'ok'})


@app.route('/favicon.ico')
def favicon():
    icon = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.png')
    return send_file(icon, mimetype='image/png')


@app.route('/api/videos')
def list_videos():
    """List all generated videos with metadata."""
    output_dir = get_output_dir()
    videos = []
    for f in sorted(os.listdir(output_dir), reverse=True):
        if not f.endswith('.mp4'):
            continue
        filepath = os.path.join(output_dir, f)
        stat = os.stat(filepath)
        if stat.st_size == 0:
            continue
        ts_str = f.replace('credits_', '').replace('.mp4', '')
        try:
            ts = datetime.strptime(ts_str, '%Y%m%d_%H%M%S')
            created = ts.isoformat()
        except ValueError:
            created = datetime.fromtimestamp(stat.st_mtime).isoformat()
        videos.append({
            'filename': f,
            'size': stat.st_size,
            'created': created,
            'video_url': f'/output/{f}',
            'thumbnail_url': f'/api/thumbnail/{f}',
            'download_url': f'/download/{f}',
        })
    return jsonify({'videos': videos})


def _thumb_path(filename):
    """Return hex-based thumbnail path: thumbnails/<2-char prefix>/<hash>.jpg"""
    digest = hashlib.sha256(filename.encode()).hexdigest()
    prefix = digest[:2]
    thumb_dir = os.path.join(get_static_dir(), 'thumbnails', prefix)
    os.makedirs(thumb_dir, exist_ok=True)
    return os.path.join(thumb_dir, digest + '.jpg')


@app.route('/api/thumbnail/<filename>')
def video_thumbnail(filename):
    """Serve a thumbnail for a video, generating it on-the-fly if needed."""
    if '/' in filename or '\\' in filename or '..' in filename:
        return jsonify({'error': 'Invalid filename'}), 400
    video_path = os.path.join(get_output_dir(), filename)
    if not os.path.exists(video_path):
        return jsonify({'error': 'Video not found'}), 404

    thumb_path = _thumb_path(filename)

    if not os.path.exists(thumb_path):
        ffmpeg = get_ffmpeg_path()
        cmd = [ffmpeg, '-i', video_path, '-ss', '1', '-vframes', '1',
               '-vf', 'scale=320:-1', '-q:v', '3', '-y', thumb_path]
        try:
            subprocess.run(cmd, capture_output=True, timeout=10,
                           **_subprocess_kwargs())
        except Exception:
            return jsonify({'error': 'Thumbnail generation failed'}), 500

    if os.path.exists(thumb_path):
        return send_file(thumb_path, mimetype='image/jpeg')
    return jsonify({'error': 'Thumbnail not found'}), 404


@app.route('/api/videos/<filename>', methods=['DELETE'])
def delete_video(filename):
    """Delete a generated video and its thumbnail."""
    if '/' in filename or '\\' in filename or '..' in filename:
        return jsonify({'error': 'Invalid filename'}), 400
    video_path = os.path.join(get_output_dir(), filename)
    if not os.path.exists(video_path):
        return jsonify({'error': 'File not found'}), 404

    os.remove(video_path)
    thumb_path = _thumb_path(filename)
    if os.path.exists(thumb_path):
        os.remove(thumb_path)
    return jsonify({'success': True})


@app.route('/check-ffmpeg')
def check_ffmpeg():
    """Check if FFmpeg is installed"""
    is_installed = check_ffmpeg_util()
    return jsonify({'installed': is_installed})

@app.route('/generate', methods=['POST'])
def generate_credits():
    """Generate the credits video"""
    try:
        # Get form data
        data = request.get_json()
        message = data.get('message', 'This video was made possible by our Patreon supporters:')
        duration = int(data.get('duration', 15))
        resolution = data.get('resolution', '1280x720')
        use_cache = data.get('use_cache', False)
        message_style = data.get('message_style', {'size': 36, 'color': '#ffffff', 'font': 'noto_sans', 'bold': True, 'align': 'left'})
        patron_style = data.get('patron_style', {'size': 20, 'color': '#FFD700', 'font': 'noto_sans', 'bold': False})
        columns = int(data.get('columns', 4))
        name_align = data.get('name_align', 'left')
        truncate_length = int(data.get('truncate_length', 15))
        word_wrap = data.get('word_wrap', False)
        name_spacing = data.get('name_spacing', False)
        bg_color = data.get('bg_color', '#000000')

        custom_names = data.get('custom_names', '').strip()

        # Validate duration
        if duration < 5 or duration > 60:
            return jsonify({'error': 'Duration must be between 5 and 60 seconds'}), 400

        # Get patrons — custom names override Patreon fetch
        if custom_names:
            patrons = [n.strip() for n in custom_names.split('\n') if n.strip()]
        elif use_cache:
            patrons = patreon_api.get_cached_patrons()
            if not patrons:
                patrons = patreon_api.fetch_active_patrons()
        else:
            patrons = patreon_api.fetch_active_patrons()

        if not patrons:
            return jsonify({'error': 'No active patrons found'}), 404

        # Generate video
        video_filename = video_renderer.render_video(
            message, patrons, duration, resolution,
            message_style, patron_style, columns, name_align,
            truncate_length, word_wrap, name_spacing, bg_color)

        return jsonify({
            'success': True,
            'video_url': f'/output/{video_filename}',
            'patron_count': len(patrons),
            'filename': video_filename
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/output/<filename>')
def serve_output(filename):
    """Serve a generated video from the writable output directory."""
    file_path = os.path.join(get_output_dir(), filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    return jsonify({'error': 'File not found'}), 404


@app.route('/download/<filename>')
def download_video(filename):
    """Download the generated video"""
    try:
        file_path = os.path.join(get_output_dir(), filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=f'patreon_credits_{filename}')
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/open-output-folder', methods=['POST'])
def open_output_folder():
    """Open the output directory in the system file manager."""
    output_dir = get_output_dir()
    os.makedirs(output_dir, exist_ok=True)
    try:
        system = platform.system()
        if system == 'Windows':
            os.startfile(output_dir)
        elif system == 'Darwin':
            subprocess.Popen(['open', output_dir])
        else:
            subprocess.Popen(['xdg-open', output_dir])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/patron-count')
def get_patron_count():
    """Get the current patron count"""
    try:
        patrons = patreon_api.get_cached_patrons()
        if not patrons:
            patrons = patreon_api.fetch_active_patrons()
        return jsonify({'count': len(patrons)})
    except Exception as e:
        return jsonify({'error': str(e), 'count': 0}), 500

@app.route('/refresh-patrons', methods=['POST'])
def refresh_patrons():
    """Force-refresh the patron list from Patreon API and update cache"""
    try:
        patrons = patreon_api.fetch_active_patrons()
        return jsonify({'count': len(patrons), 'patrons': patrons})
    except Exception as e:
        return jsonify({'error': str(e), 'count': 0}), 500

@app.route('/settings', methods=['GET'])
def get_settings():
    """Return current settings as JSON (or redirect to Settings tab)."""
    if 'text/html' in request.headers.get('Accept', ''):
        return redirect('/#settings-tab')
    # Otherwise return JSON for the JS fetch calls
    load_dotenv(get_env_path(), override=True)
    return jsonify({
        'patreon_token': os.getenv('PATREON_TOKEN', ''),
        'campaign_id': os.getenv('PATREON_CAMPAIGN_ID', ''),
        'use_dummy_data': os.getenv('USE_DUMMY_DATA', 'false').lower() == 'true',
    })


@app.route('/settings', methods=['POST'])
def save_settings():
    """Save Patreon credentials to .env and reinitialise."""
    global patreon_api
    data = request.get_json()
    token = data.get('patreon_token', '').strip()
    campaign_id = data.get('campaign_id', '').strip()
    use_dummy = 'true' if data.get('use_dummy_data') else 'false'

    _write_env(token, campaign_id, use_dummy)
    load_dotenv(get_env_path(), override=True)
    patreon_api = PatreonAPI()

    return jsonify({'success': True})


@app.route('/detect-campaign', methods=['POST'])
def detect_campaign():
    """Auto-detect campaign ID from a Patreon token."""
    data = request.get_json()
    token = data.get('token', '').strip()
    if not token:
        return jsonify({'error': 'No token provided'}), 400
    campaign_id, error = PatreonAPI.detect_campaign_id(token)
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'campaign_id': campaign_id})


@app.route('/data-dir', methods=['GET'])
def get_data_dir_route():
    """Return the current data directory path."""
    return jsonify({'path': get_data_dir()})


@app.route('/data-dir', methods=['POST'])
def set_data_dir_route():
    """Set a new data directory. Validates the path is writable."""
    data = request.get_json()
    path = data.get('path', '').strip()
    if not path:
        return jsonify({'error': 'No path provided', 'success': False}), 400
    path = os.path.abspath(path)
    try:
        os.makedirs(path, exist_ok=True)
        # Verify writable
        test_file = os.path.join(path, '.write_test')
        with open(test_file, 'w') as f:
            f.write('ok')
        os.remove(test_file)
    except OSError as e:
        return jsonify({'error': f'Cannot write to directory: {e}', 'success': False}), 400
    set_data_dir(path)
    return jsonify({'success': True, 'path': path})


@app.route('/install-ffmpeg', methods=['POST'])
def install_ffmpeg():
    """Download and install FFmpeg to the app's ffmpeg_bin/ directory."""
    try:
        url, archive_name = get_ffmpeg_download_url()
        dest_dir = get_ffmpeg_dir()
        system = platform.system()

        # Download to temp file
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=archive_name)
        tmp.close()
        resp = http_requests.get(url, stream=True, timeout=300)
        resp.raise_for_status()
        with open(tmp.name, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)

        ext = '.exe' if system == 'Windows' else ''
        ffmpeg_dest = os.path.join(dest_dir, f'ffmpeg{ext}')

        if archive_name.endswith('.zip'):
            with zipfile.ZipFile(tmp.name) as zf:
                for info in zf.infolist():
                    basename = os.path.basename(info.filename)
                    if basename in (f'ffmpeg{ext}', 'ffmpeg'):
                        with zf.open(info) as src, open(ffmpeg_dest, 'wb') as dst:
                            shutil.copyfileobj(src, dst)
                        break
        elif archive_name.endswith(('.tar.xz', '.tar.gz')):
            with tarfile.open(tmp.name) as tf:
                for member in tf.getmembers():
                    if os.path.basename(member.name) == 'ffmpeg':
                        src = tf.extractfile(member)
                        if src:
                            with open(ffmpeg_dest, 'wb') as dst:
                                shutil.copyfileobj(src, dst)
                        break

        os.unlink(tmp.name)

        if not os.path.isfile(ffmpeg_dest):
            return jsonify({'success': False, 'error': 'Could not find ffmpeg binary in archive'}), 500

        if system != 'Windows':
            os.chmod(ffmpeg_dest, 0o755)

        # Reinitialise renderer so it picks up the new path
        global video_renderer
        video_renderer = VideoRenderer()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/spec')
def api_spec():
    """OpenAPI 3.0 specification"""
    font_keys = sorted([
        'noto_sans', 'noto_serif_cjk', 'lxgw_wenkai', 'zen_maru_gothic',
        'mplus_rounded', 'shippori_mincho', 'inter', 'roboto', 'open_sans',
        'poppins', 'montserrat', 'raleway', 'quicksand', 'source_sans',
        'lato', 'nunito', 'rubik', 'dm_sans', 'josefin_sans', 'ubuntu',
        'oswald', 'bebas_neue', 'cinzel', 'playfair_display', 'merriweather',
        'crimson_text', 'lora', 'libre_baskerville', 'arvo', 'neuton',
        'alfa_slab_one', 'bangers', 'permanent_marker', 'pacifico', 'playwrite',
    ])
    spec = {
        'openapi': '3.0.3',
        'info': {
            'title': 'Patreon Credits Generator API',
            'description': 'Generate scrolling end-credits videos featuring Patreon supporters.',
            'version': '1.4.0',
        },
        'paths': {
            '/generate': {
                'post': {
                    'summary': 'Generate credits video',
                    'description': 'Fetches patrons and renders a scrolling credits MP4 video.',
                    'requestBody': {
                        'required': True,
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'properties': {
                                        'message': {
                                            'type': 'string',
                                            'default': 'This video was made possible by our Patreon supporters:',
                                            'description': 'Header text displayed at the top of the video.',
                                        },
                                        'duration': {
                                            'type': 'integer',
                                            'minimum': 5,
                                            'maximum': 60,
                                            'default': 15,
                                            'description': 'Video duration in seconds.',
                                        },
                                        'resolution': {
                                            'type': 'string',
                                            'enum': ['1280x720', '1920x1080', '3840x2160'],
                                            'default': '1280x720',
                                            'description': 'Output video resolution.',
                                        },
                                        'columns': {
                                            'type': 'integer',
                                            'minimum': 1,
                                            'maximum': 5,
                                            'default': 4,
                                            'description': 'Number of name columns.',
                                        },
                                        'name_align': {
                                            'type': 'string',
                                            'enum': ['left', 'center', 'right'],
                                            'default': 'left',
                                            'description': 'Horizontal alignment of the name columns block.',
                                        },
                                        'truncate_length': {
                                            'type': 'integer',
                                            'minimum': 0,
                                            'maximum': 50,
                                            'default': 15,
                                            'description': 'Max characters per name (0 = no truncation).',
                                        },
                                        'word_wrap': {
                                            'type': 'boolean',
                                            'default': False,
                                            'description': 'Hyphen-wrap long names instead of truncating with ellipsis.',
                                        },
                                        'name_spacing': {
                                            'type': 'boolean',
                                            'default': False,
                                            'description': 'Add an extra line of spacing between each row of names.',
                                        },
                                        'bg_color': {
                                            'type': 'string',
                                            'default': '#000000',
                                            'description': 'Background color as hex string.',
                                        },
                                        'use_cache': {
                                            'type': 'boolean',
                                            'default': False,
                                            'description': 'Use cached patron list instead of fetching fresh data.',
                                        },
                                        'message_style': {
                                            'type': 'object',
                                            'description': 'Styling for the header message.',
                                            'properties': {
                                                'size': {'type': 'integer', 'default': 36, 'description': 'Font size in px (before resolution scaling).'},
                                                'color': {'type': 'string', 'default': '#ffffff', 'description': 'Hex color.'},
                                                'font': {'type': 'string', 'enum': font_keys, 'default': 'noto_sans'},
                                                'bold': {'type': 'boolean', 'default': True},
                                                'align': {'type': 'string', 'enum': ['left', 'center', 'right', 'justify'], 'default': 'left'},
                                            },
                                        },
                                        'patron_style': {
                                            'type': 'object',
                                            'description': 'Styling for patron names.',
                                            'properties': {
                                                'size': {'type': 'integer', 'default': 20, 'description': 'Font size in px (before resolution scaling).'},
                                                'color': {'type': 'string', 'default': '#FFD700', 'description': 'Hex color.'},
                                                'font': {'type': 'string', 'enum': font_keys, 'default': 'noto_sans'},
                                                'bold': {'type': 'boolean', 'default': False},
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                    'responses': {
                        '200': {
                            'description': 'Video generated successfully.',
                            'content': {
                                'application/json': {
                                    'schema': {
                                        'type': 'object',
                                        'properties': {
                                            'success': {'type': 'boolean'},
                                            'video_url': {'type': 'string', 'description': 'Relative URL to the generated MP4.'},
                                            'patron_count': {'type': 'integer'},
                                            'filename': {'type': 'string'},
                                        },
                                    },
                                },
                            },
                        },
                        '400': {'description': 'Invalid parameters.'},
                        '404': {'description': 'No active patrons found.'},
                        '500': {'description': 'Server error.'},
                    },
                },
            },
            '/patron-count': {
                'get': {
                    'summary': 'Get patron count',
                    'description': 'Returns the number of active patrons.',
                    'responses': {
                        '200': {
                            'description': 'Patron count.',
                            'content': {
                                'application/json': {
                                    'schema': {
                                        'type': 'object',
                                        'properties': {
                                            'count': {'type': 'integer'},
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
            '/check-ffmpeg': {
                'get': {
                    'summary': 'Check FFmpeg installation',
                    'description': 'Returns whether FFmpeg is available on the server.',
                    'responses': {
                        '200': {
                            'description': 'FFmpeg status.',
                            'content': {
                                'application/json': {
                                    'schema': {
                                        'type': 'object',
                                        'properties': {
                                            'installed': {'type': 'boolean'},
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
            '/refresh-patrons': {
                'post': {
                    'summary': 'Refresh patron list',
                    'description': 'Force-refresh the patron list from the Patreon API and update the cache.',
                    'responses': {
                        '200': {
                            'description': 'Refreshed patron list.',
                            'content': {
                                'application/json': {
                                    'schema': {
                                        'type': 'object',
                                        'properties': {
                                            'count': {'type': 'integer'},
                                            'patrons': {
                                                'type': 'array',
                                                'items': {'type': 'string'},
                                                'description': 'List of patron display names.',
                                            },
                                        },
                                    },
                                },
                            },
                        },
                        '500': {'description': 'Server error.'},
                    },
                },
            },
            '/download/{filename}': {
                'get': {
                    'summary': 'Download generated video',
                    'description': 'Download a previously generated credits video by filename.',
                    'parameters': [
                        {
                            'name': 'filename',
                            'in': 'path',
                            'required': True,
                            'schema': {'type': 'string'},
                            'description': 'The video filename returned by /generate.',
                        },
                    ],
                    'responses': {
                        '200': {
                            'description': 'MP4 video file.',
                            'content': {'video/mp4': {'schema': {'type': 'string', 'format': 'binary'}}},
                        },
                        '404': {'description': 'File not found.'},
                    },
                },
            },
            '/api/videos': {
                'get': {
                    'summary': 'List generated videos',
                    'description': 'Returns all generated video files with metadata (size, date, URLs).',
                    'responses': {
                        '200': {
                            'description': 'List of videos.',
                            'content': {
                                'application/json': {
                                    'schema': {
                                        'type': 'object',
                                        'properties': {
                                            'videos': {
                                                'type': 'array',
                                                'items': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'filename': {'type': 'string'},
                                                        'size': {'type': 'integer', 'description': 'File size in bytes.'},
                                                        'created': {'type': 'string', 'format': 'date-time'},
                                                        'video_url': {'type': 'string'},
                                                        'thumbnail_url': {'type': 'string'},
                                                        'download_url': {'type': 'string'},
                                                    },
                                                },
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
            '/api/videos/{filename}': {
                'delete': {
                    'summary': 'Delete a generated video',
                    'description': 'Deletes a video file and its cached thumbnail.',
                    'parameters': [
                        {
                            'name': 'filename',
                            'in': 'path',
                            'required': True,
                            'schema': {'type': 'string'},
                            'description': 'The video filename to delete.',
                        },
                    ],
                    'responses': {
                        '200': {
                            'description': 'Video deleted.',
                            'content': {
                                'application/json': {
                                    'schema': {
                                        'type': 'object',
                                        'properties': {
                                            'success': {'type': 'boolean'},
                                        },
                                    },
                                },
                            },
                        },
                        '404': {'description': 'File not found.'},
                    },
                },
            },
            '/api/thumbnail/{filename}': {
                'get': {
                    'summary': 'Get video thumbnail',
                    'description': 'Returns a JPEG thumbnail for a generated video. Thumbnails are generated on first request and cached.',
                    'parameters': [
                        {
                            'name': 'filename',
                            'in': 'path',
                            'required': True,
                            'schema': {'type': 'string'},
                            'description': 'The video filename.',
                        },
                    ],
                    'responses': {
                        '200': {
                            'description': 'JPEG thumbnail image.',
                            'content': {'image/jpeg': {'schema': {'type': 'string', 'format': 'binary'}}},
                        },
                        '404': {'description': 'Video not found.'},
                        '500': {'description': 'Thumbnail generation failed.'},
                    },
                },
            },
        },
    }
    return jsonify(spec)


@app.route('/api/docs')
def api_docs():
    """Swagger UI page"""
    return render_template('swagger.html')


if __name__ == '__main__':
    if _is_first_run():
        print("First run detected — open http://localhost:5000 to complete setup.")
    else:
        use_dummy_data = os.getenv('USE_DUMMY_DATA', 'false').lower() == 'true'
        if not use_dummy_data and (not os.getenv('PATREON_TOKEN') or not os.getenv('PATREON_CAMPAIGN_ID')):
            print("WARNING: No Patreon credentials found.")
            print("Running in DUMMY DATA mode for testing...")
            os.environ['USE_DUMMY_DATA'] = 'true'
            patreon_api = PatreonAPI()

    if not check_ffmpeg_util():
        print("WARNING: FFmpeg not found. You can install it from the Settings page.")

    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host=host, port=port)
