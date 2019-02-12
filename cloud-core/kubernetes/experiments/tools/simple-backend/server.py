import os
import sys
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer


PORT_NUMBER = 8000

# This class will handles any incoming request.
class HTTPHandler(BaseHTTPRequestHandler):
  # Handler for the GET requests
  def do_GET(self):
    self.send_response(200)
    self.send_header('Content-type','text/html')
    self.end_headers()
    self.wfile.write("Hello World!\n")

for key in os.environ.keys():
  print "%s=%s" % (key, os.environ[key])
sys.stdout.flush()

try:
  # Create a web server and define the handler to manage the incoming request.
  server = HTTPServer(('', PORT_NUMBER), HTTPHandler)
  print '\nStarted httpserver on port ' , PORT_NUMBER
  sys.stdout.flush()
  server.serve_forever()
except KeyboardInterrupt:
  print '^C received, shutting down the web server'
  server.socket.close()
