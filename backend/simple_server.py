# simple_server.py
import http.server
import socketserver
import sys

PORT = 8000
Handler = http.server.SimpleHTTPRequestHandler

print(f"🚀 STARTING SIMPLE SERVER ON PORT {PORT}", file=sys.stderr)
sys.stderr.flush()

try:
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"✅ SERVING AT PORT {PORT}", file=sys.stderr)
        sys.stderr.flush()
        httpd.serve_forever()
except Exception as e:
    print(f"❌ SERVER FAILED: {str(e)}", file=sys.stderr)
    sys.stderr.flush()
