import http.server, os
os.chdir('/Users/cielohouse/Documents/cielo-house')
class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control','no-store')
        super().end_headers()
    def log_message(self,*a): pass
http.server.HTTPServer(('',8000),H).serve_forever()
