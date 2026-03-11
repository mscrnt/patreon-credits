from flask import Flask, render_template, request, jsonify, send_file, redirect
from werkzeug.utils import secure_filename
import hashlib
import io
import json
import logging
import os
import platform
import shutil
import subprocess
import tempfile
import zipfile
import tarfile
from datetime import datetime
import requests as http_requests

logger = logging.getLogger(__name__)
from .patreon import PatreonAPI
from .ffmpeg_renderer import VideoRenderer
from dotenv import load_dotenv
from .path_utils import (
    get_env_path, get_env_example_path, get_output_dir,
    get_templates_dir, get_static_dir, get_ffmpeg_dir,
    get_ffmpeg_download_url, get_ffmpeg_path,
    check_ffmpeg as check_ffmpeg_util,
    get_data_dir, set_data_dir, _subprocess_kwargs,
    get_generate_settings_path, get_presets_dir, get_uploads_dir,
    get_kofi_cache_path,
    get_bmc_cache_path,
    get_se_cache_path,
    get_youtube_token_path,
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
    from .path_utils import get_assets_dir
    icon = os.path.join(get_assets_dir(), 'icon.png')
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
        logger.info("Starting video generation")
        # Get form data
        data = request.get_json()
        message = data.get('message', 'This video was made possible by our Patreon supporters:')
        duration = int(data.get('duration', 15))
        resolution = data.get('resolution', '1280x720')
        message_style = data.get('message_style', {'size': 36, 'color': '#ffffff', 'font': 'noto_sans', 'bold': True, 'align': 'left'})
        patron_style = data.get('patron_style', {'size': 20, 'color': '#FFD700', 'font': 'noto_sans', 'bold': False})
        columns = int(data.get('columns', 4))
        name_align = data.get('name_align', 'left')
        truncate_length = int(data.get('truncate_length', 15))
        word_wrap = data.get('word_wrap', False)
        name_spacing = data.get('name_spacing', False)
        bg_color = data.get('bg_color', '#000000')

        custom_names = data.get('custom_names', '').strip()

        # Effects parameters (v2)
        fade_in = float(data.get('fade_in', 0))
        fade_out = float(data.get('fade_out', 0))
        speed_multiplier = float(data.get('speed_multiplier', 1.0))
        fps = int(data.get('fps', 30))
        if fps not in (30, 60):
            fps = 30
        audio_volume = float(data.get('audio_volume', 1.0))
        logo_position = data.get('logo_position', 'top-right')
        logo_size = int(data.get('logo_size', 80))
        qr_position = data.get('qr_position', 'bottom-right')
        qr_size = int(data.get('qr_size', 120))

        # Resolve file paths for uploads
        uploads_dir = get_uploads_dir()
        bg_image = None
        bg_type = data.get('bg_type', 'solid')
        if bg_type == 'image':
            bg_file = data.get('bg_image', '')
            if bg_file:
                bg_image = os.path.join(uploads_dir, bg_file)

        bg_gradient = None
        if bg_type == 'gradient':
            bg_gradient = {
                'color1': data.get('bg_gradient_color1', '#000000'),
                'color2': data.get('bg_gradient_color2', '#333333'),
                'direction': data.get('bg_gradient_direction', 'vertical'),
            }

        audio_file = None
        audio_name = data.get('audio_file', '')
        if audio_name:
            audio_file = os.path.join(uploads_dir, audio_name)

        logo_file = None
        logo_name = data.get('logo_file', '')
        if logo_name:
            logo_file = os.path.join(uploads_dir, logo_name)

        qr_image = None
        qr_url = data.get('qr_url', '').strip()
        if qr_url:
            try:
                import qrcode
                qr = qrcode.QRCode(box_size=10, border=2)
                qr.add_data(qr_url)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color='white', back_color='black')
                qr_tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                qr_img.save(qr_tmp.name)
                qr_tmp.close()
                qr_image = qr_tmp.name
            except ImportError:
                pass

        # Validate duration
        if duration < 5 or duration > 60:
            return jsonify({'error': 'Duration must be between 5 and 60 seconds'}), 400

        # Get patrons — custom names override Patreon fetch
        # Auto-cache: reuse cached data if fetched within the last hour
        if custom_names:
            patrons = [n.strip() for n in custom_names.split('\n') if n.strip()]
        else:
            patrons = patreon_api.get_cached_patrons(max_age=3600)
            if not patrons:
                patrons = patreon_api.fetch_active_patrons()

        if not patrons:
            return jsonify({'error': 'No active patrons found'}), 404

        # Generate video
        try:
            video_filename = video_renderer.render_video(
                message, patrons, duration, resolution,
                message_style, patron_style, columns, name_align,
                truncate_length, word_wrap, name_spacing, bg_color,
                fade_in=fade_in, fade_out=fade_out,
                speed_multiplier=speed_multiplier, fps=fps,
                bg_image=bg_image, bg_gradient=bg_gradient,
                audio_file=audio_file, audio_volume=audio_volume,
                logo_file=logo_file, logo_position=logo_position,
                logo_size=logo_size,
                qr_image=qr_image, qr_position=qr_position,
                qr_size=qr_size)
        finally:
            if qr_image and os.path.exists(qr_image):
                os.unlink(qr_image)

        logger.info("Video generated: %s (%d patrons)", video_filename, len(patrons))
        return jsonify({
            'success': True,
            'video_url': f'/output/{video_filename}',
            'patron_count': len(patrons),
            'filename': video_filename
        })

    except Exception as e:
        logger.error("Video generation failed: %s", e, exc_info=True)
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
        logger.info("Refreshed patrons: %d names", len(patrons))
        return jsonify({'count': len(patrons), 'patrons': patrons})
    except Exception as e:
        logger.error("Patron refresh failed: %s", e)
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


