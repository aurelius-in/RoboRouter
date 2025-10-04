Observability
=============

Services
--------
- Prometheus: http://localhost:9090 (scrapes API /metrics)
- Grafana: http://localhost:3000 (import dashboard JSON and set Prometheus datasource)

Metrics
-------
- roborouter_requests_total{service,method,endpoint,status}
- roborouter_request_latency_seconds_bucket{service,method,endpoint,le}

Notes
-----
- Set ROBOROUTER_SERVICE per service to label metrics correctly.
- Extend tracing via OpenTelemetry exporters in production as needed.

