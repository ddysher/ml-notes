#
# Example of mongodb.
#

# Use the Dockerfile at the same level to build MongoDB image. Note, there
# are offical image available:
#   docker pull mongodb
docker build -t ddysher/mongodb .

# The MongoDB image use '/data/db', and port 27017, which is default config.
# If there is no MongoDB running, we can start the instance by simply running
# the following command.  This way, when using 'mongo' client cli, we'll
# connect to it as if the MongoDB is running locally.
docker run -p 27017:27017 -v /data/db:/data/db ddysher/mongodb

# However, if there is local MongoDB, then we need to redirect port and volume.
# The following command will export container port as 27018, and persistent
# data storage to '/data/mongodb' at localhost.  We can connect to it using:
# 'mongo --port 27018' or if we do 'docker inspect' and find out the ip address
# of the container, we can use 'mongo --host 172.17.0.xx'.  Failed to redirect
# port won't start container, and failed to redirect volume will not store data
# correctly
docker run -p 27018:27017 -v /data/mongodb:/data/db ddysher/mongodb

# Assume we redirect port and directory, then we can try to verify. The
# following commands will create db and collection, we can insert and query.
# Most importantly, we can see file changes in host machine '/data/mongodb'.
mongo --port 27018
> use dockerdb
> db.users.insert({name:'someone', age:30, address:'beijing'})
> db.users.find({age: {$gt: 18}}, {name:1, _id:0})
