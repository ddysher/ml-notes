# Dockerfile
#
# Build the image::
#   docker build -t index.caicloud.io/caicloud/hostpath .
#
# Push the image ('docker login index.caicloud.io' first):
#   docker push index.caicloud.io/caicloud/hostpath
#
# Run the image:
#   docker run -d index.caicloud.io/caicloud/hostpath

FROM python:2.7-slim

COPY . /hostpath
WORKDIR /hostpath

CMD ["python", "main.py"]
