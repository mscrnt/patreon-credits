# Patreon Credits Generator

A web-based tool to automatically generate scrolling end-credits videos for YouTube content creators, featuring their Patreon supporters.

## Features

- 🎬 Generate professional scrolling credits videos (MP4 format)
- 🔄 Fetch current active patrons from Patreon API
- ⏱️ Customizable video duration (5-60 seconds)
- 📝 Custom header message with alignment options (left, center, right, justified)
- 🎨 35 bundled font families (including CJK support for Chinese/Japanese/Korean)
- 🖌️ Customizable text colors, sizes, and bold for both header and patron names
- 🎨 Customizable background color
- 📐 1-5 column layout with configurable alignment (left, center, right)
- 📏 Name truncation with configurable max length, or word wrap with hyphenation
- ➖ Optional separator lines between name rows
- 🖥️ 720p, 1080p, and 4K resolution support
- 💾 Patron list caching + localStorage for UI settings
- 🧪 Dummy data mode for testing
- 🔌 Adobe Premiere Pro plugin for direct timeline integration

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
   - Enter a custom header message with alignment options
   - Choose fonts, colors, sizes, and bold for both header and patron names
   - Set background color
   - Configure columns (1-5), name alignment, and max name length
   - Enable word wrap and/or separator lines between names
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

35 font families are included in the `fonts/` directory, so no system font dependencies are needed:

**CJK + Latin:** Noto Sans CJK, Noto Serif CJK, LXGW WenKai, Zen Maru Gothic, M PLUS Rounded 1c, Shippori Mincho

**Sans-serif:** Inter, Roboto, Open Sans, Poppins, Montserrat, Raleway, Quicksand, Source Sans 3, Lato, Nunito, Rubik, DM Sans, Josefin Sans, Ubuntu, Oswald, Bebas Neue

**Serif:** Cinzel, Playfair Display, Merriweather, Crimson Text, Lora, Libre Baskerville, Arvo, Neuton

**Display:** Alfa Slab One, Bangers

**Handwriting/Script:** Permanent Marker, Pacifico, Playwrite DE Grund

Noto Sans CJK is the default and supports Latin, Chinese, Japanese, and Korean characters.

## Project Structure

```
patreon-credits/
├── app.py                  # Flask server
├── patreon.py              # Patreon API client
├── ffmpeg_renderer.py      # Pillow + FFmpeg video rendering
├── fonts/                  # Bundled font files (35 families)
├── templates/
│   └── index.html          # Web interface
├── static/
│   └── output/             # Generated videos
├── plugins/
│   └── adobe-premiere/     # Adobe Premiere Pro CEP panel plugin
├── .env                    # Configuration
├── .env.example            # Configuration template
└── requirements.txt        # Python dependencies
```

## Video Specifications

- **Resolutions:** 720p HD, 1080p Full HD, 4K UHD
- **Format:** MP4 (H.264)
- **Background:** Customizable color (default: black)
- **Header:** Static at top, customizable font/color/size/alignment
- **Names:** Scrolling bottom-to-top, gold (#FFD700) by default
- **Layout:** 1-5 columns with left/center/right alignment
- **Name options:** Truncation with max length, word wrap with hyphenation, separator lines between rows
- **CJK support:** Proper character width handling via Pillow's `font.getlength()`

## API Endpoints

- `GET /` - Main web interface
- `POST /generate` - Generate credits video
- `GET /download/<filename>` - Download generated video
- `GET /patron-count` - Get current patron count
- `POST /refresh-patrons` - Force-refresh patron list from Patreon API
- `GET /check-ffmpeg` - Check FFmpeg installation
- `GET /api/docs` - Swagger UI documentation
- `GET /api/spec` - OpenAPI 3.0 JSON specification

## Adobe Premiere Pro Plugin

An Adobe Premiere Pro panel plugin is included in `plugins/adobe-premiere/`. It lets you generate and insert credits videos directly from within Premiere Pro.

See the [plugin README](plugins/adobe-premiere/README.md) for installation and usage instructions.

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
