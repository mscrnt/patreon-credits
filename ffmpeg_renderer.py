import subprocess
import os
import tempfile
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# Layout constants
LINE_SPACING_MULTIPLIER = 1.4
HEADER_PADDING_BASE = 30

# Font registry: name -> (regular_file, bold_file)
# Noto Sans CJK supports Latin + CJK; the others are Latin-only.
FONT_FAMILIES = {
    # Sans-serif
    'noto_sans':        ('NotoSansCJKsc-Regular.otf',    'NotoSansCJKsc-Bold.otf'),
    'inter':            ('Inter-Regular.ttf',             'Inter-Bold.ttf'),
    'roboto':           ('Roboto-Regular.ttf',            'Roboto-Bold.ttf'),
    'open_sans':        ('OpenSans-Regular.ttf',          'OpenSans-Bold.ttf'),
    'montserrat':       ('Montserrat-Regular.ttf',        'Montserrat-Bold.ttf'),
    'lato':             ('Lato-Regular.ttf',              'Lato-Bold.ttf'),
    'nunito':           ('Nunito-Regular.ttf',            'Nunito-Bold.ttf'),
    'rubik':            ('Rubik-Regular.ttf',             'Rubik-Bold.ttf'),
    'dm_sans':          ('DMSans-Regular.ttf',            'DMSans-Bold.ttf'),
    'josefin_sans':     ('JosefinSans-Regular.ttf',       'JosefinSans-Bold.ttf'),
    'ubuntu':           ('Ubuntu-Regular.ttf',            'Ubuntu-Bold.ttf'),
    'oswald':           ('Oswald-Regular.ttf',            'Oswald-Bold.ttf'),
    'bebas_neue':       ('BebasNeue-Regular.ttf',         'BebasNeue-Regular.ttf'),
    # Serif
    'playfair_display': ('PlayfairDisplay-Regular.ttf',   'PlayfairDisplay-Bold.ttf'),
    'lora':             ('Lora-Regular.ttf',              'Lora-Bold.ttf'),
    'libre_baskerville':('LibreBaskerville-Regular.ttf',  'LibreBaskerville-Bold.ttf'),
    'arvo':             ('Arvo-Regular.ttf',              'Arvo-Bold.ttf'),
    'neuton':           ('Neuton-Regular.ttf',            'Neuton-Bold.ttf'),
    # Handwriting
    'playwrite':        ('PlaywriteDEGrund-Regular.ttf',  'PlaywriteDEGrund-Regular.ttf'),
}


