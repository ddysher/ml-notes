# k8s-dns Dockerfile
#
# Build the image::
#   sudo docker build -t ddysher/k8s-dns-pod1 .
#
# Push the image ('docker login' first):
#   sudo docker push ddysher/k8s-dns-pod1
#
# Run the image:
#   sudo docker run -d ddysher/k8s-dns-pod1

FROM python:2.7.9

RUN pip install requests

COPY . /k8s-dns-pod2
WORKDIR /k8s-dns-pod2

CMD ["python", "client.py"]
