#
# Overview of docker container volume.
#

# Add a data volume to a container using -v.  -v option has the format:
# (from the host: -v /host:/container, from Docker: -v /container). The
# following command will create a data volume in container 'web'.  If we
# list its directory 'ls /', we can see the 'webapp' directory.
sudo docker run -d -P --name web -v /webapp training/webapp python app.py


# Mount a host directory as a data volume. This will mount the local directory,
# /src/webapp, into the container as the /opt/webapp directory.
sudo docker run -d -P --name web -v /src/webapp:/opt/webapp training/webapp python app.py


# It's also possible to create a named Data Volume Container to share data
# between containers, or to use from non-persistent containers. The following
# command will create a data volume container.  The container will exit after
# 'echo'. The container remains stopped, but its data volume '/dbdata' can be
# accessed.
sudo docker run -d -v /dbdata --name dbdata training/postgres echo "Data-only container"

# Now we create two containers named 'db1', 'db2', which use volumes from
# container 'dbdata'.
sudo docker run -d --volumes-from dbdata --name db1 training/postgres
sudo docker run -d --volumes-from dbdata --name db2 training/postgres

# We can also mount volume from container 'db1'.
sudo docker run -d --name db3 --volumes-from db1 training/postgres
