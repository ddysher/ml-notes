#
# Overview of dokcer container port.
#

# As we can see from webapp's Dockerfile, the container expose port 5000.
# Using -P option will map all exposed ports (here 5000), to high port
# (from the range 49000 to 49900), which docker choose it for you.
sudo docker run -d -P --name web training/webapp python app.py

# Use docker ps -l to see port mapping. Or docker port
sudo docker port web 5000
-> 0.0.0.0:49155


# It's possible to specify custom port.  The following command will create
# the container with internal port 5000 mapped to host port 8080. Note the
# format is:
# (ip:hostPort:containerPort | ip::containerPort | hostPort:containerPort)
Sudo docker run -d -p --name web 8080:5000 training/webapp python app.py
