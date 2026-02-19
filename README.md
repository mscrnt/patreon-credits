# Patreon Credits Generator

A web-based tool to automatically generate scrolling end-credits videos for YouTube content creators, featuring their Patreon supporters.

## Features

- 🎬 Generate professional scrolling credits videos (MP4 format)
- 🔄 Fetch current active patrons from Patreon API
- ⏱️ Customizable video duration (5-60 seconds)
- 📝 Custom message header
- 🎨 Clean, dark-themed web interface
- 💾 Patron list caching
- 🧪 Dummy data mode for testing

## Prerequisites

- Python 3.7+
- FFmpeg (for video generation)
- Patreon Creator Access Token (for real data)

## Installation

1. Clone the repository:
```bash
cd patreon-credits
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Install FFmpeg:
   - macOS: `brew install ffmpeg`
   - Ubuntu/Debian: `sudo apt-get install ffmpeg`
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

5. Configure environment:
```bash
cp .env.example .env
```

Edit `.env` and add your Patreon credentials:
```
PATREON_TOKEN=your_creator_access_token
PATREON_CAMPAIGN_ID=your_campaign_id
USE_DUMMY_DATA=false
```

## Getting Patreon Credentials

You need two values for the `.env` file:

### 1. Creator Access Token (`PATREON_TOKEN`)

1. Go to [Patreon Platform](https://www.patreon.com/portal/registration/register-clients)
2. Create a new client/app (or use an existing one)
3. Copy your **Creator Access Token**

### 2. Campaign ID (`PATREON_CAMPAIGN_ID`)

**Option A: Via the API (easiest)**

Run this in your terminal using the token from step 1:

```bash
curl -s -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  "https://www.patreon.com/api/oauth2/v2/campaigns"
```

The response will include your campaign ID in the `data[0].id` field.

**Option B: From the URL**

Go to your Patreon creator page and look at the URL — it sometimes contains the campaign ID.

## Usage

1. Start the Flask server:
```bash
python app.py
```

2. Open your browser to `http://localhost:5000`

3. Enter your custom message (e.g., "This video was made possible by:")

4. Set the video duration (default: 15 seconds)

5. Click "Generate Credits Video"

6. Preview and download the generated video

## Testing with Dummy Data

If you don't have Patreon credentials yet, the app will automatically run in dummy data mode with 50 sample patron names.

To explicitly enable dummy data mode, set in your `.env`:
```
USE_DUMMY_DATA=true
```

## Project Structure

```
patreon-credits/
├── app.py                  # Flask server
├── patreon.py              # Patreon API client
├── ffmpeg_renderer.py      # Video rendering logic
├── templates/
│   └── index.html          # Web interface
├── static/
│   └── output/             # Generated videos
├── patrons_cache.json      # Cached patron data
├── .env                    # Configuration
├── .env.example            # Configuration template
└── requirements.txt        # Python dependencies
```

## API Endpoints

- `GET /` - Main web interface
- `POST /generate` - Generate credits video
- `GET /download/<filename>` - Download generated video
- `GET /patron-count` - Get current patron count
- `GET /check-ffmpeg` - Check FFmpeg installation

## Video Specifications

- Resolutions: 
  - 720p HD (1280x720) - Default
  - 1080p Full HD (1920x1080)
  - 4K UHD (3840x2160)
- Format: MP4 (H.264)
- Background: Black
- Text: White, left-aligned with space for YouTube cards
- Font size: Scales with resolution
- Scroll: Bottom to top
- Layout: 3 columns on the left, right side reserved for YouTube end cards

## Troubleshooting

### FFmpeg not found
- Ensure FFmpeg is installed and in your system PATH
- Try running `ffmpeg -version` in terminal

### No patrons showing
- Check your Patreon API credentials
- Ensure you have active patrons in your campaign
- Try using the "Refresh Patron List" button

### Video generation fails
- Check FFmpeg installation
- Ensure sufficient disk space
- Check console for error messages

## Development

The app uses:
- Flask for the web server
- Patreon API v2 for patron data
- FFmpeg for video generation
- Vanilla JavaScript for the frontend

## License

MIT License - feel free to use this tool for your content creation needs!