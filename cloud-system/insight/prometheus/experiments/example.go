package main

import (
	"math"
	"net/http"

	"github.com/prometheus/client_golang/prometheus"
)

var (
	indexed = prometheus.NewCounter(
		prometheus.CounterOpts{
			Namespace: "my_company",
			Subsystem: "indexer",
			Name:      "documents_indexed",
			Help:      "The number of documents indexed.",
		},
	)

	size = prometheus.NewGauge(
		prometheus.GaugeOpts{
			Namespace: "my_company",
			Subsystem: "storage",
			Name:      "documents_total_size_bytes",
			Help:      "The total size of all documents in the storage.",
		},
	)

	requests = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "server_request_count",
			Help: "Counter of server requests broken by verb",
		},
		[]string{"verb"},
	)

	// https://godoc.org/github.com/prometheus/client_golang/prometheus#Histogram
	tempsHisto = prometheus.NewHistogram(
		prometheus.HistogramOpts{
			Name: "pond_temperature_celsius_histo",
			Help: "The temperature of the frog pond.",
			// 5 buckets, each 5 centigrade wide. Note histogram is cumulative.
			Buckets: prometheus.LinearBuckets(20, 5, 5),
		},
	)

	// https://godoc.org/github.com/prometheus/client_golang/prometheus#Summary
	tempsSummary = prometheus.NewSummary(
		prometheus.SummaryOpts{
			Name: "pond_temperature_celsius_summary",
			Help: "The temperature of the frog pond.",
		},
	)
)

func main() {
	// Simulate document indexed.
	indexed.Inc()

	// Simulate document storage size.
	size.Set(5)

	// Simulate some tempsHisto observations, data points around 18 ~ 42.
	for i := 0; i < 1000; i++ {
		tempsHisto.Observe(30 + math.Floor(120*math.Sin(float64(i)*0.1))/10)
	}

	// Simulate some tempsSummary observations, data points around 18 ~ 42.
	for i := 0; i < 1000; i++ {
		tempsSummary.Observe(30 + math.Floor(120*math.Sin(float64(i)*0.1))/10)
	}

	// See metrics at 'localhost:8080/metrics'.  Send request to 'localhost:8080/request'
	// and observe 'server_request_count' metric.
	http.Handle("/metrics", prometheus.Handler())
	http.Handle("/request", http.HandlerFunc(func(writer http.ResponseWriter, req *http.Request) {
		requests.WithLabelValues(req.Method).Inc()
	}))

	http.ListenAndServe(":8888", nil)
}

func init() {
	prometheus.MustRegister(indexed)
	prometheus.MustRegister(size)
	prometheus.MustRegister(requests)
	prometheus.MustRegister(tempsHisto)
	prometheus.MustRegister(tempsSummary)
}
