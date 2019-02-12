#
# Overview of docker container link.
#

# Start a container as daemon, from training/postgres. The container is named 'db'.
# Note that the container doesn't expose port 5432 using -P or -p.
sudo docker run -d --name db training/postgres

# Now create a web container that links to db container.  The link option is of
# the form --link name:alias.
sudo docker run -d -P --name web --link db:db training/webapp python app.py

# Docker use environment variable and /etc/hosts file to detect the linked container.
# E.g. Env vars in the web container.
...
DB_NAME=/web/db
DB_PORT=tcp://172.17.0.5:5432
DB_PORT_5000_TCP=tcp://172.17.0.5:5432
DB_PORT_5000_TCP_PROTO=tcp
DB_PORT_5000_TCP_PORT=5432
DB_PORT_5000_TCP_ADDR=172.17.0.5
...
# And there is a host entry.
172.17.0.5  db
