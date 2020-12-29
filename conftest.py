import pytest
from quart import Quart


@pytest.fixture
def app():
    app = Quart("testapp")
    @app.route
    async def index():
        return 'hi'
    return app

@pytest.fixture
def client(app):
    return app.test_client()