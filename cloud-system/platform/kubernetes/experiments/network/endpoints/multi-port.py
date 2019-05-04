#!/usr/bin/python

import threading
import time
import socket
import SocketServer

class ThreadedTCPRequestHandler1(SocketServer.BaseRequestHandler):

  def handle(self):
    print "receives request from %s" % self.client_address[0]
    self.request.send("Hello world from host %s port 6789\n" % socket.gethostname())


class ThreadedTCPRequestHandler2(SocketServer.BaseRequestHandler):

  def handle(self):
    print "receives request from %s" % self.client_address[0]
    self.request.send("Hello world from host %s port 9876\n" % socket.gethostname())


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
  pass


if __name__ == "__main__":
  server_A = ThreadedTCPServer(('', 6789), ThreadedTCPRequestHandler1)
  server_B = ThreadedTCPServer(('', 9876), ThreadedTCPRequestHandler2)

  server_A_thread = threading.Thread(target=server_A.serve_forever)
  server_B_thread = threading.Thread(target=server_B.serve_forever)

  server_A_thread.setDaemon(True)
  server_B_thread.setDaemon(True)

  server_A_thread.start()
  server_B_thread.start()

  print "listening on 6789 & 9876"

  while 1:
    time.sleep(1)
