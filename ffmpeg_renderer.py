import subprocess
import os
import tempfile
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# Layout constants
LINE_SPACING_MULTIPLIER = 1.4
HEADER_PADDING_BASE = 30

# Font registry: name -> (regular_file, bold_file)
# Noto Sans/Serif CJK support Latin + Chinese/Japanese/Korean.
# LXGW WenKai supports Latin + Chinese/Japanese kanji.
# All others are Latin-only.
FONT_FAMILIES = {
    # CJK + Latin (Chinese/Japanese/Korean)
    'noto_sans':        ('NotoSansCJKsc-Regular.otf',    'NotoSansCJKsc-Bold.otf'),
    'noto_serif_cjk':   ('NotoSerifCJKsc-Regular.otf',   'NotoSerifCJKsc-Bold.otf'),
    'lxgw_wenkai':      ('LXGWWenKai-Regular.ttf',       'LXGWWenKai-Medium.ttf'),
    'zen_maru_gothic':  ('ZenMaruGothic-Regular.ttf',    'ZenMaruGothic-Bold.ttf'),
    'mplus_rounded':    ('MPLUSRounded1c-Regular.ttf',   'MPLUSRounded1c-Bold.ttf'),
    'shippori_mincho':  ('ShipporiMincho-Regular.ttf',   'ShipporiMincho-Bold.ttf'),
    # Sans-serif (Latin only)
    'inter':            ('Inter-Regular.ttf',             'Inter-Bold.ttf'),
    'roboto':           ('Roboto-Regular.ttf',            'Roboto-Bold.ttf'),
    'open_sans':        ('OpenSans-Regular.ttf',          'OpenSans-Bold.ttf'),
    'poppins':          ('Poppins-Regular.ttf',           'Poppins-Bold.ttf'),
    'montserrat':       ('Montserrat-Regular.ttf',        'Montserrat-Bold.ttf'),
    'raleway':          ('Raleway-Regular.ttf',           'Raleway-Bold.ttf'),
    'quicksand':        ('Quicksand-Regular.ttf',         'Quicksand-Bold.ttf'),
    'source_sans':      ('SourceSans3-Regular.ttf',       'SourceSans3-Bold.ttf'),
    'lato':             ('Lato-Regular.ttf',              'Lato-Bold.ttf'),
    'nunito':           ('Nunito-Regular.ttf',            'Nunito-Bold.ttf'),
    'rubik':            ('Rubik-Regular.ttf',             'Rubik-Bold.ttf'),
    'dm_sans':          ('DMSans-Regular.ttf',            'DMSans-Bold.ttf'),
    'josefin_sans':     ('JosefinSans-Regular.ttf',       'JosefinSans-Bold.ttf'),
    'ubuntu':           ('Ubuntu-Regular.ttf',            'Ubuntu-Bold.ttf'),
    'oswald':           ('Oswald-Regular.ttf',            'Oswald-Bold.ttf'),
    'bebas_neue':       ('BebasNeue-Regular.ttf',         'BebasNeue-Regular.ttf'),
    # Serif (Latin only)
    'cinzel':           ('Cinzel-Regular.ttf',            'Cinzel-Bold.ttf'),
    'playfair_display': ('PlayfairDisplay-Regular.ttf',   'PlayfairDisplay-Bold.ttf'),
    'merriweather':     ('Merriweather-Regular.ttf',      'Merriweather-Bold.ttf'),
    'crimson_text':     ('CrimsonText-Regular.ttf',       'CrimsonText-Bold.ttf'),
    'lora':             ('Lora-Regular.ttf',              'Lora-Bold.ttf'),
    'libre_baskerville':('LibreBaskerville-Regular.ttf',  'LibreBaskerville-Bold.ttf'),
    'arvo':             ('Arvo-Regular.ttf',              'Arvo-Bold.ttf'),
    'neuton':           ('Neuton-Regular.ttf',            'Neuton-Bold.ttf'),
    # Display (Latin only)
    'alfa_slab_one':    ('AlfaSlabOne-Regular.ttf',       'AlfaSlabOne-Regular.ttf'),
    'bangers':          ('Bangers-Regular.ttf',           'Bangers-Regular.ttf'),
    # Handwriting/Script (Latin only)
    'permanent_marker': ('PermanentMarker-Regular.ttf',   'PermanentMarker-Regular.ttf'),
    'pacifico':         ('Pacifico-Regular.ttf',          'Pacifico-Regular.ttf'),
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

    def _render_header_image(self, message, width, message_style, scale_factor, bg_color='#000000'):
        """Render the header message as a PIL Image on solid background."""
        font_size = int(message_style['size'] * scale_factor)
        color = self._hex_to_rgb(message_style['color'])
        bg_rgb = self._hex_to_rgb(bg_color)
        align = message_style.get('align', 'left')

        family = message_style.get('font', 'noto_sans')
        bold = message_style.get('bold', False)
        font_path = self._resolve_font(family, bold=bold)
        font = self._load_font(font_path, font_size)

        lines = message.split('\n')
        line_height = int(font_size * LINE_SPACING_MULTIPLIER)
        text_height = line_height * len(lines)

        padding = int(HEADER_PADDING_BASE * scale_factor)
        margin = int(50 * scale_factor)
        header_height = text_height + padding * 2
        usable_width = width - margin * 2

        img = Image.new('RGB', (width, header_height), bg_rgb)
        draw = ImageDraw.Draw(img)

        y = padding
        for i, line in enumerate(lines):
            text_w = font.getlength(line)

            if align == 'center':
                x = margin + (usable_width - text_w) / 2
            elif align == 'right':
                x = margin + usable_width - text_w
            elif align == 'justify' and i < len(lines) - 1:
                words = line.split()
                if len(words) > 1:
                    total_words_w = sum(font.getlength(w) for w in words)
                    gap = (usable_width - total_words_w) / (len(words) - 1)
                    wx = float(margin)
                    for word in words:
                        draw.text((wx, y), word, font=font, fill=color)
                        wx += font.getlength(word) + gap
                    y += line_height
                    continue
                x = margin
            else:
                x = margin

            draw.text((x, y), line, font=font, fill=color)
            y += line_height

        return img, header_height

    @staticmethod
    def _wrap_name(name, max_len):
        """Split a name into lines of at most *max_len* characters.

        Breaks happen at spaces when possible; otherwise a hyphen is inserted.
        """
        if max_len <= 0 or len(name) <= max_len:
            return [name]

        lines = []
        remaining = name
        while len(remaining) > max_len:
            # Try to break at a space within the limit
            break_at = remaining.rfind(' ', 0, max_len)
            if break_at > 0:
                lines.append(remaining[:break_at])
                remaining = remaining[break_at + 1:]
            else:
                # Hard break with hyphen
                lines.append(remaining[:max_len - 1] + '-')
                remaining = remaining[max_len - 1:]
        if remaining:
            lines.append(remaining)
        return lines

    def _render_patrons_image(self, patrons, width, patron_style, scale_factor,
                              columns=4, name_align='left', truncate_length=15,
                              word_wrap=False, name_spacing=False, bg_color='#000000'):
        """Render patron names as a tall PIL Image.

        Args:
            columns: 1-5 columns for patron names.
            name_align: 'left', 'center', or 'right'.
            truncate_length: max chars per name (0 = unlimited). Used for
                truncation (with '...') or as the wrap column when word_wrap
                is enabled.
            word_wrap: when True, long names are hyphen-wrapped instead of
                truncated; each wrapped line is centred in its column.
        """
        font_size = int(patron_style['size'] * scale_factor)
        color = self._hex_to_rgb(patron_style['color'])

        family = patron_style.get('font', 'noto_sans')
        bold = patron_style.get('bold', False)
        font_path = self._resolve_font(family, bold=bold)
        font = self._load_font(font_path, font_size)

        num_columns = max(1, min(5, columns))
        line_height = int(font_size * LINE_SPACING_MULTIPLIER)
        col_padding = int(20 * scale_factor)

        # Build display entries — each entry is a list of lines
        wrap_col = truncate_length if truncate_length > 0 else 0
        entries = []  # list of list-of-strings
        for name in patrons:
            if word_wrap and wrap_col > 0:
                entries.append(self._wrap_name(name, wrap_col))
            elif wrap_col > 0 and len(name) > wrap_col:
                entries.append([name[:wrap_col].rstrip() + '...'])
            else:
                entries.append([name])

        # Measure widest rendered line across all entries
        all_lines = [ln for entry in entries for ln in entry]
        max_name_width = max((font.getlength(ln) for ln in all_lines), default=0)
        column_width = int(max_name_width + col_padding * 2)
        area_width = column_width * num_columns

        # Position the columns block based on alignment
        if name_align == 'right':
            area_offset = width - area_width
        elif name_align == 'center':
            area_offset = (width - area_width) // 2
        else:  # left
            area_offset = 0

        # Lay out entries into grid rows, tracking max lines per row
        entry_rows = []  # list of lists (each sub-list = one grid row of entries)
        for i in range(0, len(entries), num_columns):
            entry_rows.append(entries[i:i + num_columns])

        # Compute total height: each grid row is tall enough for its tallest entry.
        # Add extra spacing when word_wrap is active so wrapped lines don't merge,
        # or when name_spacing is active (separator lines need room).
        if name_spacing:
            row_gap = line_height * 2  # space above line + line + space below
        elif word_wrap:
            row_gap = line_height
        else:
            row_gap = 0
        row_heights = []
        for i, row_entries in enumerate(entry_rows):
            max_lines = max(len(e) for e in row_entries)
            gap = row_gap if i > 0 else 0
            row_heights.append(max_lines * line_height + gap)
        total_height = max(sum(row_heights), 1)

        bg_rgb = self._hex_to_rgb(bg_color)
        img = Image.new('RGB', (width, total_height), bg_rgb)
        draw = ImageDraw.Draw(img)

        # Separator line style (when name_spacing is on)
        line_color = tuple(c // 3 for c in color)  # dimmed version of name color
        line_thickness = max(1, int(scale_factor))

        y_offset = 0
        for row_idx, row_entries in enumerate(entry_rows):
            row_h = row_heights[row_idx]

            # Draw separator line above this row (skip the very first row)
            if name_spacing and row_idx > 0:
                sep_y = y_offset + row_gap // 2
                for col in range(len(row_entries)):
                    col_start_x = area_offset + col * column_width + col_padding
                    col_end_x = area_offset + col * column_width + column_width - col_padding
                    draw.line([(col_start_x, sep_y), (col_end_x, sep_y)],
                              fill=line_color, width=line_thickness)

            # Reserve the gap at the top; centre names in remaining space
            content_top = y_offset + (row_gap if row_idx > 0 else 0)
            content_h = row_h - (row_gap if row_idx > 0 else 0)

            for col, entry_lines in enumerate(row_entries):
                block_h = len(entry_lines) * line_height
                y_start = content_top + (content_h - block_h) // 2

                col_start_x = area_offset + col * column_width
                for li, line_text in enumerate(entry_lines):
                    text_w = font.getlength(line_text)
                    x = col_start_x + (column_width - text_w) / 2
                    y = y_start + li * line_height
                    draw.text((x, y), line_text, font=font, fill=color)

            y_offset += row_h

        return img, total_height

    # ------------------------------------------------------------------
    # Video rendering
    # ------------------------------------------------------------------

    def render_video(self, message, patrons, duration=15, resolution='1280x720',
                     message_style=None, patron_style=None,
                     columns=4, name_align='left', truncate_length=15,
                     word_wrap=False, name_spacing=False, bg_color='#000000'):
        """Render the credits video using Pillow + FFmpeg."""
        if message_style is None:
            message_style = {'size': 36, 'color': '#ffffff', 'font': 'noto_sans', 'bold': True, 'align': 'left'}
        if patron_style is None:
            patron_style = {'size': 20, 'color': '#FFD700', 'font': 'noto_sans', 'bold': False}

        width, height = map(int, resolution.split('x'))
        scale_factor = height / 720

        # Render images with Pillow
        header_img, header_height = self._render_header_image(
            message, width, message_style, scale_factor, bg_color)
        patrons_img, patrons_height = self._render_patrons_image(
            patrons, width, patron_style, scale_factor, columns, name_align,
            truncate_length, word_wrap, name_spacing, bg_color)

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
            # Names start below the frame and scroll up until the last row
            # clears behind the header overlay.
            total_scroll = patrons_height + height + header_height
            scroll_speed = total_scroll / duration

            # Patron image starts below the frame, scrolls upward
            patron_y_expr = f"H+{header_height}-(t*{scroll_speed})"

            # FFmpeg color format: 0xRRGGBB
            bg_hex = bg_color.lstrip('#')
            ffmpeg_color = f'0x{bg_hex}'

            cmd = [
                'ffmpeg',
                '-f', 'lavfi', '-i', f'color={ffmpeg_color}:s={resolution}:d={duration}:r=30',
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
