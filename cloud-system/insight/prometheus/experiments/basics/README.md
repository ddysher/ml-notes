<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Prometheus Example](#prometheus-example)
  - [Prometheus go client](#prometheus-go-client)
  - [Prometheus usage](#prometheus-usage)
    - [Run three process for prometheus to scrape](#run-three-process-for-prometheus-to-scrape)
    - [Build prometheus](#build-prometheus)
    - [Run prometheus](#run-prometheus)
  - [Alertmanager Usage](#alertmanager-usage)
    - [Build alertmanager](#build-alertmanager)
    - [Run alertmanager](#run-alertmanager)
    - [Restart prometheus](#restart-prometheus)
  - [Cleanup](#cleanup)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Prometheus Example

## Prometheus go client

See example.go

## Prometheus usage

### Run three process for prometheus to scrape

```
go build random.go
./random --listen-address localhost:8080 &
./random --listen-address localhost:8081 &
./random --listen-address localhost:8082 &
```

### Build prometheus

```
cd $GOPATH/src/github.com/prometheus/prometheus
make build
mv prometheus /tmp
cd -
```

### Run prometheus

```
/tmp/prometheus -config.file=./prometheus.yaml
```

Go to `http://localhost:9090` to access prometheus.

## Alertmanager Usage

Note we've already specified rules in prometheus.yaml for prometheus.

### Build alertmanager

```
cd $GOPATH/src/github.com/prometheus/alertmanager
make build
mv alertmanager /tmp
cd -
```

### Run alertmanager

```
/tmp/alertmanager -config.file=./alertmanager.yaml
```

Go to `http://localhost:9093` to access alertmanager.

### Restart prometheus

```
# stop existing prometheus, then restart
/tmp/prometheus -config.file=./prometheus.yaml -alertmanager.url http://localhost:9093
```

Observe that alert goes from PENDING to Firing.

## Cleanup

```
# stop prometheus and alertmanager
killall random
rm -rf data random
```
