# Patreon Credits Generator

A web-based tool to automatically generate scrolling end-credits videos for YouTube content creators, featuring their Patreon supporters.

## Features

- 🎬 Generate professional scrolling credits videos (MP4 format)
- 🔄 Fetch current active patrons from Patreon API
- ⏱️ Customizable video duration (5-60 seconds)
- 📝 Custom message header
- 🎨 19 bundled font families (including CJK support)
- 🖌️ Customizable text colors, sizes, and bold options
- 📐 Two layout modes: 4-column left (YouTube cards) or 3-column centered
- 🖥️ 720p, 1080p, and 4K resolution support
- 💾 Patron list caching + localStorage for UI settings
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

3. Configure your video:
   - Enter a custom header message
   - Choose fonts, colors, and bold for both the header and patron names
   - Select a layout (4-column left or 3-column centered)
   - Pick a resolution (720p, 1080p, or 4K)
   - Set the video duration (5-60 seconds)

4. Click "Generate Credits Video"

5. Preview and download the generated video

All settings are saved in your browser and restored on the next visit.

## Testing with Dummy Data

If you don't have Patreon credentials yet, the app will automatically run in dummy data mode with 50 sample patron names.

To explicitly enable dummy data mode, set in your `.env`:
```
USE_DUMMY_DATA=true
```

## Bundled Fonts

19 font families are included in the `fonts/` directory, so no system font dependencies are needed:

**Sans-serif:** Noto Sans (CJK), Inter, Roboto, Open Sans, Montserrat, Lato, Nunito, Rubik, DM Sans, Josefin Sans, Ubuntu, Oswald, Bebas Neue

**Serif:** Playfair Display, Lora, Libre Baskerville, Arvo, Neuton

**Handwriting:** Playwrite DE Grund

Noto Sans CJK is the default and supports Latin, Chinese, Japanese, and Korean characters.

## Project Structure

```
patreon-credits/
├── app.py                  # Flask server
├── patreon.py              # Patreon API client
├── ffmpeg_renderer.py      # Pillow + FFmpeg video rendering
├── fonts/                  # Bundled font files (19 families)
├── templates/
│   └── index.html          # Web interface
├── static/
│   └── output/             # Generated videos
├── .env                    # Configuration
├── .env.example            # Configuration template
└── requirements.txt        # Python dependencies
```

## Video Specifications

- **Resolutions:** 720p HD, 1080p Full HD, 4K UHD
- **Format:** MP4 (H.264)
- **Background:** Black
- **Header:** Static at top, customizable font/color/size
- **Names:** Scrolling bottom-to-top, gold (#FFD700) by default
- **Layouts:**
  - 4 columns left-aligned — right side reserved for YouTube end cards
  - 3 columns centered — names span the full frame
- **CJK support:** Proper character width handling via Pillow's `font.getlength()`

## API Endpoints

- `GET /` - Main web interface
- `POST /generate` - Generate credits video
- `GET /download/<filename>` - Download generated video
- `GET /patron-count` - Get current patron count
- `GET /check-ffmpeg` - Check FFmpeg installation

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
- **Flask** for the web server
- **Pillow (PIL)** for text rendering to images (pixel-accurate CJK support)
- **FFmpeg** for video compositing and encoding
- **Patreon API v2** for patron data
- **Google Fonts CDN** for browser font previews
- **localStorage** for persisting UI settings
- Vanilla JavaScript for the frontend

## Support

If you find this tool useful, consider supporting development:

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/mscrnt)

## License

MIT License - feel free to use this tool for your content creation needs!
