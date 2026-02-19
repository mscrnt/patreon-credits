from flask import Flask, render_template, request, jsonify, send_file
import os
from patreon import PatreonAPI
from ffmpeg_renderer import VideoRenderer
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize services
patreon_api = PatreonAPI()
video_renderer = VideoRenderer()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/check-ffmpeg')
def check_ffmpeg():
    """Check if FFmpeg is installed"""
    is_installed = video_renderer.check_ffmpeg()
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
        message_style = data.get('message_style', {'size': 36, 'color': '#ffffff', 'font': 'noto_sans', 'bold': True})
        patron_style = data.get('patron_style', {'size': 20, 'color': '#FFD700', 'font': 'noto_sans', 'bold': False})
        layout = data.get('layout', '4col_left')

        # Validate duration
        if duration < 5 or duration > 60:
            return jsonify({'error': 'Duration must be between 5 and 60 seconds'}), 400

        # Get patrons
        if use_cache:
            patrons = patreon_api.get_cached_patrons()
            if not patrons:
                patrons = patreon_api.fetch_active_patrons()
        else:
            patrons = patreon_api.fetch_active_patrons()
        
        if not patrons:
            return jsonify({'error': 'No active patrons found'}), 404
        
        # Generate video
        video_filename = video_renderer.render_video(message, patrons, duration, resolution, message_style, patron_style, layout)
        
        return jsonify({
            'success': True,
            'video_url': f'/static/output/{video_filename}',
            'patron_count': len(patrons),
            'filename': video_filename
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_video(filename):
    """Download the generated video"""
    try:
        file_path = os.path.join('static/output', filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=f'patreon_credits_{filename}')
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

if __name__ == '__main__':
    # Check for required environment variables
    use_dummy_data = os.getenv('USE_DUMMY_DATA', 'false').lower() == 'true'
    
    if not use_dummy_data and (not os.getenv('PATREON_TOKEN') or not os.getenv('PATREON_CAMPAIGN_ID')):
        print("WARNING: No Patreon credentials found.")
        print("To use real data: Copy .env.example to .env and fill in your credentials")
        print("Running in DUMMY DATA mode for testing...")
        os.environ['USE_DUMMY_DATA'] = 'true'
        # Reinitialize the API with dummy data mode
        patreon_api.__init__()
    
    # Check for FFmpeg
    if not video_renderer.check_ffmpeg():
        print("WARNING: FFmpeg not found. Please install FFmpeg to generate videos.")
        print("Install with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)")
    
    app.run(debug=True, port=5000)