"""
Simple static file server for frontend (Railway deployment)
"""
import os
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)

    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    print(f"Frontend server starting on port {port}")
    server = HTTPServer(('0.0.0.0', port), Handler)
    server.serve_forever()
