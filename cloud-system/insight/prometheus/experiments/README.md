# Prometheus go client and usage example

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
# stop existing prometheus
/tmp/prometheus -config.file=./prometheus.yaml -alertmanager.url http://localhost:9093
```

Observe that alert goes from PENDING to Firing.

## Cleanup

```
# stop prometheus and alertmanager
killall random
rm -rf data random
```
