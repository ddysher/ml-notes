# Dockerfile
#
# Build the image::
#   docker build -t index.caicloud.io/caicloud/simple-backend .
#
# Push the image ('docker login index.caicloud.io' first):
#   docker push index.caicloud.io/caicloud/simple-backend
#
# Run the image:
#   docker run -d index.caicloud.io/caicloud/simple-backend

FROM python:2.7-slim

COPY . /simple-backend
WORKDIR /simple-backend

CMD ["python", "server.py"]
