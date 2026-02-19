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
        message_style = data.get('message_style', {'size': 36, 'color': '#ffffff', 'font': 'noto_sans', 'bold': True, 'align': 'left'})
        patron_style = data.get('patron_style', {'size': 20, 'color': '#FFD700', 'font': 'noto_sans', 'bold': False})
        columns = int(data.get('columns', 4))
        name_align = data.get('name_align', 'left')
        truncate_length = int(data.get('truncate_length', 15))

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
        video_filename = video_renderer.render_video(
            message, patrons, duration, resolution,
            message_style, patron_style, columns, name_align,
            truncate_length)
        
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

@app.route('/refresh-patrons', methods=['POST'])
def refresh_patrons():
    """Force-refresh the patron list from Patreon API and update cache"""
    try:
        patrons = patreon_api.fetch_active_patrons()
        return jsonify({'count': len(patrons), 'patrons': patrons})
    except Exception as e:
        return jsonify({'error': str(e), 'count': 0}), 500

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
            'version': '1.0.0',
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
        },
    }
    return jsonify(spec)


@app.route('/api/docs')
def api_docs():
    """Swagger UI page"""
    return render_template('swagger.html')


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