def _load_generate_settings():
    """Load generate settings from disk as a dict."""
    path = get_generate_settings_path()
    if os.path.isfile(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


@app.route('/api/generate-settings', methods=['GET'])
def get_generate_settings():
    """Return saved Generate-tab form values from disk."""
    path = get_generate_settings_path()
    if os.path.isfile(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        except (json.JSONDecodeError, OSError):
            pass
    return jsonify({})


@app.route('/api/generate-settings', methods=['POST'])
def save_generate_settings():
    """Persist all Generate-tab form values to disk as JSON."""
    data = request.get_json()
    path = get_generate_settings_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return jsonify({'success': True})
    except OSError as e:
        return jsonify({'success': False, 'error': str(e)}), 500


ALLOWED_IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'}
ALLOWED_AUDIO_EXT = {'.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac'}


@app.route('/upload/image', methods=['POST'])
def upload_image():
    """Accept an image upload (logo, background). Returns the saved filename."""
    f = request.files.get('file')
    if not f or not f.filename:
        return jsonify({'error': 'No file provided'}), 400
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXT:
        return jsonify({'error': f'Unsupported image type: {ext}'}), 400
    name = secure_filename(f.filename)
    dest = os.path.join(get_uploads_dir(), name)
    f.save(dest)
    logger.info("Uploaded image: %s", name)
    return jsonify({'filename': name, 'path': dest})


@app.route('/upload/audio', methods=['POST'])
def upload_audio():
    """Accept an audio upload (background music). Returns the saved filename."""
    f = request.files.get('file')
    if not f or not f.filename:
        return jsonify({'error': 'No file provided'}), 400
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ALLOWED_AUDIO_EXT:
        return jsonify({'error': f'Unsupported audio type: {ext}'}), 400
    name = secure_filename(f.filename)
    dest = os.path.join(get_uploads_dir(), name)
    f.save(dest)
    logger.info("Uploaded audio: %s", name)
    return jsonify({'filename': name, 'path': dest})


@app.route('/uploads/<filename>')
def serve_upload(filename):
    """Serve an uploaded file (images, audio)."""
    if '/' in filename or '\\' in filename or '..' in filename:
        return jsonify({'error': 'Invalid filename'}), 400
    path = os.path.join(get_uploads_dir(), filename)
    if os.path.isfile(path):
        return send_file(path)
    return jsonify({'error': 'File not found'}), 404


@app.route('/api/assets')
def list_assets():
    """List uploaded assets, filtered by type (images or audio)."""
    asset_type = request.args.get('type', 'images')
    allowed = ALLOWED_IMAGE_EXT if asset_type == 'images' else ALLOWED_AUDIO_EXT
    uploads = get_uploads_dir()
    assets = []
    try:
        for entry in os.scandir(uploads):
            if not entry.is_file():
                continue
            ext = os.path.splitext(entry.name)[1].lower()
            if ext not in allowed:
                continue
            stat = entry.stat()
            assets.append({
                'filename': entry.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'url': f'/uploads/{entry.name}',
            })
    except OSError:
        pass
    assets.sort(key=lambda a: a['modified'], reverse=True)
    return jsonify({'assets': assets})


@app.route('/api/assets/<filename>', methods=['DELETE'])
def delete_asset(filename):
    """Delete an uploaded asset."""
    if '/' in filename or '\\' in filename or '..' in filename:
        return jsonify({'error': 'Invalid filename'}), 400
    path = os.path.join(get_uploads_dir(), filename)
    if not os.path.isfile(path):
        return jsonify({'error': 'File not found'}), 404
    try:
        os.remove(path)
        return jsonify({'success': True})
    except OSError as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/qr')
def generate_qr():
    """Generate a QR code PNG on-the-fly for a given URL."""
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify({'error': 'No url parameter'}), 400
    size = int(request.args.get('size', 200))
    try:
        import qrcode
        qr = qrcode.QRCode(box_size=max(1, size // 25), border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='white', back_color='transparent')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return send_file(buf, mimetype='image/png')
    except ImportError:
        return jsonify({'error': 'qrcode package not installed'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/integrations/bmc/fetch', methods=['POST'])
def bmc_fetch():
    """Fetch supporter names from Buy Me a Coffee."""
    data = request.get_json()
    token = (data.get('token') or '').strip()
    if not token:
        return jsonify({'error': 'No BMC token provided'}), 400
    try:
        from .integrations import BuyMeACoffeeAPI
        names = BuyMeACoffeeAPI(token).fetch_supporters()
        return jsonify({'names': names})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/webhooks/bmc', methods=['POST'])
def bmc_webhook():
    """Receive Buy Me a Coffee webhook events and store supporter names."""
    raw = request.get_data(as_text=True)
    if not raw:
        return jsonify({'error': 'No data'}), 400
    try:
        payload = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return jsonify({'error': 'Invalid JSON'}), 400
    try:
        from .integrations import BmcStore
        store = BmcStore(get_bmc_cache_path())
        store.add_webhook_event(payload)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/integrations/bmc/names')
def bmc_names():
    """Return stored BMC supporter names from webhooks."""
    try:
        from .integrations import BmcStore
        store = BmcStore(get_bmc_cache_path())
        names = store.get_names()
        return jsonify({'names': names})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/integrations/bmc/clear', methods=['POST'])
def bmc_clear():
    """Clear stored BMC supporter names (all or older than N days)."""
    try:
        from .integrations import BmcStore
        store = BmcStore(get_bmc_cache_path())
        data = request.get_json(silent=True) or {}
        days = data.get('days')
        if days is not None:
            days = int(days)
            removed = store.clear_older_than(days)
            return jsonify({'success': True, 'removed': removed})
        store.clear_names()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/integrations/bmc/schedule', methods=['GET'])
def bmc_get_schedule():
    """Return the current BMC auto-clear schedule and metadata."""
    try:
        from .integrations import BmcStore
        store = BmcStore(get_bmc_cache_path())
        return jsonify(store.get_schedule())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/integrations/bmc/schedule', methods=['POST'])
def bmc_set_schedule():
    """Set the BMC auto-clear schedule."""
    data = request.get_json()
    schedule = data.get('schedule', 'never')
    if isinstance(schedule, str) and schedule.isdigit():
        schedule = int(schedule)
    try:
        from .integrations import BmcStore
        store = BmcStore(get_bmc_cache_path())
        store.set_schedule(schedule)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/integrations/streamelements/fetch', methods=['POST'])
def streamelements_fetch():
    """Fetch tipper names from StreamElements and store locally."""
    data = request.get_json()
    jwt = (data.get('jwt') or '').strip()
    channel_id = (data.get('channel_id') or '').strip()
    if not jwt or not channel_id:
        return jsonify({'error': 'JWT and Channel ID are required'}), 400
    try:
        from .integrations import StreamElementsAPI, StreamElementsStore
        after_ms = data.get('after')
        before_ms = data.get('before')
        names = StreamElementsAPI(jwt, channel_id).fetch_tippers(
            after_ms=after_ms, before_ms=before_ms)
        store = StreamElementsStore(get_se_cache_path())
        store.merge_names(names)
        stored = store.get_names()
        return jsonify({'names': stored})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/integrations/se/names')
def se_names():
    """Return stored StreamElements tipper names."""
    try:
        from .integrations import StreamElementsStore
        store = StreamElementsStore(get_se_cache_path())
        names = store.get_names()
        return jsonify({'names': names})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/integrations/se/clear', methods=['POST'])
def se_clear():
    """Clear stored SE tipper names (all or older than N days)."""
    try:
        from .integrations import StreamElementsStore
        store = StreamElementsStore(get_se_cache_path())
        data = request.get_json(silent=True) or {}
        days = data.get('days')
        if days is not None:
            days = int(days)
            removed = store.clear_older_than(days)
            return jsonify({'success': True, 'removed': removed})
        store.clear_names()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/integrations/se/schedule', methods=['GET'])
def se_get_schedule():
    """Return the current SE auto-clear schedule and metadata."""
    try:
        from .integrations import StreamElementsStore
        store = StreamElementsStore(get_se_cache_path())
        return jsonify(store.get_schedule())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/integrations/se/schedule', methods=['POST'])
def se_set_schedule():
    """Set the SE auto-clear schedule."""
    data = request.get_json()
    schedule = data.get('schedule', 'never')
    if isinstance(schedule, str) and schedule.isdigit():
        schedule = int(schedule)
    try:
        from .integrations import StreamElementsStore
        store = StreamElementsStore(get_se_cache_path())
        store.set_schedule(schedule)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/webhooks/kofi', methods=['POST'])
def kofi_webhook():
    """Receive Ko-fi webhook events and store supporter names."""
    raw = request.form.get('data') or request.get_data(as_text=True)
    if not raw:
        return jsonify({'error': 'No data'}), 400
    try:
        payload = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return jsonify({'error': 'Invalid JSON'}), 400
    try:
        from .integrations import KoFiStore
        store = KoFiStore(get_kofi_cache_path())
        store.add_webhook_event(payload)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/integrations/kofi/names')
def kofi_names():
    """Return stored Ko-fi supporter names."""
    try:
        from .integrations import KoFiStore
        store = KoFiStore(get_kofi_cache_path())
        names = store.get_names()
        return jsonify({'names': names})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/integrations/kofi/clear', methods=['POST'])
def kofi_clear():
    """Clear stored Ko-fi supporter names (all or older than N days)."""
    try:
        from .integrations import KoFiStore
        store = KoFiStore(get_kofi_cache_path())
        data = request.get_json(silent=True) or {}
        days = data.get('days')
        if days is not None:
            days = int(days)
            removed = store.clear_older_than(days)
            return jsonify({'success': True, 'removed': removed})
        store.clear_names()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/integrations/kofi/schedule', methods=['GET'])
def kofi_get_schedule():
    """Return the current Ko-fi auto-clear schedule and metadata."""
    try:
        from .integrations import KoFiStore
        store = KoFiStore(get_kofi_cache_path())
        return jsonify(store.get_schedule())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/integrations/kofi/schedule', methods=['POST'])
def kofi_set_schedule():
    """Set the Ko-fi auto-clear schedule."""
    data = request.get_json()
    schedule = data.get('schedule', 'never')
    if isinstance(schedule, str) and schedule.isdigit():
        schedule = int(schedule)
    try:
        from .integrations import KoFiStore
        store = KoFiStore(get_kofi_cache_path())
        store.set_schedule(schedule)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/integrations/youtube/fetch', methods=['POST'])
def youtube_fetch():
    """Fetch member names from YouTube using stored OAuth tokens."""
    try:
        from .integrations import YouTubeOAuth, YouTubeAPI
        oauth = YouTubeOAuth(get_youtube_token_path())
        if not oauth.is_authorized():
            return jsonify({'error': 'YouTube not authorized. Click Authorize first.'}), 400
        settings = _load_generate_settings()
        client_id = settings.get('settingsYtClientId', '')
        client_secret = settings.get('settingsYtClientSecret', '')
        if not client_id or not client_secret:
            return jsonify({'error': 'YouTube Client ID and Secret required. Set them in Settings → Integrations.'}), 400
        access_token = oauth.get_access_token(client_id, client_secret)
        names = YouTubeAPI(access_token).fetch_members()
        return jsonify({'names': names})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/oauth/youtube/start')
def youtube_oauth_start():
    """Return the Google OAuth consent URL."""
    settings = _load_generate_settings()
    client_id = settings.get('settingsYtClientId', '')
    if not client_id:
        return jsonify({'error': 'Set your YouTube Client ID in Settings → Integrations first.'}), 400
    from .integrations import YouTubeOAuth
    oauth = YouTubeOAuth(get_youtube_token_path())
    redirect_uri = request.host_url.rstrip('/') + '/oauth/youtube/callback'
    url = oauth.get_auth_url(client_id, redirect_uri)
    return jsonify({'url': url})


@app.route('/oauth/youtube/callback')
def youtube_oauth_callback():
    """Handle the Google OAuth redirect and exchange the code for tokens."""
    code = request.args.get('code')
    error = request.args.get('error')
    if error:
        return f'''<html><body><h3>Authorization failed</h3><p>{error}</p>
            <script>window.opener&&window.opener.postMessage({{ytAuth:"error",message:"{error}"}},"*");setTimeout(function(){{window.close()}},2000)</script></body></html>'''
    if not code:
        return '<html><body><p>No authorization code received.</p></body></html>', 400
    try:
        from .integrations import YouTubeOAuth
        oauth = YouTubeOAuth(get_youtube_token_path())
        settings = _load_generate_settings()
        client_id = settings.get('settingsYtClientId', '')
        client_secret = settings.get('settingsYtClientSecret', '')
        redirect_uri = request.host_url.rstrip('/') + '/oauth/youtube/callback'
        oauth.exchange_code(code, client_id, client_secret, redirect_uri)
        return '''<html><body><h3>YouTube authorized!</h3><p>You can close this window.</p>
            <script>window.opener&&window.opener.postMessage({ytAuth:"success"},"*");setTimeout(function(){window.close()},1500)</script></body></html>'''
    except Exception as e:
        msg = str(e).replace('"', '&quot;')
        return f'''<html><body><h3>Authorization failed</h3><p>{msg}</p>
            <script>window.opener&&window.opener.postMessage({{ytAuth:"error",message:"{msg}"}},"*");setTimeout(function(){{window.close()}},3000)</script></body></html>'''


@app.route('/api/integrations/youtube/status')
def youtube_status():
    """Return whether YouTube is authorized."""
    from .integrations import YouTubeOAuth
    oauth = YouTubeOAuth(get_youtube_token_path())
    return jsonify({'authorized': oauth.is_authorized()})


@app.route('/api/integrations/youtube/revoke', methods=['POST'])
def youtube_revoke():
    """Revoke stored YouTube OAuth tokens."""
    from .integrations import YouTubeOAuth
    oauth = YouTubeOAuth(get_youtube_token_path())
    oauth.revoke()
    return jsonify({'success': True})


@app.route('/api/presets', methods=['GET'])
def list_presets_route():
    """List all saved presets."""
    from .presets import list_presets
    return jsonify({'presets': list_presets(get_presets_dir())})


@app.route('/api/presets', methods=['POST'])
def save_preset_route():
    """Save a new preset."""
    data = request.get_json()
    name = (data.get('name') or '').strip()
    config = data.get('config', {})
    if not name:
        return jsonify({'error': 'Preset name is required'}), 400
    try:
        from .presets import save_preset
        saved_name = save_preset(get_presets_dir(), name, config)
        return jsonify({'success': True, 'name': saved_name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/presets/<name>', methods=['GET'])
def load_preset_route(name):
    """Load a preset by name."""
    try:
        from .presets import load_preset
        config = load_preset(get_presets_dir(), name)
        return jsonify(config)
    except FileNotFoundError:
        return jsonify({'error': 'Preset not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/presets/<name>', methods=['DELETE'])
def delete_preset_route(name):
    """Delete a preset by name."""
    from .presets import delete_preset
    if delete_preset(get_presets_dir(), name):
        return jsonify({'success': True})
    return jsonify({'error': 'Preset not found'}), 404


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
            'version': '2.0.0',
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
            '/api/generate-settings': {
                'get': {
                    'summary': 'Get saved Generate-tab settings',
                    'responses': {'200': {'description': 'Saved form values as JSON.'}},
                },
                'post': {
                    'summary': 'Save Generate-tab settings',
                    'requestBody': {'required': True, 'content': {'application/json': {'schema': {'type': 'object'}}}},
                    'responses': {'200': {'description': 'Settings saved.'}},
                },
            },
            '/upload/image': {
                'post': {
                    'summary': 'Upload an image file (logo, background)',
                    'requestBody': {'required': True, 'content': {'multipart/form-data': {'schema': {'type': 'object', 'properties': {'file': {'type': 'string', 'format': 'binary'}}}}}},
                    'responses': {'200': {'description': 'Upload successful, returns filename.'}},
                },
            },
            '/upload/audio': {
                'post': {
                    'summary': 'Upload an audio file (background music)',
                    'requestBody': {'required': True, 'content': {'multipart/form-data': {'schema': {'type': 'object', 'properties': {'file': {'type': 'string', 'format': 'binary'}}}}}},
                    'responses': {'200': {'description': 'Upload successful, returns filename.'}},
                },
            },
            '/api/qr': {
                'get': {
                    'summary': 'Generate a QR code PNG',
                    'parameters': [
                        {'name': 'url', 'in': 'query', 'required': True, 'schema': {'type': 'string'}},
                        {'name': 'size', 'in': 'query', 'schema': {'type': 'integer', 'default': 200}},
                    ],
                    'responses': {'200': {'description': 'QR code PNG image.', 'content': {'image/png': {'schema': {'type': 'string', 'format': 'binary'}}}}},
                },
            },
            '/api/integrations/bmc/fetch': {
                'post': {
                    'summary': 'Fetch Buy Me a Coffee supporters',
                    'requestBody': {'required': True, 'content': {'application/json': {'schema': {'type': 'object', 'properties': {'token': {'type': 'string'}}}}}},
                    'responses': {'200': {'description': 'List of supporter names.'}},
                },
            },
            '/api/integrations/streamelements/fetch': {
                'post': {
                    'summary': 'Fetch StreamElements tippers',
                    'requestBody': {'required': True, 'content': {'application/json': {'schema': {'type': 'object', 'properties': {'jwt': {'type': 'string'}, 'channel_id': {'type': 'string'}}}}}},
                    'responses': {'200': {'description': 'List of tipper names.'}},
                },
            },
            '/webhooks/kofi': {
                'post': {
                    'summary': 'Ko-fi webhook receiver',
                    'description': 'Receives Ko-fi webhook events and stores supporter names.',
                    'responses': {'200': {'description': 'Event processed.'}},
                },
            },
            '/api/integrations/kofi/names': {
                'get': {
                    'summary': 'Get stored Ko-fi supporter names',
                    'responses': {'200': {'description': 'List of names from Ko-fi webhooks.'}},
                },
            },
            '/api/presets': {
                'get': {
                    'summary': 'List all saved presets',
                    'responses': {'200': {'description': 'Array of preset metadata.'}},
                },
                'post': {
                    'summary': 'Save a new preset',
                    'requestBody': {'required': True, 'content': {'application/json': {'schema': {'type': 'object', 'properties': {'name': {'type': 'string'}, 'config': {'type': 'object'}}}}}},
                    'responses': {'200': {'description': 'Preset saved.'}},
                },
            },
            '/api/presets/{name}': {
                'get': {
                    'summary': 'Load a preset by name',
                    'parameters': [{'name': 'name', 'in': 'path', 'required': True, 'schema': {'type': 'string'}}],
                    'responses': {'200': {'description': 'Preset configuration.'}, '404': {'description': 'Not found.'}},
                },
                'delete': {
                    'summary': 'Delete a preset',
                    'parameters': [{'name': 'name', 'in': 'path', 'required': True, 'schema': {'type': 'string'}}],
                    'responses': {'200': {'description': 'Preset deleted.'}, '404': {'description': 'Not found.'}},
                },
            },
        },
    }
    return jsonify(spec)


@app.route('/api/logs')
def view_logs():
    """Return the last 500 lines of the application log."""
    from .logging_config import get_log_dir
    log_file = os.path.join(get_log_dir(), 'app.log')
    if not os.path.isfile(log_file):
        return 'No log file found.\n', 200, {'Content-Type': 'text/plain'}
    try:
        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        tail = lines[-500:] if len(lines) > 500 else lines
        return ''.join(tail), 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except OSError as e:
        return f'Error reading log: {e}\n', 500, {'Content-Type': 'text/plain'}


@app.route('/api/docs')
def api_docs():
    """Swagger UI page"""
    return render_template('swagger.html')


if __name__ == '__main__':
    from .logging_config import setup_logging, load_log_settings
    setup_logging(**load_log_settings())

    if _is_first_run():
        logger.info("First run detected — open http://localhost:5000 to complete setup.")
    else:
        use_dummy_data = os.getenv('USE_DUMMY_DATA', 'false').lower() == 'true'
        if not use_dummy_data and (not os.getenv('PATREON_TOKEN') or not os.getenv('PATREON_CAMPAIGN_ID')):
            logger.warning("No Patreon credentials found. Running in DUMMY DATA mode for testing.")
            os.environ['USE_DUMMY_DATA'] = 'true'
            patreon_api = PatreonAPI()

    if not check_ffmpeg_util():
        logger.warning("FFmpeg not found. You can install it from the Settings page.")

    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host=host, port=port)
