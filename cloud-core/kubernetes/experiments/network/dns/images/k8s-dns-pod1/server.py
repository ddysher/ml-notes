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

try:
  # Create a web server and define the handler to manage the incoming request.
  server = HTTPServer(('', PORT_NUMBER), HTTPHandler)
  print 'Started httpserver on port ' , PORT_NUMBER
  server.serve_forever()
except KeyboardInterrupt:
  print '^C received, shutting down the web server'
  server.socket.close()
