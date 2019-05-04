import netifaces
import os


def PrintInterfaces():
  """Print all interfaces in the Pod."""
  for interface in netifaces.interfaces():
    if netifaces.AF_INET in netifaces.ifaddresses(interface):
      print interface
      print netifaces.ifaddresses(interface)[netifaces.AF_INET]


def PrintEnv():
  """Print all environment variables in the Pod."""
  print os.environ


if __name__ == '__main__':
  PrintEnv()
