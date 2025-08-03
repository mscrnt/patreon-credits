import subprocess
import os
import tempfile
from datetime import datetime
import shutil

class VideoRenderer:
    def __init__(self):
        self.output_dir = 'static/output'
        os.makedirs(self.output_dir, exist_ok=True)
        
    def create_credits_text(self, message, patrons):
        """Create the credits text file for FFmpeg"""
        credits_text = f"{message}\n\n"
        
        # Arrange patrons in 3 columns
        num_columns = 3
        max_name_length = 22  # Maximum characters per name
        column_spacing = 3    # Spaces between columns (reduced from default padding)
        
        # Calculate rows needed
        rows_needed = (len(patrons) + num_columns - 1) // num_columns
        
        # Create the 3-column layout
        for row in range(rows_needed):
            row_names = []
            for col in range(num_columns):
                index = row + col * rows_needed
                if index < len(patrons):
                    name = patrons[index]
                    if len(name) > max_name_length:
                        name = name[:max_name_length - 3] + "..."
                    
                    # Add the name with minimal spacing
                    if col < num_columns - 1:  # Not the last column
                        row_names.append(name + " " * (max_name_length - len(name) + column_spacing))
                    else:  # Last column doesn't need extra spacing
                        row_names.append(name)
            
            credits_text += "".join(row_names).rstrip() + "\n"
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(credits_text)
            return f.name
    
    def create_message_file(self, message):
        """Create a separate file for the message"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(message)
            return f.name
    
    def create_patrons_file(self, patrons):
        """Create a separate file for patron names"""
        # Arrange patrons in 3 columns with centered names
        num_columns = 3
        column_width = 20  # Reduced column width for tighter spacing
        column_gap = 0     # No spaces between columns
        
        # Calculate rows needed
        rows_needed = (len(patrons) + num_columns - 1) // num_columns
        
        # Create the 3-column layout with centered names
        patrons_text = ""
        
        # Fill columns from left to right, row by row
        for row in range(rows_needed):
            columns = []
            for col in range(num_columns):
                index = row * num_columns + col
                if index < len(patrons):
                    name = patrons[index]
                    # Truncate long names
                    if len(name) > column_width:
                        name = name[:column_width - 3] + "..."
                    columns.append(name)
                else:
                    columns.append("")
            
            # Format the row with centered names
            if any(columns):
                formatted_columns = []
                for i, col in enumerate(columns):
                    if col:
                        # Center the name within the column width
                        centered_name = col.center(column_width)
                        if i > 0:
                            # Add gap before non-first columns
                            centered_name = (" " * column_gap) + centered_name
                        formatted_columns.append(centered_name)
                
                row_text = "".join(formatted_columns).rstrip()
                if row_text:
                    patrons_text += row_text + "\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(patrons_text)
            return f.name
    
    def render_video(self, message, patrons, duration=15, resolution='1280x720', message_style=None, patron_style=None):
        """Render the credits video using FFmpeg"""
        if message_style is None:
            message_style = {'size': 36, 'color': '#ffffff', 'font': 'default'}
        if patron_style is None:
            patron_style = {'size': 20, 'color': '#ffffff', 'font': 'default'}
            
        # Create separate text files
        message_file = self.create_message_file(message)
        patrons_file = self.create_patrons_file(patrons)
        
        # Generate output filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'credits_{timestamp}.mp4'
        output_path = os.path.join(self.output_dir, output_filename)
        
        try:
            # Parse resolution and scale factors
            width, height = map(int, resolution.split('x'))
            scale_factor = height / 720  # Base scale on 720p
            
            # Scale positioning based on resolution
            x_position = int(50 * scale_factor)
            
            # Apply font styles
            message_size = int(message_style['size'] * scale_factor)
            patron_size = int(patron_style['size'] * scale_factor)
            
            # Convert hex colors to FFmpeg format (remove #)
            message_color = message_style['color'].lstrip('#')
            patron_color = patron_style['color'].lstrip('#')
            
            # Font weight/style - FFmpeg doesn't support bold/italic in drawtext, so we'll ignore for now
            # In a production app, you'd need to use different font files for bold/italic
            message_font_style = ''
            patron_font_style = ''
            
            # Calculate positions and scroll speed
            message_lines = message.count('\n') + 1
            message_height = message_lines * (message_size * 1.5)
            message_y_position = int(30 * scale_factor)  # Position within header
            
            # Calculate header bar dimensions
            header_height = int(message_height + (80 * scale_factor))  # Message height + padding
            header_padding = int(20 * scale_factor)  # Padding above and below text
            
            rows_needed = (len(patrons) + 2) // 3  # 3 columns
            patrons_height = rows_needed * (patron_size * 1.25)
            
            # Start patrons below the header bar
            patrons_start_y = header_height + (20 * scale_factor)
            
            # Patrons scroll from bottom to above the screen
            total_scroll_height = patrons_height + height + patrons_start_y
            scroll_speed = total_scroll_height / duration
            
            # FFmpeg command with black header bar
            # Layer order: 1) scrolling patrons, 2) black header bar, 3) static message
            cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', f'color=black:s={resolution}:d={duration}',
                '-vf', (
                    # First draw scrolling patrons
                    f"drawtext=textfile='{patrons_file}':fontsize={patron_size}:fontcolor=0x{patron_color}:"
                    f"x={x_position}:y=h-(t*{scroll_speed})+{int(patrons_start_y)},"
                    # Draw black rectangle for header background
                    f"drawbox=x=0:y=0:w=iw:h={header_height}:color=black:t=fill,"
                    # Then draw static message on top
                    f"drawtext=textfile='{message_file}':fontsize={message_size}:fontcolor=0x{message_color}:"
                    f"x={x_position}:y={message_y_position}"
                ),
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-preset', 'fast',
                '-y',  # Overwrite output
                output_path
            ]
            
            # Run FFmpeg
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg error: {result.stderr}")
            
            return output_filename
            
        finally:
            # Clean up temp files
            for temp_file in [message_file, patrons_file]:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
    
    def check_ffmpeg(self):
        """Check if FFmpeg is installed"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def get_system_font(self):
        """Get a suitable system font path"""
        # Common font paths for different systems
        font_paths = [
            # macOS
            '/System/Library/Fonts/Helvetica.ttc',
            '/Library/Fonts/Arial.ttf',
            # Linux
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            # Windows (if running in WSL or similar)
            '/mnt/c/Windows/Fonts/arial.ttf'
        ]
        
        for font in font_paths:
            if os.path.exists(font):
                return font
        
        # Return None to use FFmpeg's default font
        return None