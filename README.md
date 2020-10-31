# quart-prometheus-logger

A Prometheus logger extension for Quart.

This extension collects key request metrics for every endpoint registered in a Quart application. Namely:
* `http_requests`, the number of http requests fulfilled by the application since it started up
* `http_requests_errors`, the number of http error responses returned by the application since it started up
* `http_request_duration_seconds`, the amount of time spent handling http requests
* `http_request_size_bytes`, the size of http requests fulfilled by the application
* `http_response_size_bytes`, the size of http responses returned by the application

### Usage

Initialize the extension with the application

```py
from quart import Quart

app = Quart(__name__)
prometheus_registry = PrometheusRegistry(app=app, metrics_endpoint='internal')
```
Or you can use the factory pattern

```py
prometheus_registry = PrometheusRegistry(metrics_endpoint='internal')
def create_app()
    app = Quart(__name__)
    prometheus_registry.init_app(app)
    return app
```

