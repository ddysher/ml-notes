Yes this is exactly what happens. To reproduce the issue, start the nfs server container:
docker run -d --name nfs --privileged cpuguy83/nfs-server /tmp

Then update the server ip address in the examples/nfs-pd/testpd.yaml to point to that nfs server container. Also update the mountPath to point to /var/www/html. This will conflict with the Dockerfile Volume directive. Then run:

./cluster/kubectl.sh create -f examples/nfs-pd/testpd.yaml

You'll notice the nfs mount didn't get mounted in the container. If you rerun the example pod but use a subdirectory under /var/ww/html then it will get mounted.
