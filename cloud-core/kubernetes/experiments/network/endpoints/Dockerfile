# Dockerfile
#
# Build the image::
#   docker build -t multi-port:v1 .

FROM python:2.7-slim

COPY . /apps
WORKDIR /apps

CMD ["python", "multi-port.py"]
