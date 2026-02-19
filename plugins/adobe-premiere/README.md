# Patreon Credits Generator — Adobe Premiere Pro Plugin

A CEP (Common Extensibility Platform) panel that integrates the Patreon Credits Generator directly into Adobe Premiere Pro. Generate scrolling credits videos from your Patreon supporter list and add them to your timeline without leaving Premiere.

## Features

- Generate credits videos directly from the Premiere Pro panel
- All styling options: fonts, colors, sizes, alignment, columns, background color
- Custom names input — paste or upload a `.txt`/`.csv` file
- 35 bundled font families including CJK support
- One-click import and add to timeline
- Automatic server connection status
- Refresh patron list from panel

## Prerequisites

- Adobe Premiere Pro CC 2019 or later
- The Patreon Credits Generator server running locally — either:
  - Desktop app (`PatreonCredits.exe` / `launcher.py`), or
  - Dev server (`python app.py`)
- FFmpeg installed on the system (or bundled in the desktop app)

## Installation

### Development (Unsigned)

1. **Enable unsigned extensions** by setting the CEP debug flag:

   **Windows** — open Command Prompt as Administrator:
   ```batch
   reg add HKCU\Software\Adobe\CSXS.9 /v PlayerDebugMode /t REG_SZ /d 1 /f
   ```

   **macOS** — open Terminal:
   ```bash
   defaults write com.adobe.CSXS.9 PlayerDebugMode 1
   ```

   > Replace `CSXS.9` with `CSXS.10`, `CSXS.11`, etc. if using a newer CEP version. You can set multiple versions to be safe.

2. **Copy or symlink the plugin folder** to the Premiere Pro extensions directory:

   **Windows:**
   ```batch
   mklink /D "C:\Users\%USERNAME%\AppData\Roaming\Adobe\CEP\extensions\com.patreon.credits.generator" "D:\Projects\patreon-credits\plugins\adobe-premiere"
   ```

   **macOS:**
   ```bash
   ln -s /path/to/patreon-credits/plugins/adobe-premiere ~/Library/Application\ Support/Adobe/CEP/extensions/com.patreon.credits.generator
   ```

3. **Restart Premiere Pro.**

4. Open the panel: **Window > Extensions > Patreon Credits**

### Production (Signed)

For distribution, package and sign the extension using Adobe's [ZXPSignCmd](https://github.com/AdobeDev/CEP-Resources/tree/master/ZXPSignCMD) tool:

```bash
ZXPSignCmd -sign plugins/adobe-premiere PatreonCredits.zxp certificate.p12 password
```

## Usage

1. Start the Patreon Credits Generator server (run the desktop app or `python app.py`)

2. Open Premiere Pro and go to **Window > Extensions > Patreon Credits**

3. The panel will show a green dot when connected to the server

4. Configure your credits:
   - Set the header message and styling
   - Choose patron name font, color, and size
   - Set video duration, resolution, columns, and alignment

5. Click **Generate Credits Video**

6. Once generated, click **Import & Add to Timeline** to:
   - Download the MP4 from the server
   - Import it into your Premiere Pro project
   - Add it at the end of your active sequence's first video track

## Debugging

With the `.debug` file included, you can open Chrome DevTools for the panel at:

```
http://localhost:8088
```

This allows you to inspect the panel's HTML/JS, view console logs, and debug network requests.

## Plugin Structure

```
adobe-premiere/
├── CSXS/
│   └── manifest.xml        # CEP extension manifest
├── css/
│   └── style.css           # Panel styles (Premiere dark theme)
├── js/
│   ├── CSInterface.js      # Adobe CEP interface library
│   └── main.js             # Panel logic (API calls, Premiere integration)
├── jsx/
│   └── premiere.jsx        # ExtendScript (import media, timeline ops)
├── index.html              # Panel UI
├── .debug                  # Dev debug config (Chrome DevTools on port 8088)
└── README.md
```

## API Connection

The panel communicates with the Patreon Credits Generator server at `http://localhost:5000`. Make sure the server is running before using the panel. The connection status is shown in the top-left corner of the panel.

If you need to change the server URL (e.g., different port), edit the `API_BASE` variable in `js/main.js`.
