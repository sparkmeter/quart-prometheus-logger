"""An extension to add Prometheus logging to your Quart application."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Union
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, Counter, Histogram, generate_latest
from quart import Response, g, request
from quart.exceptions import HTTPException, HTTPStatusException
from .utils import now_utc

if TYPE_CHECKING:
    from quart import Quart
    from quart.local import LocalProxy


MetricType = Union[Counter, Histogram]

logger = logging.getLogger(__name__)


def _status_is_error(status_code: int) -> bool:
    """Determine if the given status code is an error."""
    return status_code >= 400


def linear_bucket(start: int, width: int, count: int) -> List[int]:
    """Get a list of buckets based on the parameters.

    This mimics a Prometheus golang function for bucket sizing.
    """
    return list(range(start, start + width * count, width))


# Custom linear buckets for response Histogram metrics
RESPONSE_BUCKETS = (
    *linear_bucket(100, 100, 5),
    *linear_bucket(1000, 1000, 5),
    *linear_bucket(10000, 10000, 5),
    *linear_bucket(1000000, 10000, 5),
)


# Custom linear buckets for request Histogram metrics
REQUEST_BUCKETS = (
    *linear_bucket(100, 100, 5),
    *linear_bucket(1000, 1000, 5),
    *linear_bucket(10000, 10000, 5),
    *linear_bucket(1000000, 10000, 5),
)


class PrometheusRegistry:
    """A prometheus logger.

    The logger collects http request/response metrics and posts them to
    a Prometheus server.
    """

    def __init__(self, app: Optional[Quart] = None, metrics_endpoint: str = "root"):
        """Initialize the extension.

        :param app: The quart application for which metrics are collected
        :param metrics_endpoint: The endpoint that will be scraped by Prometheus,
                            under this endpoint, the /metrics url will be registered, defaults to "root"
        """
        self._collectors: Dict[str, MetricType] = {}
        self._custom_labeler: Optional[Callable[["LocalProxy"], Dict[str, str]]] = None
        self._custom_label_names: List[str] = []
        self._register_collectors()
        if app:
            self.init_app(app, metrics_endpoint)

    def init_app(self, app: Quart, metrics_endpoint: str):
        """Register an application."""

        def start_request():
            if request.path == "/metrics":
                return
            g.start = now_utc()  # type: ignore  # This is a valid use of Quart's global object
            labels = self._custom_labeler(request) if self._custom_labeler else {}
            self.get("http_request_size_bytes").labels(path=request.path, **labels).observe(
                request.content_length or 0
            )

        def end_request(response):
            if request.path == "/metrics":
                return response
            if not hasattr(g, "start"):
                logger.warning("No start time found in the response object. Skipping.")
                return response
            end = now_utc() - g.start
            labels = self._custom_labeler(request) if self._custom_labeler else {}
            self.get("http_request_duration_seconds").labels(path=request.path, **labels).observe(
                end.total_seconds()
            )
            self.get("http_response_size_bytes").labels(path=request.path, **labels).observe(
                response.content_length or 0
            )
            self.get("http_requests").labels(
                method=request.method, path=request.path, status=response.status_code, **labels
            ).inc()
            if _status_is_error(response.status_code):
                self.get("http_requests_errors").labels(
                    method=request.method, path=request.path, status=response.status_code, **labels
                ).inc()
            return response

        def abort_with_error(exc: Union[HTTPException, Exception]) -> Response:
            if isinstance(exc, HTTPException):
                response = exc.get_response()
            else:
                response = Response("", 500)
            return end_request(response)

        self.app = app
        app.before_request(start_request)
        app.after_request(end_request)
        app.register_error_handler(HTTPStatusException, abort_with_error)
        app.add_url_rule("/metrics", metrics_endpoint, view_func=self.render)

    def _register_collectors(self):
        """Register all collectors."""
        self._collectors = {
            c._name: c  # pylint: disable=protected-access
            for c in (
                Counter(
                    "http_requests",
                    "Total number of requests",
                    ["method", "path", "status", *self._custom_label_names],
                ),
                Counter(
                    "http_requests_errors",
                    "Total number of error requests",
                    ["method", "path", "status", *self._custom_label_names],
                ),
                Histogram(
                    "http_request_duration_seconds",
                    "The amount of time spent handling requests",
                    ["path", *self._custom_label_names],
                ),
                Histogram(
                    "http_request_size_bytes",
                    "The size of requests",
                    ["path", *self._custom_label_names],
                    buckets=REQUEST_BUCKETS,
                ),
                Histogram(
                    "http_response_size_bytes",
                    "The size of responses",
                    ["path", *self._custom_label_names],
                    buckets=RESPONSE_BUCKETS,
                ),
            )
        }

    def custom_route_labeler(
        self, labeler: Callable[["LocalProxy"], Dict[str, str]], label_names: List[str]
    ) -> None:
        """Add a handler for providing additional labels for a route.

        This will reset all metrics. Conventionally it's called when the extension is first registered

        :param labeler: The handler function to invoke. It must return a dict of key-value labels.
        :param label_names: The possible label names emitted by the labeler.
        """
        self._custom_labeler = labeler
        self._custom_label_names = label_names
        for _, collector in self._collectors.items():
            REGISTRY.unregister(collector)
        self._register_collectors()

    def get(self, name: str) -> MetricType:
        """Get a registry with the given name."""
        try:
            return self._collectors[name]
        except KeyError:
            logger.exception('No collector with name "%s" found!', name)
            raise

    @staticmethod
    def render():
        """Render the stats."""
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

