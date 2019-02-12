<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Logstash](#logstash)
- [Beats](#beats)
  - [Filebeat](#filebeat)
- [Comparison](#comparison)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Logstash

Logstash is an open source data collection engine with real-time pipelining capabilities. Logstash
can dynamically unify data from disparate sources and normalize the data into destinations of your
choice.

# Beats

The Beats are lightweight data shippers, written in Go, that you install on your servers to capture
all sorts of operational data (think of logs, metrics, or network packet data). The Beats send the
operational data to Elasticsearch, either directly or via Logstash, so it can be visualized with
Kibana.

Officially, beats contain:
- Auditbeat
- Filebeat
- Heartbeat
- Metricbeat
- Packetbeat
- Winlogbeat

## Filebeat

Filebeat is a lightweight shipper for forwarding and centralizing log data. Filebeat can send output
data to logstash, elasticsearch, kafka, stdout, etc. On average, filebeat processes around 20000~25000
lines/s, using around 50M memory.

**Experiment**

Run filebeat with a very simple configuration:

```
mkdir -p /tmp/beats

docker run \
  -v "$(pwd)"/filebeat.yml:/usr/share/filebeat/filebeat.yml \
  -v /tmp/beats:/tmp/beats \
  docker.elastic.co/beats/filebeat:6.4.3
```

Filebeat stores state of each harvester (each file has a harvester) in a registry file, i.e. after
sending logs to two files:

```
$ echo "123" >> /tmp/beats/test1.log
$ echo "321" >> /tmp/beats/test2.log

$ docker exec -it a9 bash
bash-4.2$ ls /usr/share/filebeat/data/
meta.json  registry
bash-4.2$ cat /usr/share/filebeat/data/registry
[{"source":"/tmp/beats/test1.log","offset":4,"timestamp":"2018-11-08T15:47:16.093605526Z","ttl":-1,"type":"log","meta":null,"FileStateOS":{"inode":7624990,"device":44}},{"source":"/tmp/beats/test2.log","offset":4,"timestamp":"2018-11-08T15:47:26.094313383Z","ttl":-1,"type":"log","meta":null,"FileStateOS":{"inode":7623443,"device":44}}]
bash-4.2$ exit
```

Send log again, file `test1.log` offset record changed:

```
$ echo "000" >> /tmp/beats/test1.log

$ docker exec -it a9 bash
bash-4.2$ cat /usr/share/filebeat/data/registry
[{"source":"/tmp/beats/test1.log","offset":8,"timestamp":"2018-11-08T15:48:41.096340081Z","ttl":-1,"type":"log","meta":null,"FileStateOS":{"inode":7624990,"device":44}},{"source":"/tmp/beats/test2.log","offset":4,"timestamp":"2018-11-08T15:47:26.094313383Z","ttl":-1,"type":"log","meta":null,"FileStateOS":{"inode":7623443,"device":44}}]
```

*References*

- [filebeat example config](https://github.com/elastic/beats/blob/master/filebeat/filebeat.yml)
- [how filebeat works](https://www.elastic.co/guide/en/beats/filebeat/current/how-filebeat-works.html)

# Comparison

"Bests vs Logstash" is similar to "Fluentbit vs Fluentd".
