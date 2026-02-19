"""Desktop launcher: starts Flask in a background thread and opens a native window."""

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
    port = find_free_port()

    # Start Flask in a daemon thread
    def run_flask():
        from app import app
        app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)

    server_thread = threading.Thread(target=run_flask, daemon=True)
    server_thread.start()

    if not wait_for_server(port):
        print('ERROR: Flask server failed to start.', file=sys.stderr)
        sys.exit(1)

    import webview
    webview.create_window(
        'Patreon Credits Generator',
        f'http://127.0.0.1:{port}',
        width=1100,
        height=850,
        min_size=(800, 600),
    )
    webview.start()


if __name__ == '__main__':
    main()
