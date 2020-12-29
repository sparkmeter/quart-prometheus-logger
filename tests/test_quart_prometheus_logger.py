import pytest
import pytest_asyncio
import quart

from quart_prometheus_logger import PrometheusRegistry
from prometheus_client import REGISTRY


def test_init_app(app):
    registry = PrometheusRegistry()
    metrics_endpoint = "root"
    registry.init_app(app, metrics_endpoint)
    assert "prometheus_error_handler" in app.error_handler_spec
    assert "prometheus_before_request_callback" in app.before_request_funcs
    assert "prometheus_after_request_callback" in app.after_request_funcs


def test_init(app):
    registry = PrometheusRegistry(app=app)
    assert "prometheus_error_handler" in app.error_handler_spec
    assert "prometheus_before_request_callback" in app.before_request_funcs
    assert "prometheus_after_request_callback" in app.after_request_funcs


@pytest.mark.asyncio
async def test_customer_labeler(app, client):
    registry = PrometheusRegistry(app=app)
    custom_label = lambda _: {"custom_label": 1}
    registry.custom_route_labeler(custom_label, ["custom_label"])
    await client.get("/")
    for _, collector in registry._collectors.items():
        assert "custom_label" in collector._labelnames
