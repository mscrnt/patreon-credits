# Patreon Credits Generator

A standalone desktop app to generate scrolling end-credits videos for YouTube content creators, featuring their Patreon supporters. Runs as a native window on Windows, macOS, and Linux — no Python or FFmpeg install required.

## Download

Grab the latest release for your platform from the [Releases page](../../releases):

| Platform | File | Notes |
|----------|------|-------|
| **Windows** | `PatreonCredits.exe` | Standalone executable |
| **Windows** | `PatreonCredits_Setup_*.exe` | Installer (adds Start Menu shortcut) |
| **macOS** | `PatreonCredits_*.dmg` | Drag to Applications |
| **Linux** | `PatreonCredits_*.AppImage` | `chmod +x` and run |

## Features

- 🎬 Professional scrolling credits videos (MP4)
- 🔄 Fetch active patrons from Patreon API
- 📝 Custom names input — paste or upload a `.txt`/`.csv` file (no Patreon required)
- ⏱️ Customizable duration (5-60 seconds)
- 📝 Custom header with alignment options (left, center, right, justified)
- 🎨 35 bundled font families (CJK + international character fallback)
- 🖌️ Customizable text colors, sizes, and bold
- 🎨 Customizable background color
- 📐 1-5 column layout with configurable alignment
- 📏 Name truncation or word wrap with hyphenation
- ➖ Optional separator lines between name rows
- 🖥️ 720p, 1080p, and 4K resolution
- ⚙️ In-app settings page for Patreon credentials
- 🧪 Dummy data mode for testing
- 🔌 Adobe Premiere Pro plugin for direct timeline integration

## Quick Start (Desktop App)

1. Download and run the app for your platform (see above)
2. On first launch, a setup wizard helps you configure Patreon credentials (or skip to use dummy data / manual names)
3. Configure your video options and click **Generate Credits Video**
4. Preview and download the result

Settings and output videos are saved next to the executable.

## Development Setup

For contributors or running from source:

### Prerequisites

- Python 3.10+
- FFmpeg installed and in PATH

### Install

```bash
git clone https://github.com/mscrnt/patreon-credits.git
cd patreon-credits
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your Patreon credentials (or set `USE_DUMMY_DATA=true`):
```
PATREON_TOKEN=your_creator_access_token
PATREON_CAMPAIGN_ID=your_campaign_id
USE_DUMMY_DATA=false
```

### Run

```bash
# Desktop mode (native window via pywebview)
python launcher.py

# Web mode (browser at http://localhost:5000)
python app.py
```

## Getting Patreon Credentials

You need two values (configurable in the app's **Settings** page or `.env` file):

### 1. Creator Access Token (`PATREON_TOKEN`)

1. Go to [Patreon Platform](https://www.patreon.com/portal/registration/register-clients)
2. Create a new client/app (or use an existing one)
3. Copy your **Creator Access Token**

### 2. Campaign ID (`PATREON_CAMPAIGN_ID`)

Run this with your token from step 1:

```bash
curl -s -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  "https://www.patreon.com/api/oauth2/v2/campaigns"
```

The campaign ID is in the `data[0].id` field.

## Bundled Fonts

35 font families are included in the `fonts/` directory, so no system font dependencies are needed:

**CJK + Latin:** Noto Sans CJK, Noto Serif CJK, LXGW WenKai, Zen Maru Gothic, M PLUS Rounded 1c, Shippori Mincho

**Sans-serif:** Inter, Roboto, Open Sans, Poppins, Montserrat, Raleway, Quicksand, Source Sans 3, Lato, Nunito, Rubik, DM Sans, Josefin Sans, Ubuntu, Oswald, Bebas Neue

**Serif:** Cinzel, Playfair Display, Merriweather, Crimson Text, Lora, Libre Baskerville, Arvo, Neuton

**Display:** Alfa Slab One, Bangers

**Handwriting/Script:** Permanent Marker, Pacifico, Playwrite DE Grund

Noto Sans CJK is the default and supports Latin, Chinese, Japanese, and Korean characters.

## Building from Source

### Platform build scripts

```bash
# Windows (run from cmd)
scripts\build_windows.bat

# macOS
./scripts/build_macos.sh

# Linux
./scripts/build_linux.sh
```

Each script runs PyInstaller and creates the platform-specific package (Inno Setup installer, DMG, or AppImage). Builds must run on the target platform — PyInstaller cannot cross-compile.

### CI/CD

Pushing a `v*` tag triggers GitHub Actions to build all three platforms and create a GitHub Release with artifacts attached. See [.github/workflows/build.yml](.github/workflows/build.yml).

## Project Structure

```
patreon-credits/
├── app.py                  # Flask server + routes
├── launcher.py             # Desktop app entry point (pywebview)
├── path_utils.py           # Path resolution (dev vs frozen)
├── patreon.py              # Patreon API client
├── ffmpeg_renderer.py      # Pillow + FFmpeg video rendering
├── patreon_credits.spec    # PyInstaller build spec
├── fonts/                  # Bundled font files (35 families)
├── templates/
│   ├── index.html          # Main UI
│   ├── settings.html       # Settings page
│   ├── setup.html          # First-run setup wizard
│   └── swagger.html        # API docs
├── static/                 # Flask static files
├── installer/
│   └── patreon_credits.iss # Inno Setup script (Windows)
├── scripts/
│   ├── build_windows.bat   # Windows build script
│   ├── build_macos.sh      # macOS build script
│   └── build_linux.sh      # Linux build script
├── plugins/
│   └── adobe-premiere/     # Premiere Pro CEP panel plugin
├── .github/workflows/
│   └── build.yml           # CI/CD (cross-platform builds)
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

- `GET /` — Main web interface
- `POST /generate` — Generate credits video (accepts `custom_names` for manual input)
- `GET /download/<filename>` — Download generated video
- `GET /patron-count` — Get current patron count
- `POST /refresh-patrons` — Force-refresh patron list from Patreon API
- `GET /check-ffmpeg` — Check FFmpeg installation
- `GET /settings` — Settings page (Patreon credentials, dummy data toggle)
- `POST /settings` — Save settings to `.env`
- `GET /api/docs` — Swagger UI documentation
- `GET /api/spec` — OpenAPI 3.0 JSON specification

## Adobe Premiere Pro Plugin

An Adobe Premiere Pro panel plugin is included in `plugins/adobe-premiere/`. It lets you generate and insert credits videos directly from within Premiere Pro.

See the [plugin README](plugins/adobe-premiere/README.md) for installation and usage instructions.

## Troubleshooting

### FFmpeg not found (desktop app)
The desktop app bundles its own FFmpeg — this should not happen. If it does, check the status indicator in the bottom-right of the UI.

### FFmpeg not found (dev mode)
Ensure FFmpeg is installed and in your system PATH (`ffmpeg -version`).

### No patrons showing
- Check credentials in **Settings** or `.env`
- Try the **Refresh Patron List** button
- Or paste names directly in the **Custom Names** textarea

### Video generation fails
- Check FFmpeg status indicator
- Ensure sufficient disk space
- Check the console/terminal for error messages

## Tech Stack

- **Flask** — web server
- **pywebview** — native desktop window (WebView2 on Windows, WebKit on macOS/Linux)
- **PyInstaller** — standalone packaging
- **Pillow** — text rendering with font fallback (fontTools cmap)
- **FFmpeg** — video compositing (H.264 MP4)
- **Patreon API v2** — patron data
- Vanilla JavaScript frontend with localStorage persistence

## Support

If you find this tool useful, consider supporting development:

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/mscrnt)

## License

MIT License - feel free to use this tool for your content creation needs!
