"""Desktop launcher: starts Flask in a background thread and opens a native window.

Usage:
    PatreonCredits                  # Normal desktop mode (native window)
    PatreonCredits --headless       # API/server-only mode (no window)
    PatreonCredits --headless -p 8080  # Server on a custom port
"""

import argparse
import logging
import os
import socket
import sys
import threading
import time


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def wait_for_server(port, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=1):
                return True
        except OSError:
            time.sleep(0.15)
    return False


def main():
    parser = argparse.ArgumentParser(description='Patreon Credits Generator')
    parser.add_argument('--headless', action='store_true',
                        help='Run as API server only (no GUI window)')
    parser.add_argument('-p', '--port', type=int, default=8787,
                        help='Port to listen on (default: 8787)')
    args = parser.parse_args()

    # Suppress Flask/Werkzeug "development server" warning in packaged builds
    if getattr(sys, 'frozen', False):
        logging.getLogger('werkzeug').setLevel(logging.ERROR)

    # Tell Windows this is its own app, not "python.exe".
    # Without this, the taskbar groups under Python's icon.
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                'com.mscrnt.patreoncredits')
        except Exception:
            pass

    if args.headless:
        # GUI apps (console=False) on Windows have no console attached, and
        # cmd.exe won't wait for them.  Allocate a dedicated console window
        # so the server output is visible and the window stays open.
        if sys.platform == 'win32':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.AllocConsole()
                sys.stdout = open('CONOUT$', 'w')
                sys.stderr = open('CONOUT$', 'w')
                # Set the console window title
                kernel32.SetConsoleTitleW('Patreon Credits Generator — Server')
            except Exception:
                pass

        port = args.port
        host = os.environ.get('FLASK_HOST', '127.0.0.1')
        from app import app
        print('')
        print('  Patreon Credits Generator — headless mode')
        print('  ==========================================')
        print(f'  API running on: http://{host}:{port}')
        print(f'  API docs:       http://{host}:{port}/api/docs')
        print('  Press Ctrl+C to stop.')
        print('')
        app.run(host=host, port=port, debug=False, use_reloader=False)
    else:
        port = args.port

        def run_flask():
            from app import app
            app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)

        server_thread = threading.Thread(target=run_flask, daemon=True)
        server_thread.start()

        if not wait_for_server(port):
            print('ERROR: Flask server failed to start.', file=sys.stderr)
            sys.exit(1)

        import webview
        from path_utils import get_bundle_dir

        # Windows WinForms needs .ico; Linux GTK/QT needs .png
        if sys.platform == 'win32':
            icon_path = os.path.join(get_bundle_dir(), 'icon.ico')
        else:
            icon_path = os.path.join(get_bundle_dir(), 'icon.png')

        webview.create_window(
            'Patreon Credits Generator',
            f'http://127.0.0.1:{port}',
            width=1100,
            height=850,
            min_size=(800, 600),
        )
        webview.start(icon=icon_path if os.path.exists(icon_path) else None)


if __name__ == '__main__':
    main()
