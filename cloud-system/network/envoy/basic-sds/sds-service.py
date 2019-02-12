import json
import os
import sys
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

PORT_NUMBER = 5000

RESPONSE = '''{
  "hosts": [{
    "ip_address": "127.0.0.1",
    "port": 9999
  }]
}
'''

# This class will handles any incoming request.
class HTTPHandler(BaseHTTPRequestHandler):
  # Handler for the GET requests
  def do_GET(self):
    self.send_response(200)
    self.send_header('Content-Type', 'application/json')
    self.end_headers()
    self.wfile.write(RESPONSE)

try:
  # Create a web server and define the handler to manage the incoming request.
  server = HTTPServer(('', PORT_NUMBER), HTTPHandler)
  print 'Started httpserver on port' , PORT_NUMBER
  sys.stdout.flush()
  server.serve_forever()
except KeyboardInterrupt:
  print '^C received, shutting down the web server'
  server.socket.close()