class VideoRenderer:
    def __init__(self):
        self.output_dir = 'static/output'
        os.makedirs(self.output_dir, exist_ok=True)
        self._font_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')

    # ------------------------------------------------------------------
    # Font helpers
    # ------------------------------------------------------------------

    def _resolve_font(self, family, bold=False):
        """Resolve a font family name to an absolute file path.

        Falls back through bundled fonts → system fonts → PIL default.
        """
        if family in FONT_FAMILIES:
            idx = 1 if bold else 0
            candidate = os.path.join(self._font_dir, FONT_FAMILIES[family][idx])
            if os.path.exists(candidate):
                return candidate

        # Fallback: Noto Sans CJK bundled
        fallback = os.path.join(self._font_dir,
                                'NotoSansCJKsc-Bold.otf' if bold else 'NotoSansCJKsc-Regular.otf')
        if os.path.exists(fallback):
            return fallback

        # System fallbacks
        for p in ['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                   '/mnt/c/Windows/Fonts/msyh.ttc',
                   '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                   '/mnt/c/Windows/Fonts/arial.ttf']:
            if os.path.exists(p):
                return p
        return None

    def _load_font(self, font_path, size):
        """Load a PIL ImageFont, falling back to default if path is None."""
        if font_path:
            try:
                return ImageFont.truetype(font_path, size)
            except (IOError, OSError):
                pass
        return ImageFont.load_default()

    # Keep legacy helpers for anything external that calls them
    def get_system_font(self):
        return self._resolve_font('noto_sans', bold=False)

    def get_bold_font(self):
        return self._resolve_font('noto_sans', bold=True)

    # ------------------------------------------------------------------
    # Colour helper
    # ------------------------------------------------------------------

    @staticmethod
    def _hex_to_rgb(hex_color):
        """Convert hex colour string to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    # ------------------------------------------------------------------
    # Image rendering
    # ------------------------------------------------------------------

    def _render_header_image(self, message, width, message_style, scale_factor):
        """Render the header message as a PIL Image on solid black."""
        font_size = int(message_style['size'] * scale_factor)
        color = self._hex_to_rgb(message_style['color'])

        family = message_style.get('font', 'noto_sans')
        bold = message_style.get('bold', False)
        font_path = self._resolve_font(family, bold=bold)
        font = self._load_font(font_path, font_size)

        lines = message.split('\n')
        line_height = int(font_size * LINE_SPACING_MULTIPLIER)
        text_height = line_height * len(lines)

        padding = int(HEADER_PADDING_BASE * scale_factor)
        x_offset = int(50 * scale_factor)
        header_height = text_height + padding * 2

        img = Image.new('RGB', (width, header_height), (0, 0, 0))
        draw = ImageDraw.Draw(img)

        y = padding
        for line in lines:
            draw.text((x_offset, y), line, font=font, fill=color)
            y += line_height

        return img, header_height

    def _render_patrons_image(self, patrons, width, patron_style, scale_factor, layout='4col_left'):
        """Render patron names as a tall PIL Image.

        Layouts:
            '4col_left'  – 4 columns using the left ~57 % of the frame
            '3col_center' – 3 columns centred across the full frame
        """
        font_size = int(patron_style['size'] * scale_factor)
        color = self._hex_to_rgb(patron_style['color'])

        family = patron_style.get('font', 'noto_sans')
        bold = patron_style.get('bold', False)
        font_path = self._resolve_font(family, bold=bold)
        font = self._load_font(font_path, font_size)

        # Layout parameters
        if layout == '3col_center':
            num_columns = 3
            area_width = int(width * 0.90)
            area_offset = (width - area_width) // 2
        else:  # 4col_left
            num_columns = 4
            area_width = int(width * 0.57)
            area_offset = 0

        column_width = area_width // num_columns
        line_height = int(font_size * LINE_SPACING_MULTIPLIER)
        margin = int(5 * scale_factor)
        max_text_width = column_width - margin * 2

        rows_needed = (len(patrons) + num_columns - 1) // num_columns
        total_height = max(rows_needed * line_height, 1)

        img = Image.new('RGB', (width, total_height), (0, 0, 0))
        draw = ImageDraw.Draw(img)

        for row in range(rows_needed):
            y = row * line_height
            for col in range(num_columns):
                index = row * num_columns + col
                if index >= len(patrons):
                    continue

                name = patrons[index]

                # Pixel-accurate truncation
                if font.getlength(name) > max_text_width:
                    while len(name) > 0 and font.getlength(name + '...') > max_text_width:
                        name = name[:-1]
                    name = name.rstrip() + '...'

                # Centre-align within column
                text_width = font.getlength(name)
                col_start_x = area_offset + col * column_width
                x = col_start_x + (column_width - text_width) / 2

                draw.text((x, y), name, font=font, fill=color)

        return img, total_height

    # ------------------------------------------------------------------
    # Video rendering
    # ------------------------------------------------------------------

    def render_video(self, message, patrons, duration=15, resolution='1280x720',
                     message_style=None, patron_style=None, layout='4col_left'):
        """Render the credits video using Pillow + FFmpeg."""
        if message_style is None:
            message_style = {'size': 36, 'color': '#ffffff', 'font': 'noto_sans', 'bold': True}
        if patron_style is None:
            patron_style = {'size': 20, 'color': '#FFD700', 'font': 'noto_sans', 'bold': False}

        width, height = map(int, resolution.split('x'))
        scale_factor = height / 720

        # Render images with Pillow
        header_img, header_height = self._render_header_image(
            message, width, message_style, scale_factor)
        patrons_img, patrons_height = self._render_patrons_image(
            patrons, width, patron_style, scale_factor, layout)

        # Save to temp PNGs
        header_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        patrons_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        header_img.save(header_file.name)
        patrons_img.save(patrons_file.name)
        header_file.close()
        patrons_file.close()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'credits_{timestamp}.mp4'
        output_path = os.path.join(self.output_dir, output_filename)

        try:
            total_scroll = patrons_height + height
            scroll_speed = total_scroll / duration

            # Patron image starts below the frame, scrolls upward
            patron_y_expr = f"H+{header_height}-(t*{scroll_speed})"

            cmd = [
                'ffmpeg',
                '-f', 'lavfi', '-i', f'color=black:s={resolution}:d={duration}:r=30',
                '-loop', '1', '-t', str(duration), '-i', patrons_file.name,
                '-loop', '1', '-t', str(duration), '-i', header_file.name,
                '-filter_complex', (
                    f"[1:v]format=rgba,scale={width}:{patrons_height}[patron];"
                    f"[0:v][patron]overlay=0:'{patron_y_expr}'[bg];"
                    f"[bg][2:v]overlay=0:0[out]"
                ),
                '-map', '[out]',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-preset', 'fast',
                '-shortest',
                '-y',
                output_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                raise Exception(f"FFmpeg error: {result.stderr}")

            return output_filename

        finally:
            for f in [header_file.name, patrons_file.name]:
                if os.path.exists(f):
                    os.unlink(f)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def check_ffmpeg(self):
        """Check if FFmpeg is installed"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
