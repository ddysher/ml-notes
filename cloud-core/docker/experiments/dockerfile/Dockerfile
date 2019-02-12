############################################################
# Dockerfile to build training examples.
############################################################

# Below is the training/postgres Dockerfile that creates the image.
FROM ubuntu:14.04
MAINTAINER Docker Education Team <education@docker.com>

ENV PG_VERSION 9.3
RUN apt-get update
RUN apt-get -y install postgresql postgresql-client postgresql-contrib

RUN echo "host    all             all             0.0.0.0/0 trust" >> /etc/postgresql/$PG_VERSION/main/pg_hba.conf
RUN echo "listen_addresses='*'" >> /etc/postgresql/$PG_VERSION/main/postgresql.conf

RUN service postgresql start && \
 su postgres sh -c "createuser -d -r -s docker" && \
 su postgres sh -c "createdb -O docker docker" && \
 su postgres sh -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE docker to docker;\""

EXPOSE 5432
CMD ["su", "postgres", "-c", "/usr/lib/postgresql/$PG_VERSION/bin/postgres -D /var/lib/postgresql/$PG_VERSION/main/ -c config_file=/etc/postgresql/$PG_VERSION/main/postgresql.conf"]


# Below is the training/webapp Dockerfile that creates the image.
FROM ubuntu:12.04
MAINTAINER Docker Education Team <education@docker.com>

RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y -q curl python-all python-pip wget
ADD ./webapp /opt/webapp/
WORKDIR /opt/webapp
RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["python", "app.py"]